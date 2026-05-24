"""Authenticated progress.bible fetcher using browser-exported cookies.

Cookies are read from env vars (NOT hardcoded):
  PB_WP_COOKIE_NAME    — e.g. wordpress_logged_in_d4e901ddfad1e47b474958eccc4b38bc
  PB_WP_COOKIE_VALUE   — the wordpress_logged_in_* value
  PB_CF_CLEARANCE      — cf_clearance value (optional but helps Cloudflare)

URL pattern observed: data is served as PNG images at
  /products/data/<CC>/<ID>/<PAGE>.png

Mission: find index of all <CC>/<ID> pairs + filter for our 19 target ISOs.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup
from curl_cffi import requests as cc_requests
from rich import print as rprint


OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "research" / "progress_bible"
SEED_PAGES = [
    "https://progress.bible/products/data/",
    "https://progress.bible/products/",
    "https://progress.bible/",
]


def session_with_cookies() -> cc_requests.Session:
    name = os.environ.get("PB_WP_COOKIE_NAME")
    value = os.environ.get("PB_WP_COOKIE_VALUE")
    cf = os.environ.get("PB_CF_CLEARANCE")
    if not name or not value:
        rprint("[red]Set PB_WP_COOKIE_NAME + PB_WP_COOKIE_VALUE[/red]")
        sys.exit(1)

    s = cc_requests.Session(impersonate="chrome120")
    s.cookies.set(name, value, domain="progress.bible", path="/")
    if cf:
        s.cookies.set("cf_clearance", cf, domain="progress.bible", path="/")
    return s


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    s = session_with_cookies()

    rprint("[cyan]Fetching authenticated data pages...[/cyan]")
    pages: dict[str, str] = {}
    for url in SEED_PAGES:
        r = s.get(url, timeout=30)
        rprint(f"  {url} -> {r.status_code} ({len(r.text)} bytes)")
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", url.replace("https://", "")) + ".html"
        (OUT_DIR / slug).write_text(r.text)
        pages[url] = r.text

    # Check we're actually authed: look for "Log out" / username / dashboard markers
    home = pages.get("https://progress.bible/products/data/", "")
    soup = BeautifulSoup(home, "html.parser")
    indicators = ["log out", "logout", "my account", "dashboard", "welcome"]
    found = [i for i in indicators if i in home.lower()]
    rprint(f"\n[bold]auth indicators present:[/bold] {found}")

    # Look for /products/data/<CC>/<ID>/ URLs everywhere
    rprint("\n[cyan]Searching for data URLs...[/cyan]")
    pattern = re.compile(r"/products/data/([A-Z]{1,3})/([A-Z0-9]{6,15})/")
    all_data_urls: set[tuple[str, str]] = set()
    for url, html in pages.items():
        for m in pattern.finditer(html):
            all_data_urls.add((m.group(1), m.group(2)))

    rprint(f"  found {len(all_data_urls)} unique (CC, ID) pairs in initial pages")

    # Also extract every link from auth'd dashboard to discover more sub-pages
    rprint("\n[cyan]Following all dashboard links to find more data IDs...[/cyan]")
    visited = set()
    todo = []
    for url, html in pages.items():
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "progress.bible" in href and href not in visited:
                if any(s in href for s in ("/data", "/products", "/languages", "/countries", "/dashboard")):
                    todo.append(href)

    todo = list(set(todo))[:30]  # cap exploration
    rprint(f"  queued {len(todo)} URLs to crawl")

    for href in todo:
        if href in visited:
            continue
        visited.add(href)
        try:
            r = s.get(href, timeout=30)
            if r.status_code != 200:
                continue
            for m in pattern.finditer(r.text):
                all_data_urls.add((m.group(1), m.group(2)))
        except Exception as e:
            rprint(f"  [yellow]skip {href}: {e}[/yellow]")

    rprint(f"\n[bold]Total unique data IDs found: {len(all_data_urls)}[/bold]")
    for cc, did in sorted(all_data_urls)[:30]:
        rprint(f"  {cc}/{did}")

    # Save
    import json
    (OUT_DIR / "data_index.json").write_text(json.dumps(sorted(all_data_urls), indent=2))
    rprint(f"\nSaved index -> {OUT_DIR / 'data_index.json'}")

    # Sample fetch — grab page 1 of first data ID
    if all_data_urls:
        cc, did = next(iter(sorted(all_data_urls)))
        sample_url = f"https://progress.bible/products/data/{cc}/{did}/1.png"
        rprint(f"\n[cyan]Sample image fetch: {sample_url}[/cyan]")
        r = s.get(sample_url, timeout=30, headers={"Referer": "https://progress.bible/products/data/"})
        rprint(f"  -> {r.status_code} ({len(r.content)} bytes, content-type={r.headers.get('Content-Type')})")
        if r.status_code == 200 and "image" in (r.headers.get("Content-Type") or ""):
            sample_path = OUT_DIR / f"sample_{cc}_{did}_1.png"
            sample_path.write_bytes(r.content)
            rprint(f"  saved -> {sample_path}")


if __name__ == "__main__":
    main()
