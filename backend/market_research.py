"""
Professional-grade market research and SWOT analysis.
Combines website data, Reddit, Google News, HN, tech stack, and Wayback Machine
into a structured report using the LLM — same standards as industry analysts.
"""
import config


# ── LLM call ─────────────────────────────────────────────────────────────────

def _llm(prompt: str, max_tokens: int = 1800) -> str:
    from openai import OpenAI
    client = OpenAI(
        api_key=config.OPENROUTER_API_KEY,
        base_url=config.OPENROUTER_BASE_URL,
        default_headers={
            "HTTP-Referer": "https://github.com/preet1249/QuantVeil",
            "X-Title": "QuantVeil",
        },
    )
    model = config.LLM_MODEL
    print(f"  [RESEARCH] Calling {model} for market analysis...")
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.15,
            timeout=90,
        )
        if hasattr(resp, "error") and resp.error:
            err = resp.error
            print(f"  [RESEARCH] LLM error: {err.get('message', '?')}")
            return ""
        if not resp or not resp.choices:
            print("  [RESEARCH] Empty LLM response")
            return ""
        content = resp.choices[0].message.content or ""
        print("  [RESEARCH] Market analysis complete")
        return content.strip()
    except Exception as e:
        print(f"  [RESEARCH] Error: {e}")
        return ""


# ── Context formatters ────────────────────────────────────────────────────────

def _fmt_news(news: list) -> str:
    if not news:
        return "No recent news articles found."
    return "\n".join(
        f"  [{n.get('date', '')[:11]}] {n.get('source', '')} — {n.get('title', '')}"
        for n in news[:10]
    )


def _fmt_hn(hn: list) -> str:
    if not hn:
        return "No Hacker News mentions found."
    return "\n".join(
        f"  [{h.get('created_at', '')}] {h.get('points', 0)} pts, {h.get('num_comments', 0)} comments — {h.get('title', '')}"
        for h in hn[:8]
    )


def _fmt_reddit(reddit_data: dict) -> str:
    lines = []
    ai_summary = reddit_data.get("ai_summary", "")
    if ai_summary:
        lines.append(f"Reddit AI Summary:\n{ai_summary[:1200]}")
    posts = reddit_data.get("posts", [])
    if posts:
        lines.append("Top posts:")
        for p in posts[:10]:
            lines.append(f"  [{p['subreddit']}] {p['title']} (score={p['score']})")
    return "\n".join(lines) if lines else "No Reddit data."


def _fmt_tech(stack: dict) -> str:
    if not stack or not stack.get("all"):
        return "No tech stack detected."
    label = {
        "cms": "CMS/Platform", "framework": "JS Frameworks",
        "ecommerce": "E-commerce", "analytics": "Analytics",
        "marketing": "Marketing/CRM", "payments": "Payments",
        "infrastructure": "Infrastructure",
    }
    return "\n".join(
        f"  {label.get(cat, cat)}: {', '.join(stack[cat])}"
        for cat in ["cms", "framework", "ecommerce", "analytics", "marketing", "payments", "infrastructure"]
        if stack.get(cat)
    )


def _fmt_wayback(wb: dict) -> str:
    if not wb or wb.get("trend") == "unknown":
        return "Wayback Machine data unavailable or insufficient."
    lines = [wb.get("summary", "")]
    if wb.get("first_seen"):
        lines.append(f"  First archived: {wb['first_seen'][:4]}-{wb['first_seen'][4:6]}-{wb['first_seen'][6:]}")
    lines.append(f"  Page size: {wb.get('old_avg_kb', 0)} KB (6-12mo ago) → {wb.get('new_avg_kb', 0)} KB (recent)")
    return "\n".join(lines)


def _fmt_contacts(site_data: dict) -> str:
    emails  = ", ".join(site_data.get("emails", [])) or "none found"
    phones  = ", ".join(site_data.get("phones", [])) or "none found"
    socials = site_data.get("socials", {})
    social_str = ", ".join(f"{k}: {v}" for k, v in socials.items()) or "none found"
    return f"Emails: {emails}\nPhones: {phones}\nSocials: {social_str}"


# ── Main analysis function ────────────────────────────────────────────────────

def _fmt_github(gh: dict) -> str:
    if not gh or not (gh.get("has_org") or gh.get("repos")):
        return "No GitHub presence detected."
    org   = gh.get("org", {})
    repos = gh.get("repos", [])
    lines = []
    if org:
        lines.append(f"Org: {org.get('name','')} — {org.get('public_repos',0)} public repos, "
                     f"{org.get('followers',0)} followers, founded {org.get('created_at','')[:7]}")
    if repos:
        lines.append(f"Top repos by stars: " +
                     ", ".join(f"{r['name']} ({r['stars']}★)" for r in repos[:4]))
    if gh.get("top_languages"):
        lines.append(f"Primary languages: {', '.join(gh['top_languages'])}")
    if gh.get("hiring_signals"):
        lines.extend(gh["hiring_signals"])
    return "\n".join(lines) if lines else "GitHub org found but limited data."


