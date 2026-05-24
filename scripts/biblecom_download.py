"""Download Bible.com NT text per target ISO; pair with existing DBP audio manifests.

Strategy:
- For each target lang, find best available version on Bible.com
- Scrape full NT (260 chapters → ~7,957 verses)
- Save as data/text/<iso>/<version_abbr>/manifest.json mapping (book, chapter) -> verses
- Optionally update data/audio/<iso>/<fileset>/manifest.json with text field
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich import print as rprint
from rich.progress import Progress

from aiserver import biblecom
from aiserver.languages import LANGS

DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
TEXT_ROOT = DATA_ROOT / "text"


def best_version(versions: list[biblecom.Version], prefer_publishers: list[str] | None = None) -> biblecom.Version | None:
    """Heuristic pick: prefer named publishers (Bible Society > Biblica > others)."""
    if not versions:
        return None
    prefer_publishers = prefer_publishers or ["Bible Society", "Biblica", "Wycliffe"]
    for pub_kw in prefer_publishers:
        for v in versions:
            if v.publisher and pub_kw.lower() in v.publisher.lower():
                return v
    return versions[0]


def discover(iso: str) -> None:
    """List versions available for an ISO."""
    versions = biblecom.list_versions(iso)
    rprint(f"[cyan]{iso}:[/cyan] {len(versions)} version(s)")
    for v in versions:
        rprint(f"  id={v.id:<6} abbr={v.abbr:<10} local={v.local_abbr:<10} pub={v.publisher} | {v.local_title[:60]}")


def download(
    iso: str,
    version_id: int | None = None,
    local_abbr: str | None = None,
    out_dir: Path | None = None,
) -> Path | None:
    if iso not in LANGS:
        rprint(f"[red]Unknown iso: {iso}[/red]")
        return None

    if version_id is None or local_abbr is None:
        versions = biblecom.list_versions(iso)
        if not versions:
            rprint(f"[red]{iso}: no versions on bible.com[/red]")
            return None
        v = best_version(versions)
        version_id = v.id
        local_abbr = v.local_abbr
        rprint(f"[cyan]Picked:[/cyan] id={version_id} {v.local_abbr} ({v.publisher}) — {v.local_title[:60]}")

    target_dir = (out_dir or TEXT_ROOT) / iso / local_abbr
    target_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = target_dir / "nt_manifest.json"

    if manifest_path.exists():
        rprint(f"  [dim]exists — {manifest_path}[/dim]")
        return manifest_path

    manifest: dict = {
        "iso": iso,
        "version_id": version_id,
        "local_abbr": local_abbr,
        "chapters": {},
    }

    with Progress() as prog:
        task = prog.add_task(f"{iso} NT", total=260)

        def cb(i: int, book: str, chap: int, status: str):
            prog.update(task, completed=i + 1, description=f"{iso} {book} {chap}: {status[:25]}")

        chapters = biblecom.fetch_nt(version_id, local_abbr, progress_cb=cb)

    for (book, chap), verses in chapters.items():
        key = f"{book}_{chap:03d}"
        manifest["chapters"][key] = [
            {"verse": v.verse, "text": v.text} for v in verses
        ]

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    total_verses = sum(len(v) for v in manifest["chapters"].values())
    rprint(f"[green]Wrote {manifest_path}[/green] — {total_verses} verses across 260 chapters")
    return manifest_path


app = typer.Typer()


@app.command()
def discover_cmd(iso: str) -> None:
    """List Bible.com versions for an ISO."""
    discover(iso)


@app.command()
def download_cmd(
    iso: str,
    version_id: int | None = typer.Option(None, "--version-id"),
    local_abbr: str | None = typer.Option(None, "--abbr"),
) -> None:
    """Download NT text for a target language."""
    download(iso, version_id, local_abbr)


@app.command()
def bulk() -> None:
    """Download NT for all target ISOs that have at least one bible.com version."""
    for iso in LANGS:
        rprint(f"\n[bold cyan]>>> {iso}[/bold cyan]")
        try:
            download(iso)
        except Exception as e:
            rprint(f"  [red]FAIL: {e}[/red]")


if __name__ == "__main__":
    app()
