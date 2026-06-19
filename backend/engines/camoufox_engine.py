"""
Camoufox engine — modified Firefox that patches 40+ browser fingerprint leaks.
Harder to detect than Chrome-based solutions because:
  - Real Firefox rendering engine (Gecko), not Chrome
  - Patches canvas, WebGL, audio, font, screen, navigator fingerprints
  - Randomizes fingerprint per session automatically

Setup (one-time):
    pip install camoufox[geoip]
    python -m camoufox fetch
"""
import time
import random
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

CLOUDFLARE_SIGNALS = [
    "Just a moment",
    "Enable JavaScript and cookies to continue",
    "challenge-platform",
]


def is_available() -> bool:
    try:
        import camoufox  # noqa: F401
        return True
    except ImportError:
        return False


def fetch(url: str, proxy: str = None) -> dict:
    try:
        from camoufox.sync_api import Camoufox
    except ImportError:
        return {
            "error": "camoufox not installed. Run: pip install camoufox[geoip] && python -m camoufox fetch",
            "engine": "camoufox",
        }

    launch_kw = {
        "headless": True,
        "geoip": True,  # auto-match locale/timezone to exit IP geography
    }

    if proxy:
        if not proxy.startswith(("http://", "https://", "socks5://")):
            proxy = "http://" + proxy
        launch_kw["proxy"] = {"server": proxy}

    try:
        with Camoufox(**launch_kw) as browser:
            page = browser.new_page()
            page.goto(url, timeout=30000, wait_until="domcontentloaded")

            # Wait for Cloudflare / bot challenges to resolve
            for _ in range(6):
                title = page.title()
                snippet = page.content()[:2000]
                if any(sig in title or sig in snippet for sig in CLOUDFLARE_SIGNALS):
                    time.sleep(random.uniform(2.5, 4.0))
                else:
                    break

            time.sleep(random.uniform(0.8, 1.5))
            html = page.content()

            return {
                "html": html,
                "status": 200,
                "engine": "camoufox",
                "url": page.url,
                "is_cloudflare": False,
            }

    except Exception as e:
        return {"error": str(e), "engine": "camoufox"}
