"""Speech-to-text engines (Whisper, MMS)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import torch

from .languages import LANGS, get


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32


@lru_cache(maxsize=1)
def _whisper():
    from transformers import pipeline

    model_id = "openai/whisper-large-v3-turbo"
    return pipeline(
        "automatic-speech-recognition",
        model=model_id,
        dtype=DTYPE,
        device=DEVICE,
    )


@lru_cache(maxsize=1)
def _mms():
    from transformers import AutoProcessor, Wav2Vec2ForCTC

    model_id = "facebook/mms-1b-all"
    processor = AutoProcessor.from_pretrained(model_id)
    model = Wav2Vec2ForCTC.from_pretrained(model_id).to(DEVICE)
    return processor, model


def transcribe_whisper(audio: str | Path, lang_iso: str) -> str:
    import librosa

    lang = get(lang_iso)
    if lang.whisper_code is None:
        raise ValueError(f"{lang.name} not supported by Whisper")
    pipe = _whisper()
    speech, _ = librosa.load(str(audio), sr=16_000, mono=True)
    out = pipe(
        {"array": speech, "sampling_rate": 16_000},
        generate_kwargs={"language": lang.whisper_code, "task": "transcribe"},
        return_timestamps=True,
    )
    return out["text"].strip()


def transcribe_mms(audio: str | Path, lang_iso: str) -> str:
    import librosa

    lang = get(lang_iso)
    if lang.mms_iso is None:
        raise ValueError(f"{lang.name} not in MMS")
    processor, model = _mms()
    processor.tokenizer.set_target_lang(lang.mms_iso)
    model.load_adapter(lang.mms_iso)
    speech, _ = librosa.load(str(audio), sr=16_000, mono=True)
    inputs = processor(speech, sampling_rate=16_000, return_tensors="pt").to(DEVICE)
    with torch.no_grad():
        logits = model(**inputs).logits
    ids = torch.argmax(logits, dim=-1)[0]
    return processor.decode(ids).strip()


def transcribe(audio: str | Path, lang_iso: str) -> str:
    lang = get(lang_iso)
    match lang.preferred_stt:
        case "whisper":
            return transcribe_whisper(audio, lang_iso)
        case "mms":
            return transcribe_mms(audio, lang_iso)
        case _:
            raise NotImplementedError(f"STT engine '{lang.preferred_stt}' not wired yet")


def transcribe_array(samples, sr: int, lang_iso: str) -> str:
    """Transcribe from an in-memory float32 mono waveform array.

    `samples` must be float32 in [-1, 1]; `sr` should be 16 000 (resampling left
    to the caller for v1). Avoids the temp-file round-trip used by `transcribe`.
    """
    import numpy as np

    lang = get(lang_iso)
    if sr != 16_000:
        raise ValueError("transcribe_array currently requires sr=16000")
    samples = np.asarray(samples, dtype="float32")

    if lang.preferred_stt == "whisper":
        if lang.whisper_code is None:
            raise ValueError(f"{lang.name} not supported by Whisper")
        pipe = _whisper()
        out = pipe(
            {"array": samples, "sampling_rate": sr},
            generate_kwargs={"language": lang.whisper_code, "task": "transcribe"},
            return_timestamps=True,
        )
        return out["text"].strip()
    if lang.preferred_stt == "mms":
        if lang.mms_iso is None:
            raise ValueError(f"{lang.name} not in MMS")
        processor, model = _mms()
        processor.tokenizer.set_target_lang(lang.mms_iso)
        model.load_adapter(lang.mms_iso)
        inputs = processor(samples, sampling_rate=sr, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            logits = model(**inputs).logits
        ids = torch.argmax(logits, dim=-1)[0]
        return processor.decode(ids).strip()
    raise NotImplementedError(f"STT engine '{lang.preferred_stt}' not wired yet")
