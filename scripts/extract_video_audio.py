"""Extract mp3 audio from downloaded video files (mainly JESUS Film mp4s).

Reads from `data/video/<iso>/<source>/*.mp4`, writes to
`data/audio/<iso>/jesus_film/<basename>.mp3`. After running, the standard
corpus scanner (`_scan_corpus`) picks up these new audio files automatically
and ASR/TTS readiness scores update.

Requires `ffmpeg` on PATH.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from rich import print as rprint
from rich.progress import Progress


DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
VIDEO_ROOT = DATA_ROOT / "video"
AUDIO_ROOT = DATA_ROOT / "audio"


def extract_one(src_mp4: Path, dest_mp3: Path) -> tuple[bool, str]:
    """Run ffmpeg to extract a mono 22050 Hz mp3 from src_mp4."""
    if dest_mp3.exists() and dest_mp3.stat().st_size > 0:
        return True, "skip (exists)"
    dest_mp3.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(src_mp4),
        "-vn",                  # no video
        "-ac", "1",             # mono
        "-ar", "22050",         # 22.05 kHz (good for ASR; ffwd-compatible w/ Whisper/MMS)
        "-b:a", "64k",          # 64 kbps mp3 (FCBH-comparable)
        "-f", "mp3",
        str(dest_mp3),
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except Exception as e:
        return False, f"exception: {e}"
    if r.returncode != 0:
        return False, f"ffmpeg exit {r.returncode}: {r.stderr[:200]}"
    return True, "ok"


def main() -> None:
    if not shutil.which("ffmpeg"):
        rprint("[red]ffmpeg not found on PATH; install it (`apt install ffmpeg`)[/red]")
        return
    if not VIDEO_ROOT.exists():
        rprint(f"[yellow]No video dir at {VIDEO_ROOT}[/yellow]")
        return

    targets: list[tuple[Path, Path]] = []
    for iso_dir in sorted(VIDEO_ROOT.iterdir()):
        if not iso_dir.is_dir():
            continue
        iso = iso_dir.name
        for source_dir in iso_dir.iterdir():
            if not source_dir.is_dir():
                continue
            source = source_dir.name  # e.g. "arclight"
            for mp4 in sorted(source_dir.glob("*.mp4")):
                dest_name = mp4.stem + ".mp3"
                dest = AUDIO_ROOT / iso / f"jesus_film_{source}" / dest_name
                targets.append((mp4, dest))

    rprint(f"[cyan]Extracting {len(targets)} videos -> mp3[/cyan]")
    ok = 0
    fail = 0
    with Progress() as prog:
        task = prog.add_task("extract", total=len(targets))
        for src, dest in targets:
            ok_flag, msg = extract_one(src, dest)
            if ok_flag:
                ok += 1
            else:
                fail += 1
                rprint(f"  [red]FAIL {src.name}: {msg}[/red]")
            prog.advance(task)

    rprint(f"[green]Done.[/green] ok={ok} fail={fail}")
    rprint(f"Audio written under {AUDIO_ROOT}/<iso>/jesus_film_<source>/")


if __name__ == "__main__":
    main()
