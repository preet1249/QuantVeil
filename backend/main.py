#!/usr/bin/env python3
"""
QuantVeil — cold outreach + market intelligence CLI
Usage:
    python main.py <url>
    python main.py <url> --proxy             # force public proxy pool (Tor auto-detected too)
    python main.py <url> --engine curl       # force curl_cffi
    python main.py <url> --engine drission   # force DrissionPage
    python main.py <url> --engine camoufox   # force Camoufox (modified Firefox)
    python main.py <url> --no-research       # skip market research (faster)

Tor Browser is auto-detected and launched at startup if installed.
"""

import sys
import io
import os
import time
import argparse
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

# Force UTF-8 so emoji/special chars in scraped text don't crash cp1252
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from dispatcher import dispatch
from extractor import extract
from reddit_module import scrape_reddit
from llm_client import analyze
from contact_finder import find_contact_pages
import tech_stack as tech_stack_mod
import news_module
import wayback_module
import market_research


# ── Helpers ───────────────────────────────────────────────────────────────────

def _banner():
    print("""
+======================================================+
|      QUANTVEIL  +  MARKET INTELLIGENCE TOOL         |
|  curl / DrissionPage / Camoufox / Reddit / News     |
+======================================================+""")


def _section(title: str):
    print(f"\n{'-'*56}")
    print(f"  {title}")
    print(f"{'-'*56}")


def _normalize_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def _get_domain(url: str) -> str:
    return urlparse(url).netloc.replace("www.", "")


