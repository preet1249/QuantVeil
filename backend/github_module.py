"""
GitHub public API — no auth needed (60 req/hr unauthenticated).
Returns org info, repos, languages, stars, and activity signals.
"""
import re
import requests
from datetime import datetime, timedelta

TIMEOUT = 10
BASE    = "https://api.github.com"
HEADERS = {
    "User-Agent": "lead-intel-scraper/1.0",
    "Accept":     "application/vnd.github.v3+json",
}


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9-]", "-", name.lower()).strip("-")


def search_github(company: str, domain: str) -> dict:
    result = {
        "has_org": False, "org": {}, "repos": [],
        "top_languages": [], "total_stars": 0,
        "profile_url": None, "open_source_health": "unknown",
        "hiring_signals": [],
    }

    # Try org lookup — attempt multiple slug variations
    domain_name = domain.split(".")[0]
    for candidate in [_slug(domain_name), _slug(company), _slug(company) + "-1"]:
        if not candidate:
            continue
        try:
            r = requests.get(f"{BASE}/orgs/{candidate}", headers=HEADERS, timeout=TIMEOUT)
            if r.status_code == 200:
                org = r.json()
                result["has_org"]    = True
                result["profile_url"] = org.get("html_url")
                result["org"] = {
                    "login":        org.get("login"),
                    "name":         org.get("name") or org.get("login"),
                    "description":  (org.get("description") or "")[:200],
                    "public_repos": org.get("public_repos", 0),
                    "followers":    org.get("followers", 0),
                    "created_at":   org.get("created_at", "")[:10],
                    "url":          org.get("html_url", ""),
                    "blog":         org.get("blog", ""),
                    "location":     org.get("location", ""),
                }
                break
        except Exception:
            pass

    # Search repos
    login = result["org"].get("login", _slug(domain_name))
    query = f"org:{login}" if result["has_org"] else f"{company} in:name,description"
    try:
        r = requests.get(
            f"{BASE}/search/repositories",
            params={"q": query, "sort": "stars", "order": "desc", "per_page": 8},
            headers=HEADERS, timeout=TIMEOUT,
        )
        if r.status_code == 200:
            langs: dict[str, int] = {}
            cutoff = (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d")
            for repo in (r.json().get("items") or [])[:8]:
                result["repos"].append({
                    "name":        repo["name"],
                    "description": (repo.get("description") or "")[:120],
                    "stars":       repo.get("stargazers_count", 0),
                    "forks":       repo.get("forks_count", 0),
                    "language":    repo.get("language") or "",
                    "updated_at":  repo.get("updated_at", "")[:10],
                    "url":         repo.get("html_url", ""),
                    "open_issues": repo.get("open_issues_count", 0),
                })
                result["total_stars"] += repo.get("stargazers_count", 0)
                if repo.get("language"):
                    langs[repo["language"]] = langs.get(repo["language"], 0) + 1
            result["top_languages"] = sorted(langs, key=langs.get, reverse=True)[:5]

            # Active repos (updated < 90 days)
            active = [rep for rep in result["repos"] if rep["updated_at"] >= cutoff]
            if active:
                result["hiring_signals"].append(
                    f"{len(active)}/{len(result['repos'])} repos active in last 90 days"
                )
    except Exception:
        pass

    # Open-source health score
    stars = result["total_stars"]
    repos = len(result["repos"])
    if stars > 1000 or repos > 8:
        result["open_source_health"] = "active"
    elif stars > 100 or repos > 3:
        result["open_source_health"] = "moderate"
    elif result["has_org"]:
        result["open_source_health"] = "minimal"

    return result
