"""Fine-tune MMS-1B adapter for a target language (recipe step 4).

Reads data/manifests/<ISO>_asr.jsonl, fine-tunes the per-language adapter +
CTC head of facebook/mms-1b-all, saves to models/mms-<ISO>-adapter-v1/.

Usage:
    # Smoke (500 steps on 10% data)
    python scripts/train_mms_asr.py <ISO> --max-steps 500 --train-frac 0.1

    # Full
    python scripts/train_mms_asr.py <ISO> --max-steps 20000
"""

from __future__ import annotations

import io
import json
import os
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import typer
from rich import print as rprint

DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
MODELS_ROOT = Path(__file__).resolve().parents[1] / "models"


def load_manifest(iso: str, split: str | None = None) -> list[dict]:
    p = DATA_ROOT / "manifests" / f"{iso}_asr.jsonl"
    rows = [json.loads(l) for l in p.open() if l.strip()]
    if split:
        rows = [r for r in rows if r["split"] == split]
    return rows


def per_source_cap(rows: list[dict], caps_pct: dict[str, int]) -> list[dict]:
    """Cap each source's count to its allowed pct of the largest other source.

    Used to keep single-speaker corpora (Bible) from dominating training mix.
    """
    by_src = defaultdict(list)
    for r in rows:
        by_src[r["source"]].append(r)
    capped = []
    largest_other = max((len(v) for k, v in by_src.items() if caps_pct.get(k, 100) >= 100), default=0)
    for src, items in by_src.items():
        cap_pct = caps_pct.get(src, 100)
        if cap_pct >= 100:
            capped.extend(items)
        else:
            limit = max(1, int(largest_other * cap_pct / 100))
            random.shuffle(items)
            capped.extend(items[:limit])
    return capped


def build_vocab(train_rows: list[dict]) -> dict[str, int]:
    chars: set[str] = set()
    for r in train_rows:
        chars.update(r["text"])
    chars -= {" "}
    vocab = {c: i for i, c in enumerate(sorted(chars))}
    vocab["|"] = len(vocab)        # word boundary
    vocab["<unk>"] = len(vocab)
    vocab["<pad>"] = len(vocab)
    return vocab


@dataclass
class ASRDataset:
    rows: list[dict]
    processor: Any
    max_sec: float = 15.0

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):
        import soundfile as sf
        import torchaudio
        import torch
        row = self.rows[idx]
        wav, sr = sf.read(row["audio_path"])
        if wav.ndim > 1:
            wav = wav.mean(axis=1)
        if sr != 16000:
            wav_t = torch.from_numpy(wav).float().unsqueeze(0)
            wav_t = torchaudio.functional.resample(wav_t, sr, 16000)
            wav = wav_t.squeeze(0).numpy()
        if len(wav) > int(self.max_sec * 16000):
            wav = wav[: int(self.max_sec * 16000)]
        inputs = self.processor(wav, sampling_rate=16000, return_tensors="pt")
        labels = self.processor.tokenizer(row["text"]).input_ids
        return {
            "input_values": inputs.input_values.squeeze(0),
            "labels": labels,
        }


@dataclass
class CTCCollator:
    processor: Any

    def __call__(self, features):
        input_features = [{"input_values": f["input_values"]} for f in features]
        label_features = [{"input_ids": f["labels"]} for f in features]
        batch = self.processor.feature_extractor.pad(input_features, padding=True, return_tensors="pt")
        labels_batch = self.processor.tokenizer.pad(label_features, padding=True, return_tensors="pt")
        labels = labels_batch["input_ids"].masked_fill(
            labels_batch.attention_mask.ne(1), -100
        )
        batch["labels"] = labels
        return batch


def compute_metrics_fn(processor):
    import jiwer

    def fn(pred):
        import numpy as np
        pred_ids = pred.predictions.argmax(-1) if hasattr(pred.predictions, "argmax") else np.argmax(pred.predictions, axis=-1)
        labels = pred.label_ids
        labels[labels == -100] = processor.tokenizer.pad_token_id
        pred_str = processor.batch_decode(pred_ids)
        label_str = processor.batch_decode(labels, group_tokens=False)
        wer = jiwer.wer(label_str, pred_str)
        cer = jiwer.cer(label_str, pred_str)
        return {"wer": wer, "cer": cer}

    return fn


