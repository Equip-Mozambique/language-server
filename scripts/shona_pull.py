"""Pull 5 new Shona corpora identified in 2026-05-24 deep-research.

Top finds (impact-ordered):
  1. DigitalUmuganda AfriVoice — ~100h transcribed multi-speaker Shona (CC-BY-4.0)
  2. MADLAD-400 sn clean — ~31.6M tokens multi-domain text (ODC-BY)
  3. WAXAL sna_asr — ~65-80h transcribed multi-speaker (CC-BY-SA-4.0)
  4. Wikipedia Shona dump — ~3-5M tokens (CC-BY-SA)
  5. eBible Biblica SNABIB — full OT+NT Bible (CC-BY-SA-4.0)

Each subcommand is idempotent — skips if output exists.
Outputs land under `data/audio/sna/<source>/` or `data/text/sna/<source>/`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import httpx
import typer
from rich import print as rprint
from rich.progress import Progress


DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
ISO = "sna"


def _stream_download(url: str, dest: Path, chunk: int = 1 << 18) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with httpx.stream("GET", url, timeout=600.0, follow_redirects=True) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length") or 0)
        with dest.open("wb") as f, Progress() as prog:
            task = prog.add_task(dest.name, total=total or None)
            for blk in r.iter_bytes(chunk):
                f.write(blk)
                written += len(blk)
                prog.update(task, completed=written)
    return written


def cmd_afrivoice() -> None:
    """1. DigitalUmuganda AfriVoice — Shona slice (~574h total, ~100h transcribed).

    Audio shards already cached at ~/.cache/huggingface/hub/datasets--DigitalUmuganda--AfriVoice/.
    Per-shard manifest_N.json (JSONL) lives alongside in the repo; pull those, merge.
    """
    out_dir = DATA_ROOT / "audio" / ISO / "afrivoice"
    out_jsonl = out_dir / "manifest.jsonl"
    if out_jsonl.exists() and out_jsonl.stat().st_size > 0:
        rprint(f"[dim]afrivoice manifest exists — skipping[/dim]")
        return
    out_dir.mkdir(parents=True, exist_ok=True)

    from huggingface_hub import hf_hub_download, list_repo_files

    rprint("[cyan]AfriVoice — listing Shona manifests on HF[/cyan]")
    files = list_repo_files("DigitalUmuganda/AfriVoice", repo_type="dataset")
    manifests = sorted(f for f in files if f.startswith("Shona/manifest_") and f.endswith(".json"))
    rprint(f"  {len(manifests)} manifest files")

    total = 0
    transcribed = 0
    with out_jsonl.open("w", encoding="utf-8") as out:
        for i, name in enumerate(manifests):
            path = hf_hub_download(
                repo_id="DigitalUmuganda/AfriVoice",
                filename=name,
                repo_type="dataset",
            )
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    row = json.loads(line)
                    if row.get("transcription"):
                        transcribed += 1
                    out.write(json.dumps(row, ensure_ascii=False) + "\n")
                    total += 1
            if (i + 1) % 10 == 0:
                rprint(f"  ...{i+1}/{len(manifests)} shards, {total:,} rows ({transcribed:,} transcribed)")

    rprint(f"[green]Wrote {out_jsonl} — {total:,} rows ({transcribed:,} transcribed)[/green]")
    rprint(f"  Audio shards: ~/.cache/huggingface/hub/datasets--DigitalUmuganda--AfriVoice/snapshots/*/Shona/audio_shards/")


def cmd_madlad() -> None:
    """2. MADLAD-400 — Shona clean slice (~31.6M tokens text).

    `load_dataset` rejects per-lang configs (only 'default' exists).
    Download `data-v1p5/sn/clean_docs_*.jsonl.gz` directly via hf_hub.
    """
    out_dir = DATA_ROOT / "text" / ISO / "madlad400"
    target = out_dir / "shona_clean.jsonl"
    if target.exists() and target.stat().st_size > 0:
        rprint(f"[dim]madlad400 exists — skipping[/dim]")
        return
    out_dir.mkdir(parents=True, exist_ok=True)

    import gzip
    from huggingface_hub import hf_hub_download, list_repo_files

    rprint("[cyan]MADLAD-400 sn clean — listing shards[/cyan]")
    files = list_repo_files("allenai/MADLAD-400", repo_type="dataset")
    clean = sorted(f for f in files if f.startswith("data-v1p5/sn/clean_docs_"))
    rprint(f"  {len(clean)} clean shards")

    written = 0
    total_chars = 0
    with target.open("w", encoding="utf-8") as out:
        for name in clean:
            rprint(f"  downloading {name}")
            path = hf_hub_download(
                repo_id="allenai/MADLAD-400",
                filename=name,
                repo_type="dataset",
            )
            with gzip.open(path, "rt", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    row = json.loads(line)
                    txt = row.get("text") or row.get("content") or ""
                    if not txt:
                        continue
                    out.write(json.dumps({"text": txt}, ensure_ascii=False) + "\n")
                    written += 1
                    total_chars += len(txt)
            rprint(f"    cumulative: {written:,} rows, {total_chars:,} chars")
    rprint(f"[green]Wrote {target} — {written:,} rows, {total_chars:,} chars[/green]")


def cmd_waxal() -> None:
    """3. WAXAL google/WaxalNLP — sna_asr (~65-80h transcribed multi-speaker)."""
    out_dir = DATA_ROOT / "audio" / ISO / "waxal"
    manifest = out_dir / "manifest.json"
    if manifest.exists():
        rprint(f"[dim]waxal exists — skipping[/dim]")
        return
    out_dir.mkdir(parents=True, exist_ok=True)

    from datasets import load_dataset

    rprint("[cyan]WAXAL sna_asr — loading (cached)[/cyan]")
    from datasets import Audio

    ds = None
    for cfg in ("sna_asr", "sn_asr", "shona_asr", "sna"):
        try:
            ds = load_dataset("google/WaxalNLP", cfg, split="train")
            rprint(f"  loaded cfg={cfg!r}")
            break
        except Exception:
            continue
    if ds is None:
        rprint(f"[red]WAXAL load failed[/red]")
        return

    # Skip audio decoding (avoids torchcodec dependency); we only want paths.
    if "audio" in ds.column_names:
        ds = ds.cast_column("audio", Audio(decode=False))

    rprint(f"  rows: {len(ds)} | columns: {ds.column_names}")

    rows = []
    for i, ex in enumerate(ds):
        row = {"id": i}
        for k in ("transcription", "text", "speaker_id", "duration", "domain"):
            if k in ds.column_names:
                row[k] = ex.get(k)
        if "audio" in ds.column_names:
            arr = ex["audio"]
            row["audio_path"] = arr.get("path") if isinstance(arr, dict) else None
            row["sampling_rate"] = arr.get("sampling_rate") if isinstance(arr, dict) else None
        rows.append(row)
    manifest.write_text(json.dumps(rows, indent=2, ensure_ascii=False))
    rprint(f"[green]Wrote {manifest} — {len(rows)} entries[/green]")


def cmd_wikipedia() -> None:
    """4. Wikipedia Shona — pre-extracted parquet from wikimedia/wikipedia.

    wikiextractor 3.0.6 has a regex bug on Python 3.12; use HF's cleaned mirror.
    Dump: 20231101.sn (~11k articles).
    """
    out_dir = DATA_ROOT / "text" / ISO / "wikipedia"
    target = out_dir / "snwiki.jsonl"
    out_dir.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size > 0:
        rprint(f"[dim]wikipedia jsonl exists — skipping[/dim]")
        return

    import pyarrow.parquet as pq
    from huggingface_hub import hf_hub_download

    rprint("[cyan]Wikipedia sn — downloading parquet[/cyan]")
    path = hf_hub_download(
        repo_id="wikimedia/wikipedia",
        filename="20231101.sn/train-00000-of-00001.parquet",
        repo_type="dataset",
    )
    table = pq.read_table(path)
    rprint(f"  rows: {table.num_rows} | columns: {table.column_names}")

    written = 0
    total_chars = 0
    with target.open("w", encoding="utf-8") as out:
        rows = table.to_pylist()
        for row in rows:
            txt = row.get("text") or ""
            if not txt:
                continue
            entry = {"id": row.get("id"), "title": row.get("title"), "url": row.get("url"), "text": txt}
            out.write(json.dumps(entry, ensure_ascii=False) + "\n")
            written += 1
            total_chars += len(txt)
    rprint(f"[green]Wrote {target} — {written:,} articles, {total_chars:,} chars[/green]")


def cmd_ebible() -> None:
    """5. eBible Biblica SNABIB — full OT+NT Shona Bible."""
    out_dir = DATA_ROOT / "text" / ISO / "ebible_snabib"
    target = out_dir / "snabib.zip"
    out_dir.mkdir(parents=True, exist_ok=True)

    if target.exists() and (out_dir / "extracted").exists():
        rprint(f"[dim]ebible SNABIB exists — skipping[/dim]")
        return

    # Try canonical eBible URL pattern
    candidates = [
        "https://ebible.org/Scriptures/snabib_usfm.zip",
        "https://ebible.org/Scriptures/snabib.zip",
        "https://ebible.org/Scriptures/sna_readaloud.zip",
    ]
    last_err = None
    for url in candidates:
        try:
            rprint(f"  trying {url}")
            size = _stream_download(url, target)
            rprint(f"  -> {size // 1024} KB")
            break
        except Exception as e:
            last_err = e
            target.unlink(missing_ok=True)
            continue
    else:
        rprint(f"[red]eBible SNABIB download failed: {last_err}[/red]")
        rprint("  Check https://ebible.org/Scriptures/ for the current Shona archive URL")
        return

    # Extract
    ext_dir = out_dir / "extracted"
    ext_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(target) as zf:
        zf.extractall(ext_dir)
    files = list(ext_dir.rglob("*"))
    rprint(f"[green]Extracted {len(files)} files to {ext_dir}[/green]")


def cmd_all() -> None:
    """Run all 5 in order."""
    for fn in (cmd_afrivoice, cmd_madlad, cmd_waxal, cmd_wikipedia, cmd_ebible):
        rprint(f"\n[bold cyan]>>> {fn.__name__}[/bold cyan]")
        try:
            fn()
        except Exception as e:
            rprint(f"[red]{fn.__name__} FAIL: {e}[/red]")


app = typer.Typer()
app.command("afrivoice")(cmd_afrivoice)
app.command("madlad")(cmd_madlad)
app.command("waxal")(cmd_waxal)
app.command("wikipedia")(cmd_wikipedia)
app.command("ebible")(cmd_ebible)
app.command("all")(cmd_all)


if __name__ == "__main__":
    app()
