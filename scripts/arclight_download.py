"""Download Jesus Film mp4 for a target ISO via Arclight.

Pulls 720p (or best available) mp4 from mux.com for a given film + language.
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import typer
from rich import print as rprint
from rich.progress import Progress

from aiserver import arclight

DATA_ROOT = Path(__file__).resolve().parents[1] / "data" / "video"
SUMMARY = Path(__file__).resolve().parents[1] / "data" / "research" / "arclight" / "summary.json"


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


def download_film(
    iso: str,
    language_id: int | None = None,
    component_id: str = "1_jf-0-0",
    quality_pref: list[str] | None = None,
) -> Path | None:
    quality_pref = quality_pref or ["720p", "270p", "stream_m3u8"]

    if language_id is None and SUMMARY.exists():
        summary = json.loads(SUMMARY.read_text())
        match = next((s for s in summary if s["iso"] == iso), None)
        if match:
            language_id = match["language_id"]
    if language_id is None:
        rprint(f"[red]Need --language-id for {iso}[/red]")
        return None

    rprint(f"[cyan]Fetching URLs for {component_id} / langId {language_id}[/cyan]")
    urls = arclight.video_urls(component_id, language_id)
    rprint(f"  available: {sorted(urls.keys())}")
    if not urls:
        rprint(f"  [red]no URLs returned[/red]")
        return None

    # Pick best mp4 (skip HLS for now — needs ffmpeg pipeline)
    chosen_key = None
    chosen_url = None
    for pref in quality_pref:
        for k, v in urls.items():
            if pref in k and v.endswith(".mp4"):
                chosen_key, chosen_url = k, v
                break
        if chosen_url:
            break
    if not chosen_url:
        # Fallback: just take first .mp4
        for k, v in urls.items():
            if v.endswith(".mp4"):
                chosen_key, chosen_url = k, v
                break
    if not chosen_url:
        rprint(f"  [red]no mp4 url found[/red]")
        return None

    rprint(f"  picked: {chosen_key} -> {chosen_url}")
    out_dir = DATA_ROOT / iso / "arclight"
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_id = component_id.replace("/", "_")
    dest = out_dir / f"{safe_id}_{chosen_key}.mp4"

    if dest.exists():
        rprint(f"  [dim]exists ({dest.stat().st_size // 1024}K) — skipping[/dim]")
        return dest

    size = stream_to_file(chosen_url, dest)
    rprint(f"  [green]Wrote {dest} ({size // (1024 * 1024)} MB)[/green]")
    return dest


def cli(
    iso: str,
    language_id: int | None = typer.Option(None, "--language-id"),
    component_id: str = typer.Option("1_jf-0-0", "--component-id", help="1_jf-0-0=JESUS Film, 1_mld-0-0=Magdalena, 1_cl-0-0=StoryOfJesusForChildren"),
) -> None:
    download_film(iso, language_id, component_id)


if __name__ == "__main__":
    typer.run(cli)