def _fmt_crunchbase(cb: dict) -> str:
    if not cb or not cb.get("found"):
        return "Crunchbase page not accessible."
    lines = []
    if cb.get("founded"):        lines.append(f"Founded: {cb['founded']}")
    if cb.get("headquarters"):   lines.append(f"HQ: {cb['headquarters']}")
    if cb.get("employee_count"): lines.append(f"Employees: {cb['employee_count']}")
    if cb.get("funding_total"):  lines.append(f"Total Funding: {cb['funding_total']}")
    if cb.get("investors"):
        lines.append(f"Investors: {', '.join(cb['investors'][:5])}")
    if cb.get("description"):    lines.append(f"Description: {cb['description'][:200]}")
    return "\n".join(lines) if lines else "Crunchbase data found but limited."


def analyze(
    domain: str,
    site_data: dict,
    reddit_data: dict,
    news_data: dict,
    tech_stack: dict,
    wayback: dict,
    github_data: dict = None,
    crunchbase_data: dict = None,
) -> str:
    if not config.OPENROUTER_API_KEY:
        return "(Add OPENROUTER_API_KEY to .env for market research analysis)"

    brand = news_data.get("brand", domain)

    # Build concise context blocks — skip empty sections
    ctx_parts = []

    website_text = site_data.get('visible_text', '')[:1800].strip()
    if website_text:
        ctx_parts.append(
            f"WEBSITE [{domain}]\n"
            f"Title: {site_data.get('title', 'N/A')}\n"
            f"Description: {site_data.get('meta_description', '')[:300]}\n"
            f"Contacts: {_fmt_contacts(site_data)}\n"
            f"Content: {website_text}"
        )

    tech_txt = _fmt_tech(tech_stack)
    if "No tech" not in tech_txt:
        ctx_parts.append(f"TECH STACK\n{tech_txt}")

    news_txt = _fmt_news(news_data.get('news', []))
    if "No recent" not in news_txt:
        ctx_parts.append(f"GOOGLE NEWS\n{news_txt}")

    hn_txt = _fmt_hn(news_data.get('hn_posts', []))
    if "No Hacker" not in hn_txt:
        ctx_parts.append(f"HACKER NEWS\n{hn_txt}")

    reddit_txt = _fmt_reddit(reddit_data)
    if "No Reddit" not in reddit_txt:
        ctx_parts.append(f"REDDIT\n{reddit_txt}")

    wb_txt = _fmt_wayback(wayback)
    if "unavailable" not in wb_txt:
        ctx_parts.append(f"WAYBACK GROWTH\n{wb_txt}")

    gh_txt = _fmt_github(github_data or {})
    if "No GitHub" not in gh_txt:
        ctx_parts.append(f"GITHUB\n{gh_txt}")

    cb_txt = _fmt_crunchbase(crunchbase_data or {})
    if "not accessible" not in cb_txt:
        ctx_parts.append(f"CRUNCHBASE\n{cb_txt}")

    data_block = "\n\n".join(ctx_parts)

    prompt = f"""You are a senior market intelligence analyst. Write a structured report for {brand} ({domain}).

OUTPUT RULES — READ CAREFULLY:
1. Start your response IMMEDIATELY with "## COMPANY SNAPSHOT" — no preamble, no thinking, no meta-commentary.
2. Write ONLY from the DATA BLOCK below. Never invent facts.
3. Do NOT copy template text or write placeholder phrases like "specific point here".
4. Every SWOT bullet must name a real fact from the data (company name, feature, number, or quote).
5. If data is missing for a bullet, skip that bullet entirely — do not write generic filler.

DATA BLOCK:
{data_block}

REPORT FORMAT:

## COMPANY SNAPSHOT
2-3 sentences: what they do, who they serve, market position. Reference the site description and any funding/headcount data.

## SWOT ANALYSIS

### Strengths
S1. [Real strength from the data]
S2. [Real strength from the data]
S3. [Real strength from the data]

### Weaknesses
W1. [Real weakness or complaint from Reddit/reviews]
W2. [Real weakness from the data]
W3. [Real weakness from the data]

### Opportunities
O1. [Real opportunity from news, HN, or growth signal]
O2. [Real opportunity from the data]
O3. [Real opportunity from the data]

### Threats
T1. [Real competitor or threat named in the data]
T2. [Real threat from news or Reddit]
T3. [Real threat from the data]

## COMPETITIVE LANDSCAPE
Name every competitor or alternative mentioned in the Reddit, HN, or news data. One line each:
- CompetitorName — reason users compare it to {brand}

If none mentioned, write: No competitors named in available data.

## TECH STACK INTELLIGENCE
2-3 sentences on what their detected tech stack reveals about maturity, team size, and likely roadmap.

## GROWTH & HIRING SIGNALS
2-3 sentences from the Wayback trend, GitHub activity, and news.

## OUTREACH ANGLE
One sharp paragraph on the single best angle for cold outreach, based on their pain points and growth signals.
"""

    result = _llm(prompt, max_tokens=2200)
    if not result:
        return "(Market research analysis failed — check model/API key)"

    # Strip any leading reasoning or preamble the model may have emitted
    lines = result.split('\n')
    for i, line in enumerate(lines):
        if line.strip().startswith('## COMPANY SNAPSHOT'):
            result = '\n'.join(lines[i:])
            break

    return result.strip()
