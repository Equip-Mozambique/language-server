"""Build unified ASR manifest with speaker-disjoint train/dev/test splits.

Recipe step 1+2. Language-agnostic — pass ISO 639-3 code as arg.

For each enabled source, ingest paired (audio_path, text, speaker_id, duration),
normalize text, and assign train/dev/test via hashed speaker_id buckets.

Output:
    data/manifests/<ISO>_asr.jsonl
    data/manifests/<ISO>_speaker_buckets.json
    data/manifests/<ISO>_asr_stats.json

Usage:
    python scripts/asr_build_manifest.py <ISO> [--sources afrivoice,waxal]
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import typer
from rich import print as rprint

DATA_ROOT = Path(__file__).resolve().parents[1] / "data"


def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s).lower()
    s = re.sub(r"[^\w\s'À-ɏ]", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def split_bucket(speaker_id: str | None) -> str:
    """Hash speaker_id → 80/10/10 train/dev/test bucket."""
    if not speaker_id:
        # Anonymous rows: deterministic per-row split by None marker bucket
        return "train"
    h = int(hashlib.md5(speaker_id.encode()).hexdigest(), 16) % 100
    if h < 80:
        return "train"
    if h < 90:
        return "dev"
    return "test"


def ingest_afrivoice(iso: str) -> list[dict]:
    src = DATA_ROOT / "audio" / iso / "afrivoice" / "manifest.jsonl"
    if not src.exists():
        rprint(f"[yellow]afrivoice manifest missing for {iso}[/yellow]")
        return []
    rprint(f"[cyan]Ingest afrivoice from {src}[/cyan]")
    out = []
    skipped_no_text = 0
    skipped_dur = 0
    wavs_dir = DATA_ROOT / "audio" / iso / "afrivoice" / "wavs"
    with src.open() as f:
        for line in f:
            row = json.loads(line)
            txt = row.get("transcription")
            if not txt:
                skipped_no_text += 1
                continue
            txt_n = normalize_text(txt)
            if not txt_n:
                skipped_no_text += 1
                continue
            dur = row.get("duration") or 0.0
            if dur < 1.0 or dur > 30.0:
                skipped_dur += 1
                continue
            audio_filepath = row.get("audio_filepath")  # e.g. "audio_5WVMLWM20NSR.wav"
            shard_id = row.get("shard_id")
            out.append({
                "audio_path": str(wavs_dir / audio_filepath),
                "shard_id": shard_id,
                "audio_filename": audio_filepath,
                "text": txt_n,
                "text_raw": txt,
                "duration": float(dur),
                "speaker_id": row.get("speaker_id"),
                "gender": row.get("gender"),
                "source": "afrivoice",
            })
    rprint(f"  kept {len(out)} | skipped no-text {skipped_no_text} | skipped duration {skipped_dur}")
    return out


def ingest_waxal(iso: str) -> list[dict]:
    """Read WAXAL parquet shards directly from HF cache, write wavs to disk paths."""
    import pyarrow.parquet as pq
    from huggingface_hub import list_repo_files, hf_hub_download

    rprint(f"[cyan]Ingest waxal {iso} from HF[/cyan]")
    files = list_repo_files("google/WaxalNLP", repo_type="dataset")
    shards = sorted(
        f for f in files
        if f.startswith(f"data/ASR/{iso}/{iso}-train-") or f.startswith(f"data/ASR/{iso}/{iso}-test-")
    )
    if not shards:
        rprint(f"[yellow]No waxal shards for {iso}[/yellow]")
        return []
    rprint(f"  {len(shards)} train+test parquet shards")

    wavs_dir = DATA_ROOT / "audio" / iso / "waxal" / "wavs"
    out = []
    skipped_no_text = 0
    for i, shard in enumerate(shards):
        path = hf_hub_download(repo_id="google/WaxalNLP", filename=shard, repo_type="dataset")
        t = pq.read_table(path, columns=["id", "speaker_id", "transcription", "audio"])
        for row in t.to_pylist():
            txt = row.get("transcription")
            if not txt:
                skipped_no_text += 1
                continue
            txt_n = normalize_text(txt)
            if not txt_n:
                skipped_no_text += 1
                continue
            audio = row.get("audio") or {}
            audio_filename = audio.get("path") or f"{row['id']}.mp3"
            out.append({
                "audio_path": str(wavs_dir / audio_filename),
                "audio_filename": audio_filename,
                "parquet_shard": shard,
                "row_id": row.get("id"),
                "text": txt_n,
                "text_raw": txt,
                "duration": None,
                "speaker_id": row.get("speaker_id"),
                "source": "waxal",
            })
        if (i + 1) % 10 == 0:
            rprint(f"  ...{i+1}/{len(shards)} shards, {len(out)} rows")
    rprint(f"  kept {len(out)} | skipped no-text {skipped_no_text}")
    return out


SOURCE_FNS = {"afrivoice": ingest_afrivoice, "waxal": ingest_waxal}


def main(
    iso: str = typer.Argument(..., help="ISO 639-3 code, e.g. sna"),
    sources: str = typer.Option("afrivoice,waxal", help="Comma-separated source list"),
) -> None:
    rprint(f"[bold cyan]Build ASR manifest for {iso}[/bold cyan]")
    src_list = [s.strip() for s in sources.split(",") if s.strip()]

    rows: list[dict] = []
    for src in src_list:
        fn = SOURCE_FNS.get(src)
        if not fn:
            rprint(f"[red]Unknown source: {src}[/red]")
            sys.exit(2)
        rows.extend(fn(iso))

    if not rows:
        rprint(f"[red]No rows ingested[/red]")
        sys.exit(1)

    rprint(f"\n[cyan]Total rows: {len(rows)}[/cyan]")

    # Build speaker → bucket map (per-source to keep small-corpora intact)
    speakers_per_source: dict[str, set] = defaultdict(set)
    for r in rows:
        if r.get("speaker_id"):
            speakers_per_source[r["source"]].add(r["speaker_id"])

    bucket_map: dict[str, str] = {}
    for src, spks in speakers_per_source.items():
        for s in spks:
            bucket_map[s] = split_bucket(s)
        rprint(f"  {src}: {len(spks)} unique speakers")

    # Assign split
    split_counts = defaultdict(int)
    for r in rows:
        spk = r.get("speaker_id")
        r["split"] = bucket_map.get(spk, "train")
        split_counts[r["split"]] += 1

    rprint(f"\n[cyan]Split counts: {dict(split_counts)}[/cyan]")

    # Source × split breakdown
    src_split = defaultdict(lambda: defaultdict(int))
    for r in rows:
        src_split[r["source"]][r["split"]] += 1
    for src, d in src_split.items():
        rprint(f"  {src}: {dict(d)}")

    # Write outputs
    manifest_dir = DATA_ROOT / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    out_jsonl = manifest_dir / f"{iso}_asr.jsonl"
    out_buckets = manifest_dir / f"{iso}_speaker_buckets.json"
    out_stats = manifest_dir / f"{iso}_asr_stats.json"

    with out_jsonl.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    out_buckets.write_text(json.dumps(bucket_map, indent=2, ensure_ascii=False))

    stats = {
        "iso": iso,
        "total_rows": len(rows),
        "sources": src_list,
        "split_counts": dict(split_counts),
        "source_split": {k: dict(v) for k, v in src_split.items()},
        "unique_speakers_per_source": {k: len(v) for k, v in speakers_per_source.items()},
    }
    out_stats.write_text(json.dumps(stats, indent=2))
    rprint(f"\n[green]Wrote {out_jsonl}[/green]")
    rprint(f"[green]Wrote {out_buckets}[/green]")
    rprint(f"[green]Wrote {out_stats}[/green]")


if __name__ == "__main__":
    typer.run(main)
