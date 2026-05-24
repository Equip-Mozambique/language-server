"""Authenticated fetch from progress.bible (WordPress login + nonce).

Reads credentials from env vars (NOT hardcoded):
  PROGRESS_BIBLE_USER
  PROGRESS_BIBLE_PASS

Usage:
  PROGRESS_BIBLE_USER=... PROGRESS_BIBLE_PASS=... \\
      python scripts/progress_bible_fetch.py
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup
from curl_cffi import requests as cc_requests
from rich import print as rprint


LOGIN_URL = "https://progress.bible/login/"
WP_LOGIN_POST = "https://progress.bible/wp-login.php?wpe-login=true"
DATA_PAGES = [
    "https://progress.bible/products/data/",
    "https://progress.bible/data/",
    "https://progress.bible/products/",
]

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "research" / "progress_bible"


def session() -> cc_requests.Session:
    s = cc_requests.Session(impersonate="chrome120")
    return s


def get_nonce(s: cc_requests.Session) -> tuple[str, str]:
    r = s.get(LOGIN_URL, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    nonce_field = soup.find("input", attrs={"name": "pp-lf-login-nonce"})
    if not nonce_field:
        raise RuntimeError("could not find login nonce")
    referer_field = soup.find("input", attrs={"name": "_wp_http_referer"})
    return nonce_field["value"], (referer_field or {}).get("value", "/login/")


def login(s: cc_requests.Session, user: str, pwd: str) -> None:
    nonce, referer = get_nonce(s)
    rprint(f"  [dim]nonce={nonce}, referer={referer}[/dim]")
    payload = {
        "pp-lf-login-nonce": nonce,
        "_wp_http_referer": referer,
        "redirect_to": "https://progress.bible/",
        "log": user,
        "pwd": pwd,
        "rememberme": "forever",
        "wp-submit": "Log In",
    }
    # First, POST without auto-redirect to see what server replies
    r_noredir = s.post(
        WP_LOGIN_POST,
        data=payload,
        headers={"Referer": LOGIN_URL},
        timeout=30,
        allow_redirects=False,
    )
    rprint(f"  [dim]POST direct -> {r_noredir.status_code}  Location={r_noredir.headers.get('Location')}[/dim]")

    # Inspect response body for error / success markers
    snippet = r_noredir.text[:1500].replace("\n", " ")
    rprint(f"  [dim]body snippet: {snippet[:300]}...[/dim]")

    # Now follow redirects to land at final URL
    r = s.post(
        WP_LOGIN_POST,
        data=payload,
        headers={"Referer": LOGIN_URL},
        timeout=30,
        allow_redirects=True,
    )
    rprint(f"  [dim]POST followed -> {r.status_code} {r.url}[/dim]")

    cookies = list(s.cookies.keys())
    auth_cookies = [c for c in cookies if c.startswith("wordpress_logged_in") or c.startswith("wp_")]
    rprint(f"  cookies: {len(cookies)} total: {cookies}")
    rprint(f"  auth-looking: {auth_cookies}")

    # Search for error / success markers in followed response
    from bs4 import BeautifulSoup as BS
    soup = BS(r.text, "html.parser")
    errs = soup.find_all(class_=lambda c: c and any(k in c.lower() for k in ("error", "alert", "danger", "notice")))
    for e in errs[:5]:
        txt = e.get_text(strip=True)[:200]
        if txt:
            rprint(f"  [yellow]marker:[/yellow] {txt}")

    if not auth_cookies:
        rprint("  [red]LOGIN FAILED — no wordpress_logged_in cookie[/red]")


def fetch_pages(s: cc_requests.Session) -> dict[str, str]:
    out = {}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for url in DATA_PAGES:
        rprint(f"  fetching {url}")
        r = s.get(url, timeout=30)
        rprint(f"    -> {r.status_code} ({len(r.text)} bytes)")
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", url.replace("https://", "")) + ".html"
        path = OUT_DIR / slug
        path.write_text(r.text)
        out[url] = r.text
    return out


def main() -> None:
    user = os.environ.get("PROGRESS_BIBLE_USER")
    pwd = os.environ.get("PROGRESS_BIBLE_PASS")
    if not user or not pwd:
        rprint("[red]Set PROGRESS_BIBLE_USER + PROGRESS_BIBLE_PASS env vars[/red]")
        sys.exit(1)

    s = session()
    rprint("[cyan]Login...[/cyan]")
    login(s, user, pwd)

    rprint("\n[cyan]Fetching data pages...[/cyan]")
    pages = fetch_pages(s)

    rprint("\n[cyan]Crawling outbound + sub-pages on data dashboard...[/cyan]")
    # Find data table / CSV / download links on data page
    dashboard_html = pages.get("https://progress.bible/products/data/", "")
    if dashboard_html:
        soup = BeautifulSoup(dashboard_html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if re.search(r"\.(csv|xlsx|json|zip|pdf)$", href, re.I) or "data" in href.lower():
                rprint(f"    candidate: {a.get_text(strip=True)[:50]} -> {href[:100]}")

    rprint(f"\n[green]Saved pages to:[/green] {OUT_DIR}")


if __name__ == "__main__":
    main()
