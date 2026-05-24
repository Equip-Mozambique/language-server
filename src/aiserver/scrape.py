"""Tiered web scraper with auto-fallback for Cloudflare/WAF-blocked sites.

Tiers tried in order until one returns a 200:
  1. Plain httpx (in case site isn't actually blocked)
  2. curl_cffi with Chrome120 TLS/JA3 impersonation
  3. FlareSolverr proxy (if running at FLARESOLVERR_URL, default localhost:8191)
  4. Wayback Machine API — fetch latest snapshot
  5. archive.today (archive.ph) — independent snapshot

Each tier returns (status, html, tier_used) or raises on total failure.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Callable

import httpx

DEFAULT_TIMEOUT = 30.0
FLARESOLVERR_URL = os.getenv("FLARESOLVERR_URL", "http://localhost:8191/v1")

UA_CHROME = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
ACCEPT_HEADERS = {
    "User-Agent": UA_CHROME,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,pt;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}


@dataclass
class ScrapeResult:
    url: str
    status: int
    html: str
    tier: str
    elapsed_s: float


class ScrapeError(Exception):
    pass


def _tier_httpx(url: str) -> ScrapeResult:
    t0 = time.time()
    with httpx.Client(
        headers=ACCEPT_HEADERS, follow_redirects=True, timeout=DEFAULT_TIMEOUT, http2=True
    ) as c:
        r = c.get(url)
    if r.status_code >= 400:
        raise ScrapeError(f"httpx returned {r.status_code}")
    return ScrapeResult(url, r.status_code, r.text, "httpx", time.time() - t0)


def _tier_curl_cffi(url: str) -> ScrapeResult:
    from curl_cffi import requests  # local import; optional dep

    t0 = time.time()
    r = requests.get(url, impersonate="chrome120", timeout=DEFAULT_TIMEOUT, headers=ACCEPT_HEADERS)
    if r.status_code >= 400:
        raise ScrapeError(f"curl_cffi returned {r.status_code}")
    return ScrapeResult(url, r.status_code, r.text, "curl_cffi", time.time() - t0)


def _tier_flaresolverr(url: str) -> ScrapeResult:
    t0 = time.time()
    with httpx.Client(timeout=120.0) as c:
        try:
            r = c.post(FLARESOLVERR_URL, json={
                "cmd": "request.get",
                "url": url,
                "maxTimeout": 60_000,
            })
        except httpx.ConnectError as e:
            raise ScrapeError(f"FlareSolverr unreachable at {FLARESOLVERR_URL}: {e}") from e
    if r.status_code != 200:
        raise ScrapeError(f"FlareSolverr meta-status {r.status_code}")
    data = r.json()
    if data.get("status") != "ok":
        raise ScrapeError(f"FlareSolverr status: {data.get('status')} {data.get('message')}")
    sol = data["solution"]
    return ScrapeResult(
        url, sol.get("status", 200), sol.get("response", ""), "flaresolverr",
        time.time() - t0,
    )


def _tier_wayback(url: str) -> ScrapeResult:
    t0 = time.time()
    with httpx.Client(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as c:
        meta = c.get(
            "https://archive.org/wayback/available",
            params={"url": url},
            headers={"User-Agent": UA_CHROME},
        )
        meta.raise_for_status()
        snap = meta.json().get("archived_snapshots", {}).get("closest")
        if not snap or not snap.get("available"):
            raise ScrapeError("no Wayback snapshot available")
        snap_url = snap["url"]
        # Use id_ flag to get raw original page, not Wayback-wrapped chrome
        snap_url_raw = snap_url.replace("/http", "id_/http", 1)
        r = c.get(snap_url_raw, headers={"User-Agent": UA_CHROME})
    if r.status_code >= 400:
        raise ScrapeError(f"Wayback fetch returned {r.status_code}")
    return ScrapeResult(url, r.status_code, r.text, f"wayback:{snap['timestamp']}", time.time() - t0)


def _tier_archive_today(url: str) -> ScrapeResult:
    t0 = time.time()
    # archive.today's "newest" endpoint
    snap_url = f"https://archive.ph/newest/{url}"
    with httpx.Client(
        headers={"User-Agent": UA_CHROME}, follow_redirects=True, timeout=DEFAULT_TIMEOUT
    ) as c:
        r = c.get(snap_url)
    if r.status_code >= 400:
        raise ScrapeError(f"archive.today returned {r.status_code}")
    return ScrapeResult(url, r.status_code, r.text, "archive.today", time.time() - t0)


TIERS: list[tuple[str, Callable[[str], ScrapeResult]]] = [
    ("httpx", _tier_httpx),
    ("curl_cffi", _tier_curl_cffi),
    ("flaresolverr", _tier_flaresolverr),
    ("wayback", _tier_wayback),
    ("archive.today", _tier_archive_today),
]


def scrape(url: str, *, only: list[str] | None = None, skip: list[str] | None = None) -> ScrapeResult:
    """Try tiers in order until one succeeds."""
    errors: list[tuple[str, str]] = []
    for name, fn in TIERS:
        if only and name not in only:
            continue
        if skip and name in skip:
            continue
        try:
            return fn(url)
        except Exception as e:
            errors.append((name, str(e)[:200]))
            continue
    msg = " | ".join(f"{n}: {e}" for n, e in errors)
    raise ScrapeError(f"all tiers failed for {url}: {msg}")


def extract_links(html: str, base_url: str) -> list[str]:
    """Pull all <a href> URLs from HTML, resolved against base_url."""
    from urllib.parse import urljoin, urlparse

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    for a in soup.find_all("a", href=True):
        u = urljoin(base_url, a["href"])
        p = urlparse(u)
        if p.scheme in ("http", "https"):
            urls.append(u)
    return urls


def extract_text(html: str) -> str:
    """Plain text extraction (drops scripts/styles)."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)
