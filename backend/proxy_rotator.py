"""
Proxy pool with Tor-first free rotation.

Auto-launch: if Tor Browser is installed but not running, this module
starts it silently in the background and waits for the SOCKS5 proxy to come up.

Free proxy strategy (no limits, no cost):
  1. Tor SOCKS5 — rotating exit-node IP worldwide, completely free & unlimited
  2. Public proxy lists — fallback when Tor not available

Tor Browser paths searched (in order):
  - Desktop\\Tor Browser\\Browser\\firefox.exe
  - Downloads\\Tor Browser\\Browser\\firefox.exe
  - AppData\\Roaming\\Tor Browser\\Browser\\firefox.exe
  - C:\\Tor Browser\\Browser\\firefox.exe
  - C:\\Program Files\\Tor Browser\\Browser\\firefox.exe
"""
import os
import random
import socket
import subprocess
import threading
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

PROXY_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
]

TEST_URL = "http://httpbin.org/ip"
TEST_TIMEOUT = 6
TOR_PORTS = (9150, 9050)  # 9150 = Tor Browser, 9050 = Tor daemon/expert bundle

TOR_BROWSER_PATHS = [
    os.path.expandvars(r"%USERPROFILE%\Desktop\Tor Browser\Browser\firefox.exe"),
    os.path.expandvars(r"%USERPROFILE%\Downloads\Tor Browser\Browser\firefox.exe"),
    os.path.expandvars(r"%APPDATA%\Tor Browser\Browser\firefox.exe"),
    r"C:\Tor Browser\Browser\firefox.exe",
    r"C:\Program Files\Tor Browser\Browser\firefox.exe",
]


# ── Tor helpers ───────────────────────────────────────────────────────────────

def _tor_port_open(port: int) -> bool:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except Exception:
        return False


def check_tor() -> str | None:
    """Return socks5://127.0.0.1:PORT if Tor is already running, else None."""
    for port in TOR_PORTS:
        if _tor_port_open(port):
            proxy = f"socks5://127.0.0.1:{port}"
            print(f"  [TOR] Active on port {port} -> using {proxy}")
            return proxy
    return None


def find_tor_browser() -> str | None:
    """Return path to Tor Browser's firefox.exe if installed, else None."""
    for p in TOR_BROWSER_PATHS:
        if os.path.isfile(p):
            return p
    return None


def launch_tor_browser(exe_path: str) -> bool:
    """
    Launch Tor Browser minimized/hidden in the background.
    Waits up to 30s for SOCKS5 on port 9150 to appear.
    Returns True when the proxy is ready.
    """
    print(f"  [TOR] Starting Tor Browser silently...")
    try:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0  # SW_HIDE — no visible window
        subprocess.Popen(
            [exe_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            startupinfo=si,
        )
    except Exception as e:
        print(f"  [TOR] Could not launch Tor Browser: {e}")
        return False

    print("  [TOR] Waiting for Tor to connect", end="", flush=True)
    for _ in range(30):
        time.sleep(1)
        print(".", end="", flush=True)
        if _tor_port_open(9150):
            print(" ready!")
            return True
    print(" timed out")
    return False


def rotate_tor_ip(port: int = 9051, password: str = "") -> bool:
    """
    Send NEWNYM to Tor control port to get a new exit node.
    Only works if ControlPort is enabled in torrc.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect(("127.0.0.1", port))
        auth = f'AUTHENTICATE "{password}"\r\n' if password else 'AUTHENTICATE ""\r\n'
        s.sendall(auth.encode())
        s.recv(128)
        s.sendall(b"SIGNAL NEWNYM\r\n")
        resp = s.recv(128).decode()
        s.close()
        return "250 OK" in resp
    except Exception:
        return False


# ── ProxyRotator ──────────────────────────────────────────────────────────────

class ProxyRotator:
    def __init__(self):
        self._pool: list[str] = []
        self._lock = threading.Lock()
        self._tor_proxy: str | None = None

    def load(self, max_to_test: int = 150, workers: int = 30) -> int:
        # 1. Check if Tor already running
        tor = check_tor()

        # 2. Not running — try to auto-launch Tor Browser
        if not tor:
            exe = find_tor_browser()
            if exe:
                print(f"  [TOR] Found Tor Browser at: {exe}")
                launched = launch_tor_browser(exe)
                if launched:
                    tor = "socks5://127.0.0.1:9150"
                    print(f"  [TOR] Ready: {tor}")
                else:
                    print("  [TOR] Tor did not come up in time — falling back to public proxies")
            else:
                print("  [TOR] Tor Browser not found on this machine")

        if tor:
            self._tor_proxy = tor
            with self._lock:
                self._pool = [tor]
            print("  [PROXY] Using Tor (free, unlimited IP rotation)")
            return 1

        # 3. No Tor — fall back to public proxy lists
        raw = self._fetch_lists(max_to_test)
        print(f"  [PROXY] Testing {len(raw)} public proxies ({workers} workers)...")
        working = []
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(self._test, p): p for p in raw}
            for fut in as_completed(futures):
                result = fut.result()
                if result:
                    working.append(result)

        with self._lock:
            self._pool = working
        print(f"  [PROXY] {len(working)} working proxies ready")
        return len(working)

    def get(self) -> str | None:
        with self._lock:
            if not self._pool:
                return None
            proxy = random.choice(self._pool)

        # If using Tor, try requesting a new exit node between requests
        if proxy and "socks5://127.0.0.1" in proxy:
            rotate_tor_ip()

        return proxy

    def remove(self, proxy: str):
        with self._lock:
            try:
                self._pool.remove(proxy)
            except ValueError:
                pass

    def count(self) -> int:
        with self._lock:
            return len(self._pool)

    def is_using_tor(self) -> bool:
        return self._tor_proxy is not None

    # ── Internals ─────────────────────────────────────────────────────────────

    def _fetch_lists(self, limit: int) -> list[str]:
        raw = []
        for src in PROXY_SOURCES:
            try:
                resp = requests.get(src, timeout=10)
                if resp.status_code == 200:
                    lines = [l.strip() for l in resp.text.splitlines() if l.strip()]
                    raw.extend(lines)
            except Exception:
                pass
        random.shuffle(raw)
        return raw[:limit]

    def _test(self, proxy: str) -> str | None:
        fmt = f"http://{proxy}" if not proxy.startswith(("http", "socks")) else proxy
        try:
            resp = requests.get(
                TEST_URL,
                proxies={"http": fmt, "https": fmt},
                timeout=TEST_TIMEOUT,
            )
            if resp.status_code == 200:
                return fmt
        except Exception:
            pass
        return None
