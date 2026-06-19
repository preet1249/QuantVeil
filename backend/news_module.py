"""
Real-time news intelligence — no API keys required.

Sources:
  1. Google News RSS  — latest articles about the company/brand
  2. Hacker News      — tech community discussions (Algolia public API)
"""
import xml.etree.ElementTree as ET
import json
import re
import requests

TIMEOUT = 10


def _brand_from_domain(domain: str, title: str = "") -> str:
    """Extract a clean brand/company name for news searches."""
    if title:
        # Take the part before common separators
        for sep in [" | ", " - ", " — ", " : ", " :: "]:
            if sep in title:
                return title.split(sep)[0].strip()
        # If title is short, use it directly
        if len(title) < 40:
            return title.strip()
    # Fall back to domain without TLD
    return re.sub(r'\.(com|net|org|io|co|app|ai|dev)$', '', domain, flags=re.I)


def fetch_google_news(brand: str) -> list[dict]:
    """Fetch latest Google News RSS articles for a brand. Returns up to 10 articles."""
    query = brand.replace(" ", "+")
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    try:
        resp = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            return []
        # Google News wraps title as "Article Title - Source Name"
        root = ET.fromstring(resp.content)
        items = []
        for item in root.findall(".//item")[:10]:
            raw_title = item.findtext("title", "")
            pub_date  = item.findtext("pubDate", "")[:25]
            source_el = item.find("source")
            source    = source_el.text if source_el is not None else ""
            # Strip source suffix from title if present
            title = raw_title.rsplit(" - ", 1)[0] if " - " in raw_title else raw_title
            items.append({
                "title":  title.strip(),
                "source": source.strip(),
                "date":   pub_date.strip(),
            })
        return items
    except Exception:
        return []


def fetch_hacker_news(domain: str, brand: str) -> list[dict]:
    """
    Search Hacker News via Algolia public API (no key needed).
    Tries domain first, then brand name; deduplicates by objectID.
    """
    seen: set[str] = set()
    results: list[dict] = []

    for query in [domain, brand]:
        if not query:
            continue
        url = (
            f"https://hn.algolia.com/api/v1/search"
            f"?query={requests.utils.quote(query)}&tags=story&hitsPerPage=8"
        )
        try:
            resp = requests.get(url, timeout=TIMEOUT)
            if resp.status_code != 200:
                continue
            data = resp.json()
            for hit in data.get("hits", []):
                oid = hit.get("objectID", "")
                if oid in seen:
                    continue
                seen.add(oid)
                results.append({
                    "title":        hit.get("title", ""),
                    "url":          hit.get("url", ""),
                    "points":       hit.get("points", 0) or 0,
                    "num_comments": hit.get("num_comments", 0) or 0,
                    "created_at":   hit.get("created_at", "")[:10],
                    "hn_url":       f"https://news.ycombinator.com/item?id={oid}",
                })
        except Exception:
            pass

    # Sort by points descending
    results.sort(key=lambda x: x["points"], reverse=True)
    return results[:8]


def fetch_all(domain: str, page_title: str = "") -> dict:
    """Main entry point — fetches news + HN concurrently."""
    from concurrent.futures import ThreadPoolExecutor
    brand = _brand_from_domain(domain, page_title)
    print(f"  [NEWS] Searching for '{brand}'...")

    with ThreadPoolExecutor(max_workers=2) as ex:
        f_news = ex.submit(fetch_google_news, brand)
        f_hn   = ex.submit(fetch_hacker_news, domain, brand)
        news   = f_news.result()
        hn     = f_hn.result()

    print(f"  [NEWS] {len(news)} news articles | {len(hn)} HN mentions")
    return {"brand": brand, "news": news, "hn_posts": hn}
