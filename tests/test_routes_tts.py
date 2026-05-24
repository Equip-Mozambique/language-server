"""Contract tests for POST /api/tts."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch, tmp_path):
    """TestClient with stubbed synthesize so the test doesn't load MMS-TTS."""
    import aiserver.tts as tts_mod

    fake_wav = tmp_path / "fake.wav"
    # Minimal valid RIFF/WAVE header + 16 bytes silence
    fake_wav.write_bytes(
        b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"
        b"\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    )

    def fake_synthesize(text, lang_iso, out_path):
        p = Path(out_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(fake_wav.read_bytes())
        return p

    monkeypatch.setattr(tts_mod, "synthesize", fake_synthesize)
    from aiserver.api.app import app

    return TestClient(app)


def test_tts_returns_wav_for_supported_lang(client):
    r = client.post("/api/tts", json={"lang": "sna", "text": "Mhoroi"})
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("audio/wav")
    assert r.content[:4] == b"RIFF"
    assert len(r.content) > 0


def test_tts_unknown_lang_returns_404(client):
    r = client.post("/api/tts", json={"lang": "zzz", "text": "hi"})
    assert r.status_code == 404


def test_tts_lang_without_mms_tts_returns_400(client):
    """Ndau has no mms_tts model in the registry."""
    r = client.post("/api/tts", json={"lang": "ndc", "text": "Mhoroi"})
    assert r.status_code in {400, 422, 501}


def test_tts_missing_text_returns_422(client):
    r = client.post("/api/tts", json={"lang": "sna"})
    assert r.status_code == 422


def test_tts_empty_text_returns_422(client):
    r = client.post("/api/tts", json={"lang": "sna", "text": ""})
    assert r.status_code == 422


def test_tts_text_too_long_returns_413(client):
    r = client.post("/api/tts", json={"lang": "sna", "text": "x" * 10_000})
    assert r.status_code == 413
