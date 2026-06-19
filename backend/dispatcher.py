from urllib.parse import urlparse

from engines.curl_engine import fetch as curl_fetch
from engines.drission_engine import fetch as drission_fetch
from engines import camoufox_engine

# Domains confirmed reachable without proxy during this process run.
# Once a domain loads fine direct (proxy timeout → direct retry succeeds),
# all subsequent fetches for that domain skip the proxy entirely.
_direct_domains: set[str] = set()

_PROXY_TIMEOUT = 12   # seconds — short so Tor failures fail fast


def dispatch(url: str, proxy: str = None, force_engine: str = None) -> dict:
    """
    Engine escalation chain (fastest -> most stealthy):
      curl_cffi   — TLS-spoofed, instant, session-persistent
        ↓ on CF/error
      DrissionPage — real Chrome headless with deep fingerprint injection
        ↓ on CF/error
      Camoufox    — modified Firefox, 40+ fingerprint patches, hardest to detect
    """
    if force_engine == "drission":
        print("  [ENGINE] DrissionPage (forced)")
        return drission_fetch(url, proxy)

    if force_engine == "curl":
        print("  [ENGINE] curl_cffi (forced)")
        return curl_fetch(url, proxy)

    if force_engine == "camoufox":
        print("  [ENGINE] Camoufox (forced)")
        return camoufox_engine.fetch(url, proxy)

    # ── Tier 1: curl_cffi ──────────────────────────────────────────────────────
    domain = urlparse(url).netloc

    # Skip proxy for domains already confirmed reachable direct this run
    effective_proxy = None if domain in _direct_domains else proxy
    if proxy and effective_proxy is None:
        print("  [ENGINE] curl_cffi -> direct (domain cached no-proxy)")
    else:
        print("  [ENGINE] curl_cffi -> Chrome/124 TLS fingerprint")

    proxy_timeout = _PROXY_TIMEOUT if effective_proxy else None
    result = curl_fetch(url, effective_proxy, timeout=proxy_timeout)

    if "error" not in result and not result.get("is_cloudflare"):
        return result

    if "error" in result:
        err = result.get("error", "")
        print(f"  [ENGINE] curl_cffi error: {err}")

        # Proxy timeout: retry WITHOUT proxy before launching Chrome.
        # Tor exit nodes are often blocked by small/regional sites — direct
        # curl works fine for non-Cloudflare pages.
        if effective_proxy and ("timed out" in err.lower() or "timeout" in err.lower()):
            print("  [ENGINE] Proxy timeout — retrying direct (no proxy)...")
            direct = curl_fetch(url, proxy=None)
            if "error" not in direct:
                if not direct.get("is_cloudflare"):
                    _direct_domains.add(domain)   # cache: skip proxy next time
                    return direct                  # plain site, direct works ✓
                # Direct hit Cloudflare — fall through to Chrome with this result
                result = direct
            else:
                print(f"  [ENGINE] Direct also failed: {direct.get('error', '')}")
    else:
        status = result.get("status", "?")
        print(f"  [ENGINE] Cloudflare challenge detected (HTTP {status})")
        # Real 404/410 means the page doesn't exist — no point launching Chrome
        if status in (404, 410):
            return result

    # ── Tier 2: DrissionPage ───────────────────────────────────────────────────
    # DrissionPage runs real Chrome — it does NOT support SOCKS5/Tor proxy.
    # Pass proxy=None always; Chrome's own network stack handles direct connections.
    print("  [ENGINE] >> Escalating to DrissionPage (real Chrome headless)...")
    dr = drission_fetch(url, proxy=None)

    dr_html = dr.get("html", "")
    dr_ok = "error" not in dr and not dr.get("is_cloudflare")

    # If DrissionPage returned a real page (>5KB), use it
    if dr_ok and len(dr_html) >= 5000:
        return dr

    # Under 5KB = likely still getting the CF JS challenge page, not real content
    if dr_ok and len(dr_html) < 5000:
        print(f"  [ENGINE] DrissionPage result too small ({len(dr_html):,} bytes) — still CF challenge")
    elif "error" in dr:
        print(f"  [ENGINE] DrissionPage failed: {dr['error']}")

    # ── Tier 3: Camoufox ──────────────────────────────────────────────────────
    if camoufox_engine.is_available():
        print("  [ENGINE] >> Escalating to Camoufox (modified Firefox)...")
        cf_result = camoufox_engine.fetch(url, proxy)
        if "error" not in cf_result and len(cf_result.get("html", "")) >= 5000:
            return cf_result
        if "error" in cf_result:
            print(f"  [ENGINE] Camoufox failed: {cf_result['error']}")
        else:
            print(f"  [ENGINE] Camoufox result too small ({len(cf_result.get('html',''))}) bytes)")
    else:
        print("  [ENGINE] (Camoufox not installed — skipping tier 3)")

    # Return best result we have
    if dr_ok:
        return dr
    if "error" not in dr:
        return dr
    return result
