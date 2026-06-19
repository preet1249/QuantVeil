import re
import json
from bs4 import BeautifulSoup

# ── Email regex ──────────────────────────────────────────────────────────────
EMAIL_RE = re.compile(
    r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,7}\b'
)

# ── Phone regexes (US, international, generic) ───────────────────────────────
PHONE_RES = [
    re.compile(r'\+?1?[\s.\-]?\(?\d{3}\)?[\s.\-]\d{3}[\s.\-]\d{4}'),
    re.compile(r'\+\d{1,3}[\s\-]?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}'),
    re.compile(r'\(\d{3}\)[\s\-]?\d{3}[\s\-]\d{4}'),
    re.compile(r'\b\d{3}[\s.\-]\d{3}[\s.\-]\d{4}\b'),
    re.compile(r'\+44[\s\-]?\d{2,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4}'),
    re.compile(r'\+91[\s\-]?\d{5}[\s\-]?\d{5}'),
]

JUNK_EMAIL_FRAGMENTS = {
    "example.com", "test.com", "sentry.io", "w3.org", "schema.org",
    "yoursite.com", "domain.com", "company.com", "email.com",
    "placeholder", "noreply", "no-reply", "donotreply",
    "@2x.", ".png", ".jpg", ".gif", ".svg",
}

# JSON-LD schema.org keys that hold contact info
_JSONLD_EMAIL_KEYS = ("email", "contactEmail")
_JSONLD_PHONE_KEYS = ("telephone", "faxNumber", "phone")

# ── Social media platform detection ──────────────────────────────────────────
# Maps domain fragment → canonical platform name
SOCIAL_DOMAINS: dict[str, str] = {
    "facebook.com": "facebook",
    "fb.com":       "facebook",
    "fb.me":        "facebook",
    "instagram.com":"instagram",
    "twitter.com":  "twitter",
    "x.com":        "twitter",
    "linkedin.com": "linkedin",
    "youtube.com":  "youtube",
    "youtu.be":     "youtube",
    "tiktok.com":   "tiktok",
    "pinterest.com":"pinterest",
    "snapchat.com": "snapchat",
    "github.com":   "github",
    "discord.gg":   "discord",
    "discord.com":  "discord",
    "t.me":         "telegram",
    "telegram.me":  "telegram",
    "wa.me":        "whatsapp",
    "whatsapp.com": "whatsapp",
    "threads.net":  "threads",
    "bsky.app":     "bluesky",
}

# URLs that look social but aren't profile links
_SOCIAL_JUNK = (
    "/sharer", "/share", "/intent/tweet", "/dialog/share",
    "addtoany", "sharethis", "share?", "share/", "/login",
    "/signup", "/register", "/help", "/support", "/ads",
)


def _platform_of(url: str) -> str | None:
    url_lower = url.lower()
    for domain, platform in SOCIAL_DOMAINS.items():
        if domain in url_lower:
            return platform
    return None


def _is_real_profile(url: str) -> bool:
    """Filter out share buttons, login pages, and root-domain-only links."""
    from urllib.parse import urlparse
    u = url.lower()
    if any(junk in u for junk in _SOCIAL_JUNK):
        return False
    try:
        path = urlparse(url).path.strip("/")
        # Root domain with no path — not a profile
        if not path:
            return False
    except Exception:
        pass
    return True


def _clean_phone(raw: str) -> str:
    return re.sub(r'\s+', ' ', raw.strip())


