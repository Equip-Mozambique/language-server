"""Empirical MMS coverage probe for a target language.

Loads facebook/mms-1b-all with `target_lang=<ISO>`, runs inference on N random
transcribed clips, computes WER + CER, and writes a JSON report to
data/research/<ISO>_mms_baseline.json.

Used to decide adapter init strategy before training (recipe step 0).

Usage:
    python scripts/mms_probe.py <ISO> [--n 50] [--source waxal|afrivoice]
"""

from __future__ import annotations

import io
import json
import random
import re
import sys
import unicodedata
from pathlib import Path

import typer
from rich import print as rprint

DATA_ROOT = Path(__file__).resolve().parents[1] / "data"


def normalize_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).lower()
    s = re.sub(r"[^\w\s'À-ɏ]", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def wer_cer(refs: list[str], hyps: list[str]) -> tuple[float, float]:
    import jiwer
    refs_n = [normalize_text(r) for r in refs]
    hyps_n = [normalize_text(h) for h in hyps]
    w = jiwer.wer(refs_n, hyps_n)
    c = jiwer.cer(refs_n, hyps_n)
    return w, c


def collect_waxal_clips(iso: str, n: int, seed: int = 42) -> list[dict]:
    """Pull N random rows from waxal test parquet shards (audio bytes inline)."""
    import pyarrow.parquet as pq
    from huggingface_hub import list_repo_files, hf_hub_download

    files = list_repo_files("google/WaxalNLP", repo_type="dataset")
    test_shards = sorted(f for f in files if f.startswith(f"data/ASR/{iso}/{iso}-test-"))
    if not test_shards:
        rprint(f"[red]No WAXAL test shards for {iso}[/red]")
        return []

    all_rows = []
    for shard in test_shards:
        path = hf_hub_download(repo_id="google/WaxalNLP", filename=shard, repo_type="dataset")
        t = pq.read_table(path, columns=["id", "transcription", "audio"])
        for r in t.to_pylist():
            if r.get("transcription"):
                all_rows.append(r)
    rprint(f"  {len(all_rows)} transcribed test rows")
    rng = random.Random(seed)
    rng.shuffle(all_rows)
    return all_rows[:n]


def run_inference(rows: list[dict], iso: str) -> list[str]:
    import torch
    import torchaudio
    import soundfile as sf
    from transformers import AutoProcessor, Wav2Vec2ForCTC

    rprint("[cyan]Loading facebook/mms-1b-all[/cyan]")
    proc = AutoProcessor.from_pretrained("facebook/mms-1b-all", target_lang=iso)
    model = Wav2Vec2ForCTC.from_pretrained(
        "facebook/mms-1b-all", target_lang=iso, ignore_mismatched_sizes=True,
    )
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device).eval()
    rprint(f"  device: {device}")

    hyps = []
    for i, row in enumerate(rows):
        audio_bytes = row["audio"]["bytes"]
        wav, sr = sf.read(io.BytesIO(audio_bytes))
        if wav.ndim > 1:
            wav = wav.mean(axis=1)
        if sr != 16000:
            wav_t = torch.from_numpy(wav).float().unsqueeze(0)
            wav_t = torchaudio.functional.resample(wav_t, sr, 16000)
            wav = wav_t.squeeze(0).numpy()
        inputs = proc(wav, sampling_rate=16000, return_tensors="pt").to(device)
        with torch.no_grad():
            logits = model(**inputs).logits
        pred = logits.argmax(dim=-1)
        text = proc.batch_decode(pred)[0]
        hyps.append(text)
        if (i + 1) % 10 == 0:
            rprint(f"  ...{i+1}/{len(rows)}")
    return hyps


def main(
    iso: str = typer.Argument(..., help="ISO 639-3 code, e.g. sna"),
    n: int = typer.Option(50, help="Number of clips to probe"),
    source: str = typer.Option("waxal", help="Source: waxal | afrivoice"),
    seed: int = typer.Option(42),
) -> None:
    rprint(f"[bold cyan]MMS probe for {iso}[/bold cyan]")

    if source == "waxal":
        rows = collect_waxal_clips(iso, n, seed)
    else:
        rprint(f"[red]Source {source} not yet implemented in probe[/red]")
        sys.exit(2)
    if not rows:
        sys.exit(1)

    refs = [r["transcription"] for r in rows]
    try:
        hyps = run_inference(rows, iso)
    except Exception as e:
        rprint(f"[red]MMS load/inference failed: {e}[/red]")
        report = {"iso": iso, "n": len(rows), "source": source, "error": str(e),
                  "decision": "scratch_adapter"}
        out = DATA_ROOT / "research" / f"{iso}_mms_baseline.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2))
        rprint(f"[yellow]Wrote {out}[/yellow]")
        sys.exit(1)

    w, c = wer_cer(refs, hyps)
    rprint(f"\n[bold]Baseline WER: {w:.3f}  CER: {c:.3f}  (n={len(rows)})[/bold]")

    if w < 0.30:
        decision = "stock_adapter_init"
    elif w < 0.50:
        decision = "stock_adapter_high_lr"
    else:
        decision = "scratch_adapter"

    examples = [{"ref": r, "hyp": h, "ref_norm": normalize_text(r), "hyp_norm": normalize_text(h)}
                for r, h in list(zip(refs, hyps))[:10]]
    report = {
        "iso": iso, "n": len(rows), "source": source,
        "wer": w, "cer": c, "decision": decision, "examples": examples,
    }
    out = DATA_ROOT / "research" / f"{iso}_mms_baseline.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    rprint(f"[green]Wrote {out}[/green]")
    rprint(f"[bold]Decision: {decision}[/bold]")


if __name__ == "__main__":
    typer.run(main)
