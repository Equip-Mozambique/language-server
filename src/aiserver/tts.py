"""Text-to-speech engines (MMS-TTS, Piper, Toucan)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import torch

from .languages import get


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


@lru_cache(maxsize=64)
def _mms_tts(lang_iso: str):
    from transformers import VitsModel, AutoTokenizer

    model_id = f"facebook/mms-tts-{lang_iso}"
    tok = AutoTokenizer.from_pretrained(model_id)
    model = VitsModel.from_pretrained(model_id).to(DEVICE)
    return tok, model


def synthesize_mms(text: str, lang_iso: str, out_path: str | Path) -> Path:
    import soundfile as sf

    lang = get(lang_iso)
    if lang.mms_tts is None:
        raise ValueError(f"{lang.name} not in MMS-TTS")
    tok, model = _mms_tts(lang.mms_tts)
    inputs = tok(text, return_tensors="pt").to(DEVICE)
    with torch.no_grad():
        waveform = model(**inputs).waveform[0].cpu().numpy()
    out = Path(out_path)
    sf.write(out, waveform.astype(np.float32), samplerate=model.config.sampling_rate)
    return out


def synthesize(text: str, lang_iso: str, out_path: str | Path) -> Path:
    lang = get(lang_iso)
    match lang.preferred_tts:
        case "mms":
            return synthesize_mms(text, lang_iso, out_path)
        case _:
            raise NotImplementedError(f"TTS engine '{lang.preferred_tts}' not wired yet")
