"""Bulk download JESUS Film (and optional Magdalena / SoJC) for all 19 target ISOs.

Reads `data/research/arclight/summary.json` for languageIds.
Defaults to JESUS Film only (1_jf-0-0).
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from rich import print as rprint

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arclight_download import download_film  # type: ignore

SUMMARY = Path(__file__).resolve().parents[1] / "data" / "research" / "arclight" / "summary.json"

# Films to fetch per lang (in order). 1_jf-0-0 = JESUS Film
# Add 1_mld-0-0 (Magdalena) and 1_cl-0-0 (StoryOfJesusForChildren) if you want more
FILMS = ["1_jf-0-0"]


def main() -> None:
    if not SUMMARY.exists():
        rprint(f"[red]No summary file at {SUMMARY} — run arclight_discover.py first[/red]")
        sys.exit(1)
    summary = json.loads(SUMMARY.read_text())

    rprint(f"[bold cyan]Bulk Arclight download — {len(summary)} ISOs × {len(FILMS)} films[/bold cyan]\n")
    results: list[tuple[str, str, str]] = []
    for entry in summary:
        iso = entry["iso"]
        lang_id = entry["language_id"]
        for film in FILMS:
            rprint(f"\n[yellow]>>> {iso} ({lang_id}) — {film}[/yellow]")
            t0 = time.time()
            try:
                dest = download_film(iso, lang_id, film)
                dt = time.time() - t0
                if dest:
                    results.append((iso, film, f"ok ({dt:.0f}s)"))
                else:
                    results.append((iso, film, "no-mp4"))
            except Exception as e:
                rprint(f"  [red]FAIL: {e}[/red]")
                results.append((iso, film, f"fail: {e}"))

    rprint("\n[bold cyan]Summary[/bold cyan]")
    for iso, film, status in results:
        rprint(f"  {iso} {film}: {status}")


if __name__ == "__main__":
    main()