def _prompt_api_key():
    if not config.OPENROUTER_API_KEY:
        if sys.stdin.isatty():
            print("\n  [LLM] No OPENROUTER_API_KEY found in environment.")
            key = input("  Enter your OpenRouter API key (or press Enter to skip AI): ").strip()
            if key:
                config.OPENROUTER_API_KEY = key
                os.environ["OPENROUTER_API_KEY"] = key
                return
        print("  [LLM] No API key - skipping AI analysis. Add to .env to enable.")


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run(url: str, use_proxy: bool = False, force_engine: str = None, do_research: bool = True):
    _banner()
    url    = _normalize_url(url)
    domain = _get_domain(url)
    start  = time.time()

    print(f"\n  TARGET : {url}")
    print(f"  DOMAIN : {domain}")

    # ── Tor / proxy auto-detection ────────────────────────────────────────────
    proxy = None
    from proxy_rotator import check_tor, find_tor_browser, launch_tor_browser, ProxyRotator

    tor_proxy = check_tor()
    if not tor_proxy:
        exe = find_tor_browser()
        if exe:
            _section("TOR BROWSER")
            print("  Found Tor Browser — launching in background...")
            if launch_tor_browser(exe):
                tor_proxy = "socks5://127.0.0.1:9150"
            else:
                print("  Tor did not start in time — running without proxy")

    if tor_proxy:
        proxy = tor_proxy
        print(f"  [PROXY] Tor active: {proxy}")
    elif use_proxy:
        _section("PROXY POOL")
        rotator = ProxyRotator()
        count = rotator.load(max_to_test=120, workers=25)
        if count:
            proxy = rotator.get()
            print(f"  Active proxy: {proxy}")
        else:
            print("  No working proxies found - proceeding without proxy.")

    # ── Step 1 / 4 : Scrape website ───────────────────────────────────────────
    _section("1 / 4  |  SCRAPING WEBSITE")
    result     = dispatch(url, proxy=proxy, force_engine=force_engine)
    html       = result.get("html", "")
    headers    = result.get("headers", {})
    engine_used = result.get("engine", "unknown")

    if "error" in result and not html:
        print(f"  [FAIL] {result['error']}")
    else:
        print(f"  [OK]   engine={engine_used}  |  {len(html):,} bytes  |  HTTP {result.get('status', '?')}")

    # Detect tech stack immediately from homepage HTML + headers (instant, no network)
    stack = tech_stack_mod.detect(html, headers) if html else {}
    if stack.get("all"):
        print(f"  [TECH] Detected: {', '.join(stack['all'][:8])}")

    # ── Step 2 / 4 : Extract contacts ─────────────────────────────────────────
    _section("2 / 4  |  EXTRACTING CONTACTS")

    homepage_extracted = extract(html) if html else {
        "emails": [], "phones": [], "socials": {},
        "title": domain, "meta_description": "", "visible_text": "",
    }

    all_emails  = set(homepage_extracted["emails"])
    all_phones  = set(homepage_extracted["phones"])
    all_socials = dict(homepage_extracted.get("socials", {}))

    if html:
        def _engine(u):
            return dispatch(u, proxy=proxy, force_engine=force_engine)

        site_is_cf = result.get("is_cloudflare", False) or engine_used in ("drission", "camoufox")
        contact_pages = find_contact_pages(
            url, html, _engine, max_pages=3, site_is_cloudflare=site_is_cf
        )
        for cp in contact_pages:
            cp_data     = extract(cp["html"])
            new_emails  = set(cp_data["emails"]) - all_emails
            new_phones  = set(cp_data["phones"]) - all_phones
            new_socials = {k: v for k, v in cp_data.get("socials", {}).items() if k not in all_socials}
            if new_emails or new_phones or new_socials:
                print(f"  [+] {cp['url']}")
                for e in new_emails:
                    print(f"      email  -> {e}")
                for p in new_phones:
                    print(f"      phone  -> {p}")
                for k, v in new_socials.items():
                    print(f"      {k:<10} -> {v}")
            all_emails  |= set(cp_data["emails"])
            all_phones  |= set(cp_data["phones"])
            all_socials.update(cp_data.get("socials", {}))
            if not homepage_extracted.get("meta_description") and cp_data.get("meta_description"):
                homepage_extracted["meta_description"] = cp_data["meta_description"]

    emails  = sorted(all_emails)
    phones  = sorted(all_phones)
    homepage_extracted["emails"]  = emails
    homepage_extracted["phones"]  = phones
    homepage_extracted["socials"] = all_socials

    print(f"\n  Emails  ({len(emails)} total)")
    for e in emails:
        print(f"    -> {e}")
    if not emails:
        print("    - none detected")

    print(f"  Phones  ({len(phones)} total)")
    for p in phones:
        print(f"    -> {p}")
    if not phones:
        print("    - none detected")

    print(f"  Socials ({len(all_socials)} found)")
    for platform, link in sorted(all_socials.items()):
        print(f"    [{platform}] {link}")
    if not all_socials:
        print("    - none detected")

    # ── Step 3 / 4 : Reddit + News + Wayback (run news & wayback in parallel) ─
    _section("3 / 4  |  REDDIT + NEWS + INTELLIGENCE")

    # Run Reddit, News, and Wayback Machine concurrently to save time
    page_title = homepage_extracted.get("title", "")
    with ThreadPoolExecutor(max_workers=3) as ex:
        f_reddit  = ex.submit(scrape_reddit, domain)
        f_news    = ex.submit(news_module.fetch_all, domain, page_title)
        f_wayback = ex.submit(wayback_module.get_growth_indicators, domain)
        reddit_data = f_reddit.result()
        news_data   = f_news.result()
        wayback     = f_wayback.result()

    # Reddit output
    ai_summary = reddit_data.get("ai_summary", "")
    posts      = reddit_data.get("posts", [])
    if ai_summary:
        print(f"\n  Reddit AI Summary:")
        for line in ai_summary.splitlines()[:15]:
            print(f"    {line}")
    if posts:
        print(f"\n  Top Reddit posts ({len(posts)} found):")
        for i, p in enumerate(posts[:5], 1):
            print(f"  {i:>2}. [{p['subreddit']}] {p['title'][:68]}")
            print(f"       score={p['score']}  {p['permalink'][:68]}")

    # News output
    news_items = news_data.get("news", [])
    hn_posts   = news_data.get("hn_posts", [])
    if news_items:
        print(f"\n  Recent News ({len(news_items)} articles):")
        for n in news_items[:5]:
            print(f"    [{n.get('date','')[:11]}] {n.get('source','')} — {n.get('title','')[:65]}")
    if hn_posts:
        print(f"\n  Hacker News ({len(hn_posts)} mentions):")
        for h in hn_posts[:4]:
            print(f"    [{h.get('points',0)} pts] {h.get('title','')[:65]}")

    # Wayback output
    wb_summary = wayback.get("summary", "")
    if wb_summary:
        print(f"\n  Growth Trend: {wb_summary}")

    # ── Step 4 / 4 : AI Analysis + Market Research ────────────────────────────
    _section("4 / 4  |  AI ANALYSIS + MARKET RESEARCH")
    _prompt_api_key()

    # Cold outreach brief (existing)
    cold_outreach = analyze(homepage_extracted, reddit_data, domain)

    # Professional market research (new)
    research_report = ""
    if do_research and config.OPENROUTER_API_KEY:
        research_report = market_research.analyze(
            domain       = domain,
            site_data    = homepage_extracted,
            reddit_data  = reddit_data,
            news_data    = news_data,
            tech_stack   = stack,
            wayback      = wayback,
        )

    # ── Final report ──────────────────────────────────────────────────────────
    elapsed = time.time() - start

    print(f"\n{'='*56}")
    print(f"  QUANTVEIL REPORT  -  {domain}")
    print(f"{'='*56}")

    # Contacts
    print(f"\nCONTACTS:")
    print(f"  Emails : {', '.join(emails) if emails else 'none found'}")
    print(f"  Phones : {', '.join(phones) if phones else 'none found'}")
    if all_socials:
        print(f"  Socials:")
        for platform, link in sorted(all_socials.items()):
            print(f"    {platform:<12} {link}")
    else:
        print(f"  Socials: none found")

    # Tech stack
    tech_lines = tech_stack_mod.format_for_display(stack)
    if tech_lines:
        print(f"\nTECH STACK:")
        for line in tech_lines:
            print(line)

    # Cold outreach brief
    print(f"\nCOLD OUTREACH BRIEF:\n")
    print(cold_outreach)

    # Market research
    if research_report:
        print(f"\n{'='*56}")
        print(f"  MARKET INTELLIGENCE REPORT  -  {domain}")
        print(f"{'='*56}\n")
        print(research_report)

    print(f"\n{'-'*56}")
    print(f"  Done in {elapsed:.1f}s  |  engine={engine_used}")
    print(f"{'-'*56}\n")


# ── CLI entry point ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="QuantVeil - emails, phones, socials, Reddit, news & market intelligence"
    )
    parser.add_argument("url", help="Target URL (e.g. https://example.com)")
    parser.add_argument("--proxy",       action="store_true", help="Auto-load free proxies")
    parser.add_argument("--engine",      choices=["curl", "drission", "camoufox"], help="Force engine")
    parser.add_argument("--key",         metavar="OPENROUTER_KEY", help="OpenRouter API key")
    parser.add_argument("--no-research", action="store_true", help="Skip market research (faster)")

    args = parser.parse_args()

    if args.key:
        config.OPENROUTER_API_KEY = args.key
        os.environ["OPENROUTER_API_KEY"] = args.key

    run(
        args.url,
        use_proxy   = args.proxy,
        force_engine = args.engine,
        do_research  = not args.no_research,
    )


if __name__ == "__main__":
    main()
