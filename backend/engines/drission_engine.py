import time
import random
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Injected via CDP before any page script runs — each session gets unique
# randomized canvas/WebGL/audio/screen values so every scrape looks like
# a different physical device.
_STEALTH_JS = """
(function() {
    const _seed = Math.random();
    const _int  = (n) => Math.floor(_seed * n);

    // --- navigator.webdriver ---
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

    // --- navigator.plugins (headless has 0, real Chrome has many) ---
    Object.defineProperty(navigator, 'plugins', {
        get: () => { const a = [1,2,3,4,5]; a.item = i => a[i]; a.namedItem = () => null; a.refresh = () => {}; return a; }
    });

    // --- navigator.languages ---
    Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });

    // --- chrome.runtime (headless lacks this) ---
    if (!window.chrome) window.chrome = {};
    if (!window.chrome.runtime) window.chrome.runtime = {};

    // --- Canvas 2D fingerprint noise ---
    const _origToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(type, quality) {
        const ctx = this.getContext('2d');
        if (ctx) {
            const imgData = ctx.getImageData(0, 0, this.width || 1, this.height || 1);
            for (let i = 0; i < imgData.data.length; i += 100) {
                imgData.data[i] ^= (_int(3));
            }
            ctx.putImageData(imgData, 0, 0);
        }
        return _origToDataURL.apply(this, arguments);
    };

    // --- WebGL vendor / renderer rotation ---
    const _VENDORS   = ['Intel Inc.', 'NVIDIA Corporation', 'AMD', 'Google Inc.'];
    const _RENDERERS = [
        'Intel Iris Pro OpenGL Engine',
        'ANGLE (NVIDIA GeForce GTX 1660 Ti Direct3D11 vs_5_0 ps_5_0)',
        'AMD Radeon Pro 5500M OpenGL Engine',
        'ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0)',
    ];
    const _vendor   = _VENDORS[_int(_VENDORS.length)];
    const _renderer = _RENDERERS[_int(_RENDERERS.length)];
    const _patchWebGL = (ctx) => {
        if (!ctx) return;
        const orig = ctx.getParameter.bind(ctx);
        ctx.getParameter = (param) => {
            if (param === 37445) return _vendor;    // UNMASKED_VENDOR_WEBGL
            if (param === 37446) return _renderer;  // UNMASKED_RENDERER_WEBGL
            return orig(param);
        };
    };
    const _origGetCtx = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function(type, attribs) {
        const ctx = _origGetCtx.apply(this, arguments);
        if (type === 'webgl' || type === 'webgl2') _patchWebGL(ctx);
        return ctx;
    };

    // --- Screen resolution jitter ---
    const _W = [1366, 1440, 1536, 1680, 1920, 2560][_int(6)];
    const _H = [768,  900,  864,  1050, 1080, 1440][_int(6)];
    Object.defineProperty(screen, 'width',       { get: () => _W });
    Object.defineProperty(screen, 'height',      { get: () => _H });
    Object.defineProperty(screen, 'availWidth',  { get: () => _W });
    Object.defineProperty(screen, 'availHeight', { get: () => _H - 40 });

    // --- Permissions API (headless returns 'denied' for notifications) ---
    if (navigator.permissions && navigator.permissions.query) {
        const _origQuery = navigator.permissions.query.bind(navigator.permissions);
        navigator.permissions.query = (desc) => {
            if (desc && desc.name === 'notifications') {
                return Promise.resolve({ state: 'prompt', onchange: null });
            }
            return _origQuery(desc);
        };
    }
})();
"""


def fetch(url: str, proxy: str = None) -> dict:
    try:
        from DrissionPage import ChromiumPage, ChromiumOptions
    except ImportError:
        return {"error": "DrissionPage not installed", "engine": "drission"}

    opts = ChromiumOptions()
    opts.auto_port()
    opts.set_argument("--headless")
    opts.set_argument("--disable-blink-features=AutomationControlled")
    opts.set_argument("--no-sandbox")
    opts.set_argument("--disable-dev-shm-usage")
    opts.set_argument("--disable-gpu")
    opts.set_argument("--disable-extensions")
    opts.set_argument("--window-size=1920,1080")
    opts.set_argument("--lang=en-US")
    opts.set_pref("credentials_enable_service", False)
    opts.set_pref("profile.password_manager_enabled", False)

    if proxy:
        opts.set_proxy(proxy)

    page = None
    try:
        for attempt in range(2):
            try:
                page = ChromiumPage(addr_or_opts=opts)
                break
            except Exception:
                if attempt == 0:
                    time.sleep(3)
                    opts.auto_port()
                else:
                    raise

        # Inject stealth fingerprint script before ANY page loads via CDP.
        # This runs before the site's own JS so the patches are already in
        # place when anti-bot scripts check fingerprints.
        try:
            page.run_cdp("Page.addScriptToEvaluateOnNewDocument",
                         source=_STEALTH_JS)
        except Exception:
            # Fallback: inject after load (less effective but better than nothing)
            page.run_js(_STEALTH_JS)

        page.get(url)

        # Wait for Cloudflare / Akamai challenge to auto-resolve
        for _ in range(5):
            title = page.title or ""
            html_peek = page.html or ""
            if "Just a moment" in title or "Just a moment" in html_peek:
                time.sleep(random.uniform(2.5, 4.0))
            else:
                break

        # Base wait for JS frameworks to render initial content
        time.sleep(random.uniform(1.5, 2.5))

        # If page is suspiciously small, the JS app hasn't rendered yet.
        # Scroll to trigger lazy loaders and wait for network to settle.
        html = page.html or ""
        if len(html) < 5000:
            try:
                page.run_js("window.scrollTo(0, document.body.scrollHeight / 2)")
            except Exception:
                pass
            time.sleep(3.0)
            html = page.html or ""

        # Second scroll pass for stubborn SPAs
        if len(html) < 5000:
            try:
                page.run_js("window.scrollTo(0, 0)")
            except Exception:
                pass
            time.sleep(2.0)
            html = page.html or ""

        final_url = page.url

        return {
            "html": html,
            "status": 200,
            "engine": "drission",
            "url": final_url,
            "is_cloudflare": False,
        }

    except Exception as e:
        return {"error": str(e), "engine": "drission"}

    finally:
        if page:
            try:
                page.quit()
            except Exception:
                pass
