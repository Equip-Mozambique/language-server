"""Hybrid translation: Whisper translate-to-English (audio path, handled in routes_stt)
+ NLLB-200 for text."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import torch


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

NLLB_MODEL_ID = "facebook/nllb-200-distilled-600M"

# Source languages whose Whisper pipeline can task=translate directly to English.
WHISPER_TRANSLATE_SRC = {"sna", "nya", "por"}

# ISO 639-3 → NLLB FLORES code. None entries mark explicit no-coverage.
NLLB_CODES: dict[str, str | None] = {
    "sna": "sna_Latn",
    "nya": "nya_Latn",
    "tso": "tso_Latn",
    "yao": "yao_Latn",
    "ven": "ven_Latn",
    "por": "por_Latn",
    "nde": "nde_Latn",
    "seh": None,
    "ndc": None,
    "kck": None,
    "nmq": None,
    "vmw": None,
    "ngl": None,
    "chw": None,
    "tsc": None,
    "rng": None,
    "toi": None,
}

NLLB_TARGETS = {"en": "eng_Latn", "pt": "por_Latn"}


def plan_translation(src_iso: str, tgt: str) -> dict[str, Any]:
    """Best-route plan assuming both audio and text inputs are available."""
    if tgt == "en" and src_iso in WHISPER_TRANSLATE_SRC:
        return {"engine": "whisper-translate", "covered": True}
    if NLLB_CODES.get(src_iso) and tgt in NLLB_TARGETS:
        return {"engine": "nllb", "covered": True}
    return {"engine": "none", "covered": False}


@lru_cache(maxsize=1)
def _nllb():
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(NLLB_MODEL_ID)
    mdl = AutoModelForSeq2SeqLM.from_pretrained(NLLB_MODEL_ID).to(DEVICE)
    return tok, mdl


def _nllb_translate(text: str, src_flores: str, tgt_flores: str) -> str:
    """Run NLLB on a text string. Lazy-loads model on first call."""
    tok, mdl = _nllb()
    tok.src_lang = src_flores
    inputs = tok(text, return_tensors="pt").to(DEVICE)
    out_ids = mdl.generate(
        **inputs,
        forced_bos_token_id=tok.convert_tokens_to_ids(tgt_flores),
        max_new_tokens=256,
    )
    return tok.batch_decode(out_ids, skip_special_tokens=True)[0]


def translate_text(text: str, src_iso: str, tgt: str) -> dict[str, Any]:
    """Text-only translation. Whisper-translate is audio-only; this falls back to NLLB."""
    src_flores = NLLB_CODES.get(src_iso)
    tgt_flores = NLLB_TARGETS.get(tgt)
    if src_flores and tgt_flores:
        translated = _nllb_translate(text, src_flores, tgt_flores)
        return {"text": translated, "engine": "nllb", "covered": True}
    return {"text": "", "engine": "none", "covered": False}
