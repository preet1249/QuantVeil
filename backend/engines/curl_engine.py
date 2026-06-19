import random
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import USER_AGENTS, TIMEOUT
from engines.session_store import load as load_cookies, save as save_cookies

IMPERSONATE_PROFILES = [
    "chrome124", "chrome120", "chrome116", "chrome110",
]

CLOUDFLARE_SIGNALS = [
    "Just a moment",
    "Enable JavaScript and cookies to continue",
    "Attention Required! | Cloudflare",
    "cf-browser-verification",
    "challenge-platform",
]


def fetch(url: str, proxy: str = None, timeout: int = None) -> dict:
    try:
        from curl_cffi import requests as curl_requests
    except ImportError:
        return {"error": "curl_cffi not installed", "engine": "curl_cffi"}

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

    proxies = {"http": proxy, "https": proxy} if proxy else None
    impersonate = random.choice(IMPERSONATE_PROFILES)

    try:
        # Use a persistent session — reuses cookies from previous visits
        # so the site sees a "returning browser" not a cold bot
        session = curl_requests.Session(impersonate=impersonate)

        saved = load_cookies(url)
        for name, value in saved.items():
            session.cookies.set(name, value)

        resp = session.get(
            url,
            headers=headers,
            timeout=timeout if timeout is not None else TIMEOUT,
            proxies=proxies,
            allow_redirects=True,
            verify=False,
        )

        # Persist any new cookies the server set
        new_cookies = {k: v for k, v in session.cookies.items()}
        if new_cookies:
            merged = {**saved, **new_cookies}
            save_cookies(url, merged)

        html = resp.text
        resp_headers = dict(resp.headers)

        is_cloudflare = (
            "cf-ray" in resp_headers
            or resp.status_code in [403, 503]
            or any(sig in html for sig in CLOUDFLARE_SIGNALS)
        )

        return {
            "html": html,
            "status": resp.status_code,
            "headers": resp_headers,
            "is_cloudflare": is_cloudflare,
            "engine": "curl_cffi",
            "impersonate": impersonate,
            "url": str(resp.url),
        }

    except Exception as e:
        return {"error": str(e), "engine": "curl_cffi"}
