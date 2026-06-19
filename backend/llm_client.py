import config


def _get_client():
    from openai import OpenAI
    return OpenAI(
        api_key=config.OPENROUTER_API_KEY,
        base_url=config.OPENROUTER_BASE_URL,
        default_headers={
            "HTTP-Referer": "https://github.com/preet1249/QuantVeil",
            "X-Title": "QuantVeil",
        },
    )


def analyze(site_data: dict, reddit_data: dict, domain: str) -> str:
    if not config.OPENROUTER_API_KEY:
        return _format_no_llm(site_data, reddit_data, domain)

    posts = reddit_data.get("posts", [])
    ai_summary = reddit_data.get("ai_summary", "")

    reddit_block = "\n".join(
        f"  [{p['subreddit']}] {p['title']}  (score={p['score']})"
        for p in posts[:15]
    ) or "  No Reddit posts found."

    prompt = f"""You are a cold outreach research assistant. Analyze this website and Reddit data to help craft a personalized cold email.

TARGET DOMAIN: {domain}
PAGE TITLE: {site_data.get('title', 'N/A')}
META DESCRIPTION: {site_data.get('meta_description', 'N/A')}

WEBSITE CONTENT (excerpt):
{site_data.get('visible_text', '')[:2000]}

REDDIT AI SUMMARY (from Reddit's own analysis):
{ai_summary[:1500] if ai_summary else 'Not available'}

REDDIT POSTS ({len(posts)} found):
{reddit_block}

Provide a structured lead brief:

1. BUSINESS OVERVIEW
   What does this company do? (2-3 sentences, factual)

2. TARGET MARKET
   Who are their customers / end users?

3. REDDIT SENTIMENT
   Positive points (bullet list, based on Reddit)
   Negative points / complaints (bullet list, based on Reddit)
   If no Reddit data: note that.

4. PAIN POINTS
   What problems might they have right now? (2-4 bullets)

5. COLD OUTREACH OPENING LINE
   Write ONE punchy, specific first sentence for a cold email that references something real about this company. Do NOT use generic phrases like "I noticed your website" - make it specific.

Keep each section concise. No filler.
"""

    model = config.LLM_MODEL
    print(f"  [LLM] Calling {model} via OpenRouter...")
    client = _get_client()

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=900,
            temperature=0.25,
            timeout=60,
        )
        if hasattr(resp, "error") and resp.error:
            err = resp.error
            print(f"  [LLM] Error {err.get('code','?')}: {err.get('message','')}")
            return _format_no_llm(site_data, reddit_data, domain)
        if not resp or not resp.choices:
            print("  [LLM] Empty response.")
            return _format_no_llm(site_data, reddit_data, domain)
        content = resp.choices[0].message.content
        if not content:
            print(f"  [LLM] Null content (finish_reason={getattr(resp.choices[0], 'finish_reason', '?')})")
            return _format_no_llm(site_data, reddit_data, domain)
        print(f"  [LLM] Got response from {model}")
        return content.strip()
    except Exception as e:
        print(f"  [LLM] Error: {e}")
        return _format_no_llm(site_data, reddit_data, domain)


def _format_no_llm(site_data: dict, reddit_data: dict, domain: str) -> str:
    posts = reddit_data.get("posts", [])
    reddit_lines = "\n".join(
        f"  [{p['subreddit']}] {p['title']}  (score={p['score']})"
        for p in posts[:10]
    ) or "  No Reddit posts found."

    return (
        f"TITLE      : {site_data.get('title', domain)}\n"
        f"DESCRIPTION: {site_data.get('meta_description', 'N/A')}\n\n"
        f"REDDIT MENTIONS:\n{reddit_lines}\n\n"
        f"(Add your OPENROUTER_API_KEY to .env for AI-powered analysis)"
    )
