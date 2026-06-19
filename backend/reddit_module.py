"""
Reddit scraper using non-headless Chrome (off-screen window).
Reddit's Akamai bot detection blocks headless mode but not visible Chrome.
Extracts both Reddit's AI summary section and individual post links.
"""
import re
import time
from bs4 import BeautifulSoup
from urllib.parse import quote as urlquote

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
window.chrome = {runtime: {}};
"""

# AI summary section headings Reddit uses
AI_SUMMARY_MARKERS = [
    "Overall Sentiment", "Major Complaints", "Use Cases",
    "Alternatives Suggested", "Quotes Representing", "What Redditors Say",
    "Positive Points", "Negative Points", "Key Takeaways",
]


def _make_page():
    from DrissionPage import ChromiumPage, ChromiumOptions
    opts = ChromiumOptions()
    opts.auto_port()
    # Non-headless with off-screen placement so it runs silently
    opts.set_argument("--window-size=1280,800")
    opts.set_argument("--window-position=-2000,-2000")
    opts.set_argument("--no-sandbox")
    opts.set_argument("--disable-gpu")
    opts.set_argument("--disable-extensions")
    opts.set_argument("--disable-blink-features=AutomationControlled")
    opts.set_browser_path(CHROME_PATH)
    return ChromiumPage(addr_or_opts=opts)


def _extract_ai_summary(soup: BeautifulSoup) -> str:
    """Pull the structured AI summary Reddit generates for searches."""
    full_text = soup.get_text(separator="\n")
    lines = [l.strip() for l in full_text.splitlines() if l.strip()]

    # Find first marker
    start_idx = None
    for i, line in enumerate(lines):
        if any(marker in line for marker in AI_SUMMARY_MARKERS):
            start_idx = max(0, i - 1)
            break

    if start_idx is None:
        return ""

    # Collect until we hit the post listing (usually after ~60 lines)
    summary_lines = lines[start_idx: start_idx + 60]
    # Trim trailing subreddit/nav noise
    trimmed = []
    for line in summary_lines:
        if line.startswith("r/") and len(line) < 30:
            break
        trimmed.append(line)

    return "\n".join(trimmed)


def _extract_posts(soup: BeautifulSoup) -> list:
    posts = []

    # Post title links (new Reddit uses data-testid="post-title")
    title_links = soup.find_all("a", attrs={"data-testid": "post-title"})

    # Scores via faceplate-number elements
    score_els = soup.find_all("faceplate-number")
    # First N numbers correspond to N posts (heuristic)
    scores = []
    for el in score_els:
        try:
            scores.append(int(el.get("number", 0)))
        except ValueError:
            scores.append(0)

    for i, link in enumerate(title_links):
        title = link.get_text(strip=True)
        href = link.get("href", "")
        subreddit = ""
        # Extract subreddit from /r/name/comments/...
        m = re.match(r"^/r/([^/]+)/", href)
        if m:
            subreddit = "r/" + m.group(1)

        posts.append({
            "title": title,
            "score": scores[i] if i < len(scores) else 0,
            "num_comments": 0,
            "subreddit": subreddit,
            "permalink": "https://www.reddit.com" + href if href.startswith("/") else href,
        })

    return posts


def scrape_reddit(domain: str) -> dict:
    print(f"  [REDDIT] Launching Chrome (off-screen) to search Reddit for '{domain}'...")

    page = None
    all_posts = []
    ai_summary = ""

    try:
        page = _make_page()
        page.run_js(STEALTH_JS)

        # Strip TLD to get brand name (basecamp.com -> basecamp)
        brand = re.sub(r'\.(com|io|co|net|org|app|ai|dev).*$', '', domain)

        # Four queries: reviews (triggers AI summary), domain, startup community, alternatives
        queries = [
            f"{brand} reviews",
            f'site:{domain}',
            f'"{brand}" site:reddit.com/r/entrepreneur OR site:reddit.com/r/startups OR site:reddit.com/r/SaaS',
            f'"{brand}" alternatives',
        ]

        for q in queries:
            url = f"https://www.reddit.com/search/?q={urlquote(q)}&sort=relevance&t=all"
            page.get(url)
            time.sleep(3.5)  # wait for SPA render

            html = page.html
            soup = BeautifulSoup(html, "lxml")

            # Extract AI summary only from first query (most relevant)
            if not ai_summary:
                ai_summary = _extract_ai_summary(soup)

            posts = _extract_posts(soup)
            print(f"  [REDDIT] Query '{q}' -> {len(posts)} posts")
            all_posts.extend(posts)

    except Exception as e:
        print(f"  [REDDIT] Error: {e}")
    finally:
        if page:
            try:
                page.quit()
            except Exception:
                pass

    # Deduplicate by title
    seen, unique = set(), []
    for p in all_posts:
        if p["title"] not in seen:
            seen.add(p["title"])
            unique.append(p)
    unique.sort(key=lambda x: x["score"], reverse=True)

    print(f"  [REDDIT] {len(unique)} unique posts | AI summary: {len(ai_summary)} chars")
    return {"posts": unique, "ai_summary": ai_summary, "domain": domain}
