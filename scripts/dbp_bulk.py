"""Bulk DBP downloader for all DBP-covered target languages.

Sequential per-language. Skip langs already downloaded (manifest.json exists).
"""

from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich import print as rprint

from dbp_download import download  # type: ignore[import-not-found]

# Empirically confirmed DBP audio coverage (from dbp_summary.py scan 2026-05-23)
COVERED = [
    "sna", "nde", "nya", "toi", "kck", "tso", "por", "vmw",
    "seh", "ngl", "ndc", "tsc", "rng", "yao",
]

DATA_ROOT = Path(__file__).resolve().parents[1] / "data" / "audio"


def already_downloaded(iso: str) -> bool:
    iso_dir = DATA_ROOT / iso
    if not iso_dir.exists():
        return False
    for sub in iso_dir.iterdir():
        if (sub / "manifest.json").exists():
            return True
    return False


def main() -> None:
    rprint(f"[bold cyan]Bulk DBP download — {len(COVERED)} languages[/bold cyan]\n")
    results = []
    for iso in COVERED:
        rprint(f"\n[bold yellow]>>> {iso}[/bold yellow]")
        if already_downloaded(iso):
            rprint(f"  [dim]skip — already downloaded[/dim]")
            results.append((iso, "skipped", 0))
            continue
        t0 = time.time()
        try:
            download(iso, None, None)
            dt = time.time() - t0
            results.append((iso, "ok", dt))
        except SystemExit:
            results.append((iso, "no-audio", 0))
        except Exception as e:
            rprint(f"  [red]FAIL:[/red] {e}")
            traceback.print_exc()
            results.append((iso, "fail", time.time() - t0))

    rprint("\n[bold cyan]Summary[/bold cyan]")
    for iso, status, dt in results:
        rprint(f"  {iso}: {status} ({dt:.1f}s)")


if __name__ == "__main__":
    # Make `scripts.dbp_download` importable
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    main()
