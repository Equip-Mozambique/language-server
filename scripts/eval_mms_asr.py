"""Evaluate fine-tuned MMS-ASR adapter on test split (recipe step 5).

Reports WER + CER overall, per source, per top-10 test speakers, and dumps
worst-50 hypotheses.

Usage:
    python scripts/eval_mms_asr.py <ISO> [--model models/mms-<ISO>-adapter-v1/final]
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import typer
from rich import print as rprint

DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
MODELS_ROOT = Path(__file__).resolve().parents[1] / "models"


def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s).lower()
    s = re.sub(r"[^\w\s'À-ɏ]", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def main(
    iso: str = typer.Argument(...),
    model: str = typer.Option("", help="Path to fine-tuned adapter dir (default: models/mms-<ISO>-adapter-v1/final)"),
    batch_size: int = 8,
    max_examples: int = 0,
) -> None:
    import torch
    import torchaudio
    import soundfile as sf
    import jiwer
    from transformers import AutoProcessor, Wav2Vec2ForCTC

    if not model:
        model = str(MODELS_ROOT / f"mms-{iso}-adapter-v1" / "final")
    rprint(f"[bold cyan]Eval {iso} model={model}[/bold cyan]")

    test_path = DATA_ROOT / "manifests" / f"{iso}_asr.jsonl"
    rows = [json.loads(l) for l in test_path.open() if l.strip()]
    test_rows = [r for r in rows if r["split"] == "test" and Path(r["audio_path"]).exists()]
    if max_examples:
        test_rows = test_rows[:max_examples]
    rprint(f"  test rows on-disk: {len(test_rows)}")

    proc = AutoProcessor.from_pretrained(model, target_lang=iso)
    m = Wav2Vec2ForCTC.from_pretrained(model, target_lang=iso, ignore_mismatched_sizes=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    m.to(device).eval()
    rprint(f"  device: {device}")

    hyps, refs, srcs, spks, paths = [], [], [], [], []

    def transcribe_batch(batch_rows):
        waves = []
        for r in batch_rows:
            wav, sr = sf.read(r["audio_path"])
            if wav.ndim > 1:
                wav = wav.mean(axis=1)
            if sr != 16000:
                wav_t = torch.from_numpy(wav).float().unsqueeze(0)
                wav_t = torchaudio.functional.resample(wav_t, sr, 16000)
                wav = wav_t.squeeze(0).numpy()
            waves.append(wav)
        inp = proc(waves, sampling_rate=16000, return_tensors="pt", padding=True).to(device)
        with torch.no_grad():
            logits = m(**inp).logits
        pred = logits.argmax(-1)
        return proc.batch_decode(pred)

    for i in range(0, len(test_rows), batch_size):
        chunk = test_rows[i : i + batch_size]
        texts = transcribe_batch(chunk)
        for r, h in zip(chunk, texts):
            hyps.append(normalize_text(h))
            refs.append(normalize_text(r["text"]))
            srcs.append(r["source"])
            spks.append(r.get("speaker_id"))
            paths.append(r["audio_path"])
        if (i // batch_size + 1) % 20 == 0:
            rprint(f"  ...{i + len(chunk)}/{len(test_rows)}")

    overall_wer = jiwer.wer(refs, hyps)
    overall_cer = jiwer.cer(refs, hyps)
    rprint(f"\n[bold green]Overall WER: {overall_wer:.3f}  CER: {overall_cer:.3f}[/bold green]")

    # Per source
    by_src = defaultdict(lambda: ([], []))
    for r, h, s in zip(refs, hyps, srcs):
        by_src[s][0].append(r)
        by_src[s][1].append(h)
    per_source = {}
    for s, (R, H) in by_src.items():
        per_source[s] = {
            "n": len(R),
            "wer": jiwer.wer(R, H),
            "cer": jiwer.cer(R, H),
        }
        rprint(f"  {s}: WER {per_source[s]['wer']:.3f}  CER {per_source[s]['cer']:.3f}  (n={len(R)})")

    # Per top-10 speakers by count
    by_spk = defaultdict(lambda: ([], []))
    for r, h, s in zip(refs, hyps, spks):
        if s:
            by_spk[s][0].append(r)
            by_spk[s][1].append(h)
    top_spks = sorted(by_spk.items(), key=lambda kv: -len(kv[1][0]))[:10]
    per_speaker = []
    for s, (R, H) in top_spks:
        per_speaker.append({
            "speaker_id": s,
            "n": len(R),
            "wer": jiwer.wer(R, H),
        })

    # Worst-50 by individual WER (single-utterance)
    indiv = []
    for r, h, src, spk, p in zip(refs, hyps, srcs, spks, paths):
        w = jiwer.wer([r], [h]) if r and h else 1.0
        indiv.append((w, r, h, src, spk, p))
    indiv.sort(key=lambda x: -x[0])
    worst = indiv[:50]

    eval_dir = DATA_ROOT / "research"
    eval_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "iso": iso,
        "model": model,
        "n_test": len(test_rows),
        "wer": overall_wer,
        "cer": overall_cer,
        "per_source": per_source,
        "per_speaker_top10": per_speaker,
    }
    out_json = eval_dir / f"{iso}_mms_asr_eval.json"
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    rprint(f"[green]Wrote {out_json}[/green]")

    worst_path = eval_dir / f"{iso}_worst.tsv"
    with worst_path.open("w", encoding="utf-8") as f:
        f.write("wer\tsource\tspeaker\tref\thyp\tpath\n")
        for w, r, h, s, sp, p in worst:
            f.write(f"{w:.3f}\t{s}\t{sp}\t{r}\t{h}\t{p}\n")
    rprint(f"[green]Wrote {worst_path}[/green]")


if __name__ == "__main__":
    typer.run(main)
