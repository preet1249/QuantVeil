"""
Crunchbase public page scraper — uses our 3-tier bypass engine.
Best-effort: Crunchbase is Cloudflare-protected and JS-heavy.
Extracts what it can from the rendered HTML.
"""
import re
import json
from bs4 import BeautifulSoup


def _slug_candidates(company: str, domain: str) -> list:
    domain_name = domain.split(".")[0].lower()
    clean = re.sub(r"[^a-z0-9]", "-", company.lower()).strip("-")
    return list(dict.fromkeys([domain_name, clean, clean + "-1", clean + "-llc"]))


def search_crunchbase(company: str, domain: str, proxy: str = None) -> dict:
    from dispatcher import dispatch

    result = {
        "found": False, "url": None,
        "description": "", "founded": "", "headquarters": "",
        "employee_count": "", "funding_total": "",
        "funding_rounds": [], "investors": [],
        "categories": [],
    }

    for slug in _slug_candidates(company, domain):
        url = f"https://www.crunchbase.com/organization/{slug}"
        try:
            r = dispatch(url, proxy=proxy, force_engine=None)
            html = r.get("html", "")
            if len(html) < 4000:
                continue

            soup = BeautifulSoup(html, "lxml")
            text = soup.get_text(separator=" ", strip=True)

            # Check it's a real org page (not 404/search)
            if "Page not found" in text or "No results found" in text[:1000]:
                continue

            result["found"] = True
            result["url"] = url

            # JSON-LD (most reliable source on Crunchbase)
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string or "")
                    if not isinstance(data, dict):
                        continue
                    result["description"] = result["description"] or (data.get("description") or "")[:400]
                    result["founded"]     = result["founded"]     or str(data.get("foundingDate") or "")
                    addr = data.get("address") or {}
                    if isinstance(addr, dict):
                        result["headquarters"] = addr.get("addressLocality", "")
                except Exception:
                    pass

            # Funding total  (e.g. "$12.5M Total Funding")
            fund_m = re.search(r"\$[\d.,]+\s*[BMK]?\s*(?:Total\s+)?Funding", text, re.I)
            if fund_m:
                result["funding_total"] = fund_m.group(0).strip()

            # Employee count
            emp_m = re.search(r"(\d{1,4}[-–]\d{1,4}|\d{1,4}\+?)\s+[Ee]mployee", text)
            if emp_m:
                result["employee_count"] = emp_m.group(0).strip()

            # Founded year fallback
            if not result["founded"]:
                yr_m = re.search(r"[Ff]ounded\s+(?:in\s+)?(\d{4})", text)
                if yr_m:
                    result["founded"] = yr_m.group(1)

            # Headquarters fallback
            if not result["headquarters"]:
                hq_m = re.search(r"(?:Headquarters|HQ)\s*[:·]\s*([A-Z][^·\n]{3,50})", text)
                if hq_m:
                    result["headquarters"] = hq_m.group(1).strip()

            # Investors — look for "Lead Investors" or "Investors" section text
            investor_section = re.search(
                r"(?:Investors|Lead Investors)[:\s]+([A-Z][^\n]{10,300})", text
            )
            if investor_section:
                raw = investor_section.group(1)
                result["investors"] = [i.strip() for i in re.split(r"[,·]", raw) if i.strip()][:8]

            break  # success

        except Exception:
            continue

    return result
