"""Contract tests for POST /api/transcribe."""

from __future__ import annotations

import io
import wave

import numpy as np
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    """TestClient with stubbed STT + translate so unit tests skip real model loads."""
    import aiserver.stt as stt_mod
    import aiserver.translate as t_mod

    monkeypatch.setattr(stt_mod, "transcribe", lambda audio, lang_iso: f"FAKE_TRANSCRIPT[{lang_iso}]")
    monkeypatch.setattr(
        t_mod,
        "_nllb_translate",
        lambda text, src_flores, tgt_flores: f"FAKE_NLLB[{src_flores}->{tgt_flores}]:{text}",
    )

    from aiserver.api.app import app

    return TestClient(app)


def _silent_wav_bytes(duration_s: float = 0.5, sr: int = 16000) -> bytes:
    """Make a tiny silent WAV in memory."""
    n = int(duration_s * sr)
    samples = np.zeros(n, dtype=np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(samples.tobytes())
    return buf.getvalue()


def test_transcribe_returns_transcript_and_translation_for_supported(client):
    wav = _silent_wav_bytes()
    r = client.post(
        "/api/transcribe?lang=sna&target=pt",
        files={"audio": ("clip.wav", wav, "audio/wav")},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["lang"] == "sna"
    assert data["target"] == "pt"
    assert data["transcript"] == "FAKE_TRANSCRIPT[sna]"
    assert data["translation"]
    assert data["engine"] == "nllb"
    assert data["covered"] is True


def test_transcribe_uncovered_translation_returns_empty_translation(client):
    """Sena has no NLLB and no Whisper-translate. Transcript only."""
    wav = _silent_wav_bytes()
    r = client.post(
        "/api/transcribe?lang=seh&target=en",
        files={"audio": ("clip.wav", wav, "audio/wav")},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["transcript"] == "FAKE_TRANSCRIPT[seh]"
    assert data["translation"] == ""
    assert data["engine"] == "none"
    assert data["covered"] is False


def test_transcribe_unknown_lang_returns_400(client):
    wav = _silent_wav_bytes()
    r = client.post(
        "/api/transcribe?lang=zzz&target=en",
        files={"audio": ("clip.wav", wav, "audio/wav")},
    )
    assert r.status_code in {400, 404, 422}


def test_transcribe_invalid_target_returns_422(client):
    wav = _silent_wav_bytes()
    r = client.post(
        "/api/transcribe?lang=sna&target=fr",
        files={"audio": ("clip.wav", wav, "audio/wav")},
    )
    assert r.status_code == 422


def test_transcribe_missing_audio_returns_422(client):
    r = client.post("/api/transcribe?lang=sna&target=en")
    assert r.status_code == 422
