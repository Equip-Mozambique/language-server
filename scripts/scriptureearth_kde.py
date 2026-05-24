"""Scrape ScriptureEarth Makonde (kde) page + download NT audio mp3 per book.

ScriptureEarth exposes direct mp3 download URLs for kde — best paired
script+audio in our 19-target set.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from rich import print as rprint
from rich.progress import Progress

from aiserver.scrape import scrape


INDEX_URL = "https://scriptureearth.org/00i-Scripture_Index.php?iso=kde"
OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "audio" / "kde" / "scriptureearth"


def stream_to_file(url: str, dest: Path) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    bytes_written = 0
    with httpx.stream("GET", url, timeout=600.0, follow_redirects=True) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length") or 0)
        with dest.open("wb") as f, Progress() as prog:
            task = prog.add_task(dest.name, total=total or None)
            for chunk in r.iter_bytes(1 << 16):
                f.write(chunk)
                bytes_written += len(chunk)
                prog.update(task, completed=bytes_written)
    return bytes_written


def main() -> None:
    rprint(f"[cyan]Scraping {INDEX_URL}[/cyan]")
    res = scrape(INDEX_URL)
    soup = BeautifulSoup(res.html, "html.parser")

    # ScriptureEarth embeds mp3 paths inside <option value="..."> attributes,
    # not in <a href>. Pattern: `./data/kde/audio/NN_BOOK_CCC.mp3`.
    mp3_paths = set(re.findall(r"\./data/kde/audio/[0-9A-Za-z_]+\.mp3", res.html))
    mp3_links: list[tuple[str, str]] = []
    for path in sorted(mp3_paths):
        abs_url = urljoin("https://scriptureearth.org/", path.lstrip("./"))
        label = Path(path).name
        mp3_links.append((abs_url, label))

    rprint(f"  found {len(mp3_links)} mp3 links")
    for url, label in mp3_links[:10]:
        rprint(f"  - {label[:40]:<40}  {url[:100]}")

    if not mp3_links:
        rprint("[red]no mp3 links found — page structure may have changed[/red]")
        # Dump page for inspection
        debug = Path("/tmp/se_kde.html")
        debug.write_text(res.html)
        rprint(f"  saved page to {debug} for debugging")
        return

    rprint(f"\n[cyan]Downloading {len(mp3_links)} files to {OUT_DIR}[/cyan]")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for url, label in mp3_links:
        fname = re.sub(r"[^a-zA-Z0-9._-]+", "_", label or Path(url).name)
        if not fname.lower().endswith(".mp3"):
            fname += ".mp3"
        dest = OUT_DIR / fname
        if dest.exists():
            rprint(f"  [dim]skip (exists): {fname}[/dim]")
            continue
        try:
            size = stream_to_file(url, dest)
            rprint(f"  [green]{fname}[/green] ({size // 1024} KB)")
        except Exception as e:
            rprint(f"  [red]FAIL {fname}: {e}[/red]")


if __name__ == "__main__":
    main()