def _extract_json_ld(soup: BeautifulSoup) -> tuple[set, set, dict]:
    """
    Parse <script type="application/ld+json"> blocks.
    Returns (emails, phones, socials) where socials = {platform: url}.
    JSON-LD is the highest-accuracy source for all three.
    """
    emails: set[str] = set()
    phones: set[str] = set()
    socials: dict[str, str] = {}

    def _collect_same_as(urls):
        for u in (urls if isinstance(urls, list) else [urls]):
            if not isinstance(u, str):
                continue
            platform = _platform_of(u)
            if platform and _is_real_profile(u) and platform not in socials:
                socials[platform] = u

    def _walk(node):
        if not isinstance(node, dict):
            return
        for item in node.get("@graph", []):
            _walk(item)
        for k in _JSONLD_EMAIL_KEYS:
            val = node.get(k, "")
            if val and isinstance(val, str) and "@" in val:
                emails.add(val.replace("mailto:", "").strip().lower())
        for k in _JSONLD_PHONE_KEYS:
            val = node.get(k, "")
            if val and isinstance(val, str):
                phones.add(val.strip())
        # sameAs — the standard schema.org field for social profiles
        if "sameAs" in node:
            _collect_same_as(node["sameAs"])
        for cp in node.get("contactPoint", []):
            _walk(cp if isinstance(cp, dict) else {})
        for key in ("author", "founder", "member", "employee", "contactPoint"):
            sub = node.get(key)
            if isinstance(sub, dict):
                _walk(sub)
            elif isinstance(sub, list):
                for s in sub:
                    _walk(s)

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            raw = script.string or ""
            data = json.loads(raw)
            items = data if isinstance(data, list) else [data]
            for item in items:
                _walk(item)
        except Exception:
            pass

    return emails, phones, socials


def extract(html: str) -> dict:
    # Parse with lxml before anything else so we keep the full DOM
    soup = BeautifulSoup(html, "lxml")

    # ── 1. JSON-LD structured data (highest accuracy) ────────────────────────
    jsonld_emails, jsonld_phones, socials = _extract_json_ld(soup)

    # ── 2. mailto:, tel: hrefs + social <a> links ────────────────────────────
    mailto_emails: set[str] = set()
    tel_phones: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith("mailto:"):
            addr = href[7:].split("?")[0].strip().lower()
            if addr:
                mailto_emails.add(addr)
        elif href.startswith("tel:"):
            raw = href[4:].strip().replace(" ", "").replace("-", "")
            if raw:
                tel_phones.append(raw)
        elif href.startswith("http"):
            platform = _platform_of(href)
            if platform and _is_real_profile(href) and platform not in socials:
                socials[platform] = href

    # ── 3. Regex on visible text ──────────────────────────────────────────────
    # Remove non-content tags AFTER extracting JSON-LD (scripts are already processed)
    for tag in soup(["script", "style", "noscript", "meta", "link"]):
        tag.decompose()

    text = soup.get_text(separator=" ")
    raw_html_str = str(soup)

    text_emails = {m.lower() for m in EMAIL_RE.findall(text)}
    html_emails = {m.lower() for m in EMAIL_RE.findall(raw_html_str)}

    all_emails = jsonld_emails | mailto_emails | text_emails | html_emails

    emails = sorted({
        e for e in all_emails
        if not any(frag in e for frag in JUNK_EMAIL_FRAGMENTS)
        and len(e) < 80
        and "." in e.split("@")[-1]
    })

    # ── 4. Phones (tel: hrefs + JSON-LD + regex, deduped by last-10-digits) ──
    phones_raw: dict[str, str] = {}

    def _add_phone(raw: str):
        digits = re.sub(r'\D', '', raw)
        if 7 <= len(digits) <= 15:
            fp = digits[-10:]
            if len(raw) >= len(phones_raw.get(fp, "")):
                phones_raw[fp] = raw

    # tel: hrefs (highest reliability — explicit phone links)
    for p in tel_phones:
        _add_phone(p)

    # JSON-LD phones (structured data)
    for p in jsonld_phones:
        _add_phone(p)

    # Regex phones from visible text
    for pattern in PHONE_RES:
        for m in pattern.findall(text):
            _add_phone(_clean_phone(m))

    phones = sorted(phones_raw.values())

    # ── 5. Page metadata ──────────────────────────────────────────────────────
    title = soup.title.get_text(strip=True) if soup.title else ""

    meta_desc = ""
    meta = soup.find("meta", attrs={"name": re.compile("description", re.I)})
    if meta and meta.get("content"):
        meta_desc = meta["content"][:300]

    visible_text = " ".join(text.split())[:4000]

    return {
        "emails": emails,
        "phones": phones,
        "socials": socials,
        "title": title,
        "meta_description": meta_desc,
        "visible_text": visible_text,
    }