def main(
    iso: str = typer.Argument(...),
    max_steps: int = 20000,
    train_frac: float = 1.0,
    batch_size: int = 8,
    grad_accum: int = 8,
    lr: float = 1e-3,
    warmup_steps: int = 500,
    eval_steps: int = 1000,
    save_steps: int = 2000,
    bible_cap_pct: int = 30,
    seed: int = 42,
    output_subdir: str = "v1",
) -> None:
    import torch
    from transformers import (
        Wav2Vec2ForCTC,
        AutoProcessor,
        TrainingArguments,
        Trainer,
    )

    rprint(f"[bold cyan]MMS-ASR train: {iso}[/bold cyan]")
    rprint(f"  CUDA: {torch.cuda.is_available()} | device 0: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu'}")

    train_rows = load_manifest(iso, "train")
    dev_rows = load_manifest(iso, "dev")
    rprint(f"  train rows: {len(train_rows)} | dev rows: {len(dev_rows)}")

    # Bible cap (only matters once dbp_bible source ingested; harmless otherwise)
    caps = {"dbp_bible": bible_cap_pct}
    train_rows = per_source_cap(train_rows, caps)
    rprint(f"  after source cap: {len(train_rows)}")

    random.seed(seed)
    if train_frac < 1.0:
        random.shuffle(train_rows)
        train_rows = train_rows[: int(len(train_rows) * train_frac)]
        rprint(f"  smoke subset: {len(train_rows)}")

    # Filter rows whose audio is missing or 0-byte (afrivoice tarballs ship some empty placeholders)
    def usable(p):
        try:
            return Path(p).stat().st_size > 0
        except FileNotFoundError:
            return False
    train_rows = [r for r in train_rows if usable(r["audio_path"])]
    dev_rows = [r for r in dev_rows if usable(r["audio_path"])]
    rprint(f"  after on-disk filter (non-empty): train {len(train_rows)} | dev {len(dev_rows)}")

    rprint(f"[cyan]Loading processor (target_lang={iso})[/cyan]")
    processor = AutoProcessor.from_pretrained("facebook/mms-1b-all", target_lang=iso)

    rprint("[cyan]Loading model with stock adapter (bf16)[/cyan]")
    model = Wav2Vec2ForCTC.from_pretrained(
        "facebook/mms-1b-all",
        target_lang=iso,
        ignore_mismatched_sizes=True,
        torch_dtype=torch.bfloat16,
    )
    # Freeze everything, then unfreeze adapter layers + lm_head
    for p in model.parameters():
        p.requires_grad = False
    for n, p in model.named_parameters():
        if "adapter" in n.lower() or n.startswith("lm_head"):
            p.requires_grad = True
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    rprint(f"  trainable params: {trainable:,} / {total:,} ({100*trainable/total:.2f}%)")

    train_ds = ASRDataset(train_rows, processor)
    dev_ds = ASRDataset(dev_rows, processor)
    collator = CTCCollator(processor)

    out_dir = MODELS_ROOT / f"mms-{iso}-adapter-{output_subdir}"
    out_dir.mkdir(parents=True, exist_ok=True)

    args = TrainingArguments(
        output_dir=str(out_dir),
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        gradient_accumulation_steps=grad_accum,
        max_steps=max_steps,
        learning_rate=lr,
        warmup_steps=warmup_steps,
        eval_strategy="steps",
        eval_steps=eval_steps,
        save_steps=save_steps,
        save_total_limit=3,
        logging_steps=50,
        bf16=True,
        gradient_checkpointing=True,
        dataloader_num_workers=2,
        report_to=[],
        load_best_model_at_end=True,
        metric_for_best_model="wer",
        greater_is_better=False,
        seed=seed,
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=dev_ds,
        data_collator=collator,
        processing_class=processor,
        compute_metrics=compute_metrics_fn(processor),
    )

    rprint(f"[bold green]Training → {out_dir}[/bold green]")
    trainer.train()
    trainer.save_model(str(out_dir / "final"))
    processor.save_pretrained(str(out_dir / "final"))
    rprint(f"[bold green]Done. Saved to {out_dir / 'final'}[/bold green]")


if __name__ == "__main__":
    typer.run(main)
