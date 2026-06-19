"""
Contact page discovery — no LLM used.

Priority order (original, proven):
  1. Homepage link scoring — score <a> tags by contact keywords
  2. Brute-force common paths — /contact, /about, /team, etc.
  3. Sitemap.xml — LAZY fallback, only runs if steps 1+2 didn't find enough pages

Non-Cloudflare: async curl_cffi (all at once, fast)
Cloudflare: sequential full engine (avoids spawning many Chrome instances)
"""
import asyncio
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

# ── Keyword scoring ───────────────────────────────────────────────────────────

HREF_KEYWORDS = {
    "contact": 10, "reach": 8, "get-in-touch": 8, "getintouch": 8,
    "hello": 7, "talk": 6, "hire": 6, "connect": 5,
    "about": 4, "team": 4, "people": 3, "us": 2, "support": 3, "help": 2,
}
ANCHOR_KEYWORDS = {
    "contact": 10, "reach us": 9, "get in touch": 9, "say hello": 8,
    "talk to us": 8, "hire us": 7, "email us": 8, "connect": 5,
    "about": 4, "team": 4, "our team": 5, "support": 3,
}
COMMON_PATHS = [
    "/contact", "/contact-us", "/contactus", "/reach-us", "/reach",
    "/get-in-touch", "/getintouch", "/say-hello", "/hello",
    "/about", "/about-us", "/aboutus",
    "/team", "/our-team", "/people", "/company",
    "/support", "/help", "/talk-to-us", "/hire-us",
    "/connect", "/lets-talk", "/email-us",
    "/pages/contact", "/pages/about", "/en/contact", "/en/about",
]

CLOUDFLARE_SIGNALS = [
    "Just a moment", "Enable JavaScript and cookies to continue",
    "cf-browser-verification", "challenge-platform",
]


# ── Scoring ───────────────────────────────────────────────────────────────────

def _score_url(href: str, anchor: str = "") -> int:
    score = 0
    h, a = href.lower(), anchor.lower()
    for kw, w in HREF_KEYWORDS.items():
        if kw in h:
            score += w
    for kw, w in ANCHOR_KEYWORDS.items():
        if kw in a:
            score += w
    return score


# ── Homepage link scoring ─────────────────────────────────────────────────────

def _is_internal(href: str, netloc: str) -> bool:
    p = urlparse(href)
    return (not p.scheme) or (netloc in p.netloc)


