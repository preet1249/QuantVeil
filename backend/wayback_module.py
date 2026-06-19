"""
Wayback Machine CDX API — free, no key, measures website growth over time.
Compares snapshot size from 12 months ago vs last 3 months to detect trend.
"""
import requests
from datetime import datetime, timedelta

CDX_URL = "http://web.archive.org/cdx/search/cdx"
TIMEOUT  = 15


def _fetch_snapshots(domain: str, from_date: str, to_date: str, limit: int = 5) -> list[dict]:
    try:
        resp = requests.get(
            CDX_URL,
            params={
                "url":        domain,
                "output":     "json",
                "limit":      limit,
                "fl":         "timestamp,length,statuscode",
                "from":       from_date,
                "to":         to_date,
                "filter":     "statuscode:200",
                "collapse":   "timestamp:8",  # one per day max
            },
            timeout=TIMEOUT,
        )
        if resp.status_code != 200 or not resp.text.strip():
            return []
        rows = resp.json()
        if len(rows) <= 1:  # header only
            return []
        results = []
        for row in rows[1:]:  # skip header
            try:
                results.append({
                    "timestamp":  row[0],
                    "size_bytes": int(row[1]) if row[1].isdigit() else 0,
                    "status":     row[2],
                })
            except Exception:
                pass
        return results
    except Exception:
        return []


def get_growth_indicators(domain: str) -> dict:
    """
    Returns a growth trend dict:
      trend        : "growing" | "stable" | "shrinking" | "unknown"
      change_pct   : float
      old_avg_kb   : float  (12-6 months ago)
      new_avg_kb   : float  (last 3 months)
      first_seen   : str    (earliest archive date)
      summary      : str    (human-readable 1-liner)
    """
    now          = datetime.utcnow()
    ago_12m      = (now - timedelta(days=365)).strftime("%Y%m%d")
    ago_6m       = (now - timedelta(days=180)).strftime("%Y%m%d")
    ago_3m       = (now - timedelta(days=90)).strftime("%Y%m%d")
    today        = now.strftime("%Y%m%d")

    old_snaps = _fetch_snapshots(domain, ago_12m, ago_6m, 5)
    new_snaps = _fetch_snapshots(domain, ago_3m,  today,  5)

    # Also try to find the first ever snapshot
    first_seen = None
    try:
        resp = requests.get(
            CDX_URL,
            params={"url": domain, "output": "json", "limit": 2, "fl": "timestamp", "from": "19960101"},
            timeout=TIMEOUT,
        )
        rows = resp.json()
        if len(rows) > 1:
            first_seen = rows[1][0][:8]  # YYYYMMDD
    except Exception:
        pass

    if not old_snaps or not new_snaps:
        return {
            "trend": "unknown", "change_pct": 0,
            "old_avg_kb": 0, "new_avg_kb": 0,
            "first_seen": first_seen,
            "summary": "Insufficient Wayback Machine data for this domain.",
        }

    old_sizes = [s["size_bytes"] for s in old_snaps if s["size_bytes"] > 0]
    new_sizes = [s["size_bytes"] for s in new_snaps if s["size_bytes"] > 0]

    if not old_sizes or not new_sizes:
        return {
            "trend": "unknown", "change_pct": 0,
            "old_avg_kb": 0, "new_avg_kb": 0,
            "first_seen": first_seen,
            "summary": "Page size data unavailable.",
        }

    old_avg = sum(old_sizes) / len(old_sizes)
    new_avg = sum(new_sizes) / len(new_sizes)
    change  = ((new_avg - old_avg) / old_avg) * 100 if old_avg else 0
    change  = round(change, 1)

    if change > 15:
        trend   = "growing"
        summary = f"Site content is growing (+{change}% page size over 6 months) — signals active development or expansion."
    elif change < -15:
        trend   = "shrinking"
        summary = f"Site content is shrinking ({change}% page size over 6 months) — may indicate downsizing or major redesign."
    else:
        trend   = "stable"
        summary = f"Site content is stable ({change:+.1f}% change) — consistent presence, no major overhauls."

    return {
        "trend":       trend,
        "change_pct":  change,
        "old_avg_kb":  round(old_avg / 1024, 1),
        "new_avg_kb":  round(new_avg / 1024, 1),
        "first_seen":  first_seen,
        "summary":     summary,
    }
