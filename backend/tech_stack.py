"""
Tech stack detection from HTML content and HTTP response headers.
No external API — pure pattern matching against 50+ known technologies.
"""
import re
from bs4 import BeautifulSoup

# (pattern, tech_name, category)
SIGNATURES: list[tuple[str, str, str]] = [
    # ── CMS / Site Builders ────────────────────────────────────────────────────
    (r'wp-content/|wp-json/|wp-includes/',      "WordPress",      "cms"),
    (r'cdn\.shopify\.com|Shopify\.theme',        "Shopify",        "cms"),
    (r'static\.squarespace\.com',                "Squarespace",    "cms"),
    (r'wixstatic\.com|wix\.com/dplugins',        "Wix",            "cms"),
    (r'assets\.website-files\.com|webflow\.io',  "Webflow",        "cms"),
    (r'ghost\.io|content\.ghost\.org',           "Ghost",          "cms"),
    (r'hubspot\.net.*cms|hs-sites\.com',         "HubSpot CMS",    "cms"),
    (r'sites\.google\.com|google\.com/jsapi',    "Google Sites",   "cms"),
    (r'drupal\.js|Drupal\.settings',             "Drupal",         "cms"),
    (r'joomla',                                  "Joomla",         "cms"),

    # ── JS Frameworks / Libraries ──────────────────────────────────────────────
    (r'__NEXT_DATA__|/_next/static/',            "Next.js",        "framework"),
    (r'__NUXT__|/_nuxt/',                        "Nuxt.js",        "framework"),
    (r'___gatsby|gatsby-',                       "Gatsby",         "framework"),
    (r'react-dom|data-reactroot|__REACT',        "React",          "framework"),
    (r'vue\.min\.js|data-v-[a-f0-9]+|__vue__',  "Vue.js",         "framework"),
    (r'ng-version=|angular\.min\.js',            "Angular",        "framework"),
    (r'svelte-|__SVELTE',                        "Svelte",         "framework"),
    (r'remix\.run|__remixContext',               "Remix",          "framework"),
    (r'astro-island|astro\.build',               "Astro",          "framework"),

    # ── E-commerce ────────────────────────────────────────────────────────────
    (r'woocommerce|wc-blocks',                   "WooCommerce",    "ecommerce"),
    (r'Mage\.Cookies|mage/requirejs',            "Magento",        "ecommerce"),
    (r'bigcommerce\.com',                        "BigCommerce",    "ecommerce"),
    (r'klaviyo\.com',                            "Klaviyo",        "ecommerce"),

    # ── Analytics ─────────────────────────────────────────────────────────────
    (r'googletagmanager\.com|GTM-[A-Z0-9]+',    "Google Tag Mgr", "analytics"),
    (r'google-analytics\.com|gtag\(|UA-\d+|G-[A-Z0-9]{6,}', "Google Analytics", "analytics"),
    (r'mixpanel\.com/lib',                       "Mixpanel",       "analytics"),
    (r'cdn\.segment\.com|analytics\.js',         "Segment",        "analytics"),
    (r'static\.hotjar\.com',                     "Hotjar",         "analytics"),
    (r'plausible\.io/js',                        "Plausible",      "analytics"),
    (r'posthog\.com/static',                     "PostHog",        "analytics"),
    (r'amplitude\.com/libs',                     "Amplitude",      "analytics"),

    # ── Marketing / CRM / Support ─────────────────────────────────────────────
    (r'js\.hs-scripts\.com|hs-analytics',        "HubSpot",        "marketing"),
    (r'widget\.intercom\.io|intercomSettings',   "Intercom",       "marketing"),
    (r'js\.driftt\.com|drift\.com',              "Drift",          "marketing"),
    (r'static\.zdassets\.com|zendesk\.com',      "Zendesk",        "marketing"),
    (r'salesforce\.com|force\.com',              "Salesforce",     "marketing"),
    (r'chimpstatic\.com|mailchimp\.com',         "Mailchimp",      "marketing"),
    (r'cdn\.activecampaign\.com',                "ActiveCampaign", "marketing"),
    (r'js\.crisp\.chat|crisp\.chat',             "Crisp",          "marketing"),

    # ── Payments ──────────────────────────────────────────────────────────────
    (r'js\.stripe\.com|stripe\.com/v3',          "Stripe",         "payments"),
    (r'paypalobjects\.com|paypal\.com/sdk',      "PayPal",         "payments"),
    (r'braintreegateway\.com',                   "Braintree",      "payments"),
    (r'checkout\.razorpay\.com',                 "Razorpay",       "payments"),

    # ── Infrastructure / CDN / Hosting ────────────────────────────────────────
    (r'cloudflare\.com|cf-ray|__cf_chl',         "Cloudflare",     "infrastructure"),
    (r'amazonaws\.com|cloudfront\.net',          "AWS",            "infrastructure"),
    (r'vercel\.app|vercel\.com|_vercel',         "Vercel",         "infrastructure"),
    (r'netlify\.app|netlify\.com',               "Netlify",        "infrastructure"),
    (r'fastly\.net',                             "Fastly",         "infrastructure"),
    (r'render\.com',                             "Render",         "infrastructure"),
    (r'pages\.dev|workers\.cloudflare',          "Cloudflare Pages","infrastructure"),
    (r'nginx',                                   "nginx",          "infrastructure"),
    (r'Apache',                                  "Apache",         "infrastructure"),
    (r'Microsoft-IIS',                           "IIS",            "infrastructure"),
]

CATEGORIES = ["cms", "framework", "ecommerce", "analytics", "marketing", "payments", "infrastructure"]


def detect(html: str, headers: dict) -> dict:
    """
    Detect tech stack from HTML + HTTP headers.
    Returns dict: {category: [tech, ...], "all": [all techs]}
    """
    # Combine HTML + header string for a single regex pass
    headers_str = " ".join(f"{k}: {v}" for k, v in headers.items())
    combined = html + "\n" + headers_str

    detected: dict[str, list[str]] = {cat: [] for cat in CATEGORIES}

    for pattern, tech, category in SIGNATURES:
        if re.search(pattern, combined, re.IGNORECASE):
            if tech not in detected[category]:
                detected[category].append(tech)

    # Also pull <meta name="generator"> tag
    try:
        soup = BeautifulSoup(html, "lxml")
        gen = soup.find("meta", attrs={"name": re.compile("^generator$", re.I)})
        if gen and gen.get("content"):
            g = gen["content"].strip()
            # Add to CMS if not already covered
            if g and not any(g.lower() in t.lower() for cat in detected.values() for t in cat):
                detected["cms"].append(g)
    except Exception:
        pass

    all_techs = [t for cat in CATEGORIES for t in detected[cat]]
    detected["all"] = all_techs
    return detected


def format_for_display(stack: dict) -> list[str]:
    """Return human-readable lines for terminal output."""
    label_map = {
        "cms":            "CMS / Platform   ",
        "framework":      "JS Framework     ",
        "ecommerce":      "E-commerce       ",
        "analytics":      "Analytics        ",
        "marketing":      "Marketing / CRM  ",
        "payments":       "Payments         ",
        "infrastructure": "Infrastructure   ",
    }
    lines = []
    for cat in CATEGORIES:
        techs = stack.get(cat, [])
        if techs:
            lines.append(f"  {label_map[cat]}: {', '.join(techs)}")
    return lines
