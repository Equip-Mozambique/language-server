"""Extract audio files referenced by an ASR manifest to local disk.

Recipe step 3 helper. Reads data/manifests/<ISO>_asr.jsonl, extracts audio for
each row from its source location (tar.xz for afrivoice, parquet for waxal) to
the absolute audio_path written in the manifest.

Idempotent — skips files already on disk.

Usage:
    python scripts/extract_asr_audio.py <ISO> [--source afrivoice|waxal|all]
"""

from __future__ import annotations

import io
import json
import tarfile
from collections import defaultdict
from pathlib import Path

import typer
from rich import print as rprint
from rich.progress import Progress

DATA_ROOT = Path(__file__).resolve().parents[1] / "data"


def extract_afrivoice(rows: list[dict], iso: str) -> None:
    """Extract from ~/.cache/huggingface/.../Shona/audio_shards/audio_N.tar.xz."""
    rows = [r for r in rows if r["source"] == "afrivoice"]
    if not rows:
        return
    rprint(f"[cyan]afrivoice: {len(rows)} files needed[/cyan]")

    from huggingface_hub import snapshot_download
    snap = Path(snapshot_download(
        repo_id="DigitalUmuganda/AfriVoice", repo_type="dataset",
        allow_patterns=["README.md"],   # snapshot points to cache dir; we just want path
    ))
    # snap might be README only; we want the snapshot dir
    snap_dir = snap.parent if snap.is_file() else snap
    # Find canonical Shona shards dir
    base = snap_dir / "Shona" / "audio_shards"
    if not base.exists():
        # Fall back: find via cache scan
        for p in (Path.home() / ".cache" / "huggingface" / "hub").rglob("Shona/audio_shards"):
            base = p
            break
    rprint(f"  shard dir: {base}")

    # Group rows by shard_id
    by_shard: dict[int, list[dict]] = defaultdict(list)
    for r in rows:
        by_shard[int(r["shard_id"])].append(r)

    # Skip already-extracted
    todo = 0
    for sid, group in by_shard.items():
        for r in group:
            if not Path(r["audio_path"]).exists():
                todo += 1
    rprint(f"  to extract: {todo} (skip already-on-disk)")
    if todo == 0:
        return

    wavs_dir = DATA_ROOT / "audio" / iso / "afrivoice" / "wavs"
    wavs_dir.mkdir(parents=True, exist_ok=True)

    # Strategy: tar with --files-from filter — extract only wanted clips.
    # Spends xz decode on every shard once but writes only needed wavs.
    shards_present = sorted(by_shard.keys())
    rprint(f"  shards: {len(shards_present)}")

    import subprocess
    import tempfile
    with Progress() as prog:
        task = prog.add_task("afrivoice", total=todo)
        done = sum(1 for r in rows if Path(r["audio_path"]).exists())
        prog.update(task, completed=done)
        for sid in shards_present:
            tar_path = base / f"audio_{sid}.tar.xz"
            if not tar_path.exists():
                rprint(f"[yellow]missing {tar_path}[/yellow]")
                continue
            remaining = [r for r in by_shard[sid] if not Path(r["audio_path"]).exists()]
            if not remaining:
                continue
            # Pass wanted basenames via --files-from (deduped)
            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as fh:
                wanted_names = sorted({r["audio_filename"] for r in remaining})
                fh.write("\n".join(wanted_names))
                files_from = fh.name
            try:
                subprocess.run(
                    ["tar", "-xJf", str(tar_path), "-C", str(wavs_dir),
                     "--files-from", files_from, "--ignore-failed-read"],
                    check=True, capture_output=True,
                )
            except subprocess.CalledProcessError as e:
                rprint(f"[red]tar extract failed for shard {sid}: {e.stderr.decode()[:300]}[/red]")
                continue
            finally:
                Path(files_from).unlink(missing_ok=True)
            done = sum(1 for r in rows if Path(r["audio_path"]).exists())
            prog.update(task, completed=done)
            rprint(f"  shard {sid}: {len(wanted_names)} wanted, total on-disk={done}")
    rprint(f"[green]afrivoice on-disk: {done} of {len(rows)} needed[/green]")


def extract_waxal(rows: list[dict], iso: str) -> None:
    """Extract audio bytes from waxal parquet rows."""
    import pyarrow.parquet as pq
    from huggingface_hub import hf_hub_download

    rows = [r for r in rows if r["source"] == "waxal"]
    if not rows:
        return
    rprint(f"[cyan]waxal: {len(rows)} files needed[/cyan]")

    todo = [r for r in rows if not Path(r["audio_path"]).exists()]
    rprint(f"  to extract: {len(todo)} (skip already-on-disk)")
    if not todo:
        return

    wavs_dir = DATA_ROOT / "audio" / iso / "waxal" / "wavs"
    wavs_dir.mkdir(parents=True, exist_ok=True)

    by_shard: dict[str, list[dict]] = defaultdict(list)
    for r in todo:
        by_shard[r["parquet_shard"]].append(r)

    with Progress() as prog:
        task = prog.add_task("waxal", total=len(todo))
        done = 0
        for shard, group in by_shard.items():
            path = hf_hub_download(repo_id="google/WaxalNLP", filename=shard, repo_type="dataset")
            wanted = {r["audio_filename"]: r["audio_path"] for r in group}
            t = pq.read_table(path, columns=["audio"])
            for row in t.to_pylist():
                a = row.get("audio") or {}
                nm = a.get("path")
                if nm in wanted:
                    Path(wanted[nm]).write_bytes(a["bytes"])
                    done += 1
                    prog.update(task, completed=done)
    rprint(f"[green]Extracted {done} waxal files[/green]")


def main(
    iso: str = typer.Argument(...),
    source: str = typer.Option("all", help="afrivoice|waxal|all"),
) -> None:
    manifest = DATA_ROOT / "manifests" / f"{iso}_asr.jsonl"
    if not manifest.exists():
        rprint(f"[red]Manifest missing: {manifest}[/red]")
        raise typer.Exit(1)
    rows = [json.loads(l) for l in manifest.open() if l.strip()]
    rprint(f"[cyan]Loaded {len(rows)} manifest rows[/cyan]")

    if source in ("all", "afrivoice"):
        extract_afrivoice(rows, iso)
    if source in ("all", "waxal"):
        extract_waxal(rows, iso)


if __name__ == "__main__":
    typer.run(main)
