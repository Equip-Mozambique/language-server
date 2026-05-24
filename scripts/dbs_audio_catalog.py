"""Scrape DBS audio catalog and inventory by language.

DBS (Digital Bible Society) audio at https://dbs.org/audio — distributes
audio Bible packages assembled from FCBH, Davar, Biblica, BibleLeague, etc.
"""

from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup
from rich import print as rprint
from rich.table import Table

from aiserver.scrape import scrape


PAGES = [
    "https://dbs.org/audio",
    "https://dbs.org/audio/",
    "https://dbs.org/audio/collections",
    "https://dbs.org/en/bibles",
]


def main() -> None:
    out_dir = Path(__file__).resolve().parents[1] / "data" / "research" / "dbs"
    out_dir.mkdir(parents=True, exist_ok=True)

    found_codes: set[str] = set()
    for url in PAGES:
        rprint(f"\n[bold cyan]>>> {url}[/bold cyan]")
        try:
            res = scrape(url)
        except Exception as e:
            rprint(f"  [red]FAIL:[/red] {e}")
            continue
        rprint(f"  tier={res.tier}, bytes={len(res.html)}")

        # Save raw
        fname = url.replace("https://", "").replace("/", "_") + ".html"
        (out_dir / fname).write_text(res.html)

        # Heuristic: DBS Bible codes are 6-char alphanumeric (e.g. SEHWBT, NDCBSZ, VEN98)
        # often appearing as link paths /bibles/SEHWBT or in URLs
        soup = BeautifulSoup(res.html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            m = re.search(r"/([A-Z]{3}[A-Z0-9]{2,5})(?:[/?]|$)", href)
            if m:
                found_codes.add(m.group(1))

    rprint(f"\n[bold]Found {len(found_codes)} DBS Bible codes[/bold]")

    # Group by ISO prefix (first 3 chars)
    by_iso = {}
    for code in sorted(found_codes):
        iso = code[:3].lower()
        by_iso.setdefault(iso, []).append(code)

    t = Table(title="DBS Bible inventory (by ISO prefix)")
    t.add_column("ISO3")
    t.add_column("Codes")
    t.add_column("Target?")

    # Our 19 target ISOs (3-char form where applicable)
    targets = {
        "sna", "nde", "nbl", "nya", "toi", "kck", "nmq", "ven", "tso",
        "por", "vmw", "seh", "ngl", "chw", "ndc", "tsc", "rng", "yao",
    }
    for iso, codes in sorted(by_iso.items()):
        is_target = "★" if iso in targets else ""
        t.add_row(iso, ", ".join(codes), is_target)
    rprint(t)

    # Save inventory JSON
    import json
    inventory = {iso: codes for iso, codes in sorted(by_iso.items())}
    (out_dir / "inventory.json").write_text(json.dumps(inventory, indent=2))
    rprint(f"\n[green]Saved inventory:[/green] {out_dir / 'inventory.json'}")

    # Target-focused report
    rprint("\n[bold cyan]Target language coverage:[/bold cyan]")
    for iso in sorted(targets):
        if iso in by_iso:
            rprint(f"  [green]{iso}:[/green] {', '.join(by_iso[iso])}")
        else:
            rprint(f"  [dim]{iso}: not found[/dim]")


if __name__ == "__main__":
    main()
