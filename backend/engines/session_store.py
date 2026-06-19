"""
Cookie persistence per domain.
Saves curl_cffi session cookies to disk so repeat visits
don't cold-start and bypass "new session" bot signals.
"""
import json
import os
from pathlib import Path
from urllib.parse import urlparse

_STORE = Path(__file__).parent.parent / "sessions"


def _key(url: str) -> str:
    return urlparse(url).netloc.replace(".", "_").replace(":", "_")


def load(url: str) -> dict:
    _STORE.mkdir(exist_ok=True)
    f = _STORE / f"{_key(url)}.json"
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save(url: str, cookies: dict):
    _STORE.mkdir(exist_ok=True)
    f = _STORE / f"{_key(url)}.json"
    try:
        f.write_text(json.dumps(cookies, indent=2), encoding="utf-8")
    except Exception:
        pass