def _extract_candidate_links(html: str, base_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    netloc = urlparse(base_url).netloc
    seen: set[str] = set()
    candidates = []

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        anchor = a.get_text(strip=True)
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        if not _is_internal(href, netloc):
            continue
        full = urljoin(base_url, href).split("#")[0].rstrip("/")
        if full in seen or full == base_url.rstrip("/"):
            continue
        seen.add(full)
        score = _score_url(href, anchor)
        if score > 0:
            candidates.append({"url": full, "score": score, "anchor": anchor})

    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates


# ── Sitemap (lazy fallback only) ──────────────────────────────────────────────

def _get_sitemap_contact_urls(origin: str, curl_fetch) -> list[str]:
    sitemap_candidates = []
    try:
        r = curl_fetch(origin + "/robots.txt")
        if r.get("html"):
            for line in r["html"].splitlines():
                if line.lower().startswith("sitemap:"):
                    url = line.split(":", 1)[1].strip()
                    if url.startswith("http"):
                        sitemap_candidates.insert(0, url)
    except Exception:
        pass

    for path in ["/sitemap.xml", "/sitemap_index.xml"]:
        sitemap_candidates.append(origin + path)

    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    found_urls: list[str] = []

    for sm_url in sitemap_candidates[:3]:
        try:
            r = curl_fetch(sm_url)
            content = r.get("html", "")
            if not content or r.get("status") != 200:
                continue
            if "<urlset" not in content and "<sitemapindex" not in content:
                continue

            root = ET.fromstring(content)

            for child_sm in root.findall(".//sm:sitemap/sm:loc", ns):
                try:
                    sub = curl_fetch(child_sm.text.strip())
                    if sub.get("html") and "<urlset" in sub["html"]:
                        sub_root = ET.fromstring(sub["html"])
                        for loc in sub_root.findall(".//sm:loc", ns):
                            u = loc.text.strip()
                            if _score_url(u) >= 5:
                                found_urls.append(u)
                except Exception:
                    pass

            for loc in root.findall(".//sm:loc", ns):
                u = loc.text.strip()
                if _score_url(u) >= 5:
                    found_urls.append(u)

            if found_urls:
                break
        except Exception:
            pass

    found_urls.sort(key=lambda u: _score_url(u), reverse=True)
    return list(dict.fromkeys(found_urls))


# ── Async prober (non-CF) ─────────────────────────────────────────────────────

def _is_cloudflare_html(html: str, headers: dict) -> bool:
    return "cf-ray" in headers or any(s in html for s in CLOUDFLARE_SIGNALS)


async def _async_fetch(url: str, session, headers: dict) -> dict | None:
    try:
        resp = await session.get(url, headers=headers, timeout=10,
                                 allow_redirects=True, verify=False)
        html = resp.text
        h = dict(resp.headers)
        if resp.status_code == 200 and len(html) > 500 and not _is_cloudflare_html(html, h):
            return {"url": url, "html": html}
    except Exception:
        pass
    return None


async def _async_probe(urls: list[str]) -> list[dict]:
    from curl_cffi.requests import AsyncSession
    import random
    from config import USER_AGENTS

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    results = []
    async with AsyncSession(impersonate="chrome124") as session:
        tasks = [_async_fetch(u, session, headers) for u in urls]
        for r in await asyncio.gather(*tasks, return_exceptions=True):
            if isinstance(r, dict):
                results.append(r)
    return results


# ── Sequential prober (CF) ────────────────────────────────────────────────────

def _fetch_with_engine(url: str, engine_fn) -> dict | None:
    try:
        result = engine_fn(url)
        html = result.get("html", "")
        if result.get("status") == 200 and len(html) > 500:
            return {"url": url, "html": html}
    except Exception:
        pass
    return None


# ── Main entry point ──────────────────────────────────────────────────────────

def find_contact_pages(
    homepage_url: str,
    homepage_html: str,
    engine_fn,
    max_pages: int = 3,
    site_is_cloudflare: bool = False,
) -> list[dict]:
    base = homepage_url.rstrip("/")
    parsed = urlparse(base)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    from engines.curl_engine import fetch as curl_fetch

    # ── Step 1: Homepage link scoring ─────────────────────────────────────────
    print("  [CONTACT] Scanning homepage links...")
    candidates = _extract_candidate_links(homepage_html, base)
    if candidates:
        top = candidates[0]
        print(f"  [CONTACT] Top link: {top['anchor']!r} (score {top['score']}) -> {top['url']}")

    # ── Build URL list: homepage links → brute-force ──────────────────────────
    url_priority: list[str] = []
    url_score_map: dict[str, tuple[int, str]] = {}
    seen: set[str] = set()

    def _add(url: str, score: int = 0, anchor: str = ""):
        if url not in seen:
            url_priority.append(url)
            url_score_map[url] = (score, anchor)
            seen.add(url)

    for c in candidates[:10]:
        _add(c["url"], c["score"], c.get("anchor", ""))

    for path in COMMON_PATHS:
        _add(origin + path, _score_url(path), "")

    # ── Step 2: Probe ─────────────────────────────────────────────────────────
    scored_results: list[dict] = []

    if site_is_cloudflare:
        to_probe = url_priority[:6]
        print(f"  [CONTACT] Cloudflare site — sequential probe of {len(to_probe)} URLs...")
        for u in to_probe:
            r = _fetch_with_engine(u, engine_fn)
            if r:
                score, anchor = url_score_map.get(u, (0, ""))
                r["score"] = score
                scored_results.append(r)
                if len(scored_results) >= max_pages:
                    break
    else:
        to_probe = url_priority[:20]
        print(f"  [CONTACT] Async probing {len(to_probe)} URLs...")
        try:
            loop = asyncio.new_event_loop()
            raw = loop.run_until_complete(_async_probe(to_probe))
            loop.close()
        except Exception as e:
            print(f"  [CONTACT] Async failed ({e}), falling back to sync...")
            raw = []
            with ThreadPoolExecutor(max_workers=10) as ex:
                futs = {ex.submit(curl_fetch, u): u for u in to_probe}
                for fut in as_completed(futs):
                    res = fut.result()
                    if res.get("status") == 200 and len(res.get("html", "")) > 500:
                        raw.append({"url": futs[fut], "html": res["html"]})

        for r in raw:
            score, anchor = url_score_map.get(r["url"], (0, ""))
            r["score"] = score
            scored_results.append(r)

    scored_results.sort(key=lambda x: x["score"], reverse=True)
    pages = scored_results[:max_pages]

    # ── Step 3: Sitemap fallback (only if we still need more pages) ───────────
    if len(pages) < max_pages and not site_is_cloudflare:
        print(f"  [CONTACT] Only {len(pages)} page(s) found — trying sitemap fallback...")
        sitemap_urls = _get_sitemap_contact_urls(origin, curl_fetch)
        new_urls = [u for u in sitemap_urls[:10] if u not in seen]
        if new_urls:
            try:
                loop = asyncio.new_event_loop()
                extra = loop.run_until_complete(_async_probe(new_urls))
                loop.close()
            except Exception:
                extra = []
            for r in extra:
                r["score"] = _score_url(r["url"])
                pages.append(r)
            pages.sort(key=lambda x: x["score"], reverse=True)
            pages = pages[:max_pages]

    print(f"  [CONTACT] {len(pages)} contact page(s) ready")
    for p in pages:
        print(f"    -> {p['url']}")
    return pages
