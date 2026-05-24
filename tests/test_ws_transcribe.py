"""WebSocket contract tests for /api/ws/transcribe.

Client → server protocol:
- First message: JSON text `{"lang": "<iso>", "target": "en"|"pt"}`. Server replies
  with `{"ok": true}` or closes on error.
- Subsequent: binary frames, each one a complete PCM chunk (int16 LE, 16 kHz, mono).
  Each frame MAY be preceded by a JSON text frame `{"chunk_id": N, "ms": ...}` —
  optional, used only for echoing chunk_id back.
- Server replies per-binary-frame with JSON `{"chunk_id": N, "transcript": "...",
  "translation": "...", "engine": "...", "covered": bool}`.
"""

from __future__ import annotations

import json
import struct

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    import aiserver.stt as stt_mod
    import aiserver.translate as t_mod

    monkeypatch.setattr(
        stt_mod, "transcribe_array",
        lambda samples, sr, lang_iso: f"CHUNK[{lang_iso},{len(samples)}]",
        raising=False,
    )
    # Also stub legacy transcribe in case the WS handler falls back to file path.
    monkeypatch.setattr(stt_mod, "transcribe", lambda p, lang: f"FILE[{lang}]")
    monkeypatch.setattr(
        t_mod, "_nllb_translate", lambda text, s, t: f"TR[{s}->{t}]:{text}"
    )

    from aiserver.api.app import app

    return TestClient(app)


def _pcm_frame(samples_int16):
    return struct.pack(f"<{len(samples_int16)}h", *samples_int16)


def test_ws_rejects_unknown_lang(client):
    with client.websocket_connect("/api/ws/transcribe") as ws:
        ws.send_json({"lang": "zzz", "target": "en"})
        msg = ws.receive_json()
        assert msg.get("ok") is False
        assert "lang" in msg.get("error", "").lower() or "unknown" in msg.get("error", "").lower()


def test_ws_accepts_known_lang_and_returns_chunk(client):
    with client.websocket_connect("/api/ws/transcribe") as ws:
        ws.send_json({"lang": "sna", "target": "pt"})
        ack = ws.receive_json()
        assert ack.get("ok") is True

        ws.send_bytes(_pcm_frame([0] * 1600))  # 100 ms silence
        msg = ws.receive_json()
        assert "transcript" in msg
        assert "translation" in msg
        assert msg["engine"] in {"nllb", "none", "whisper-translate"}


def test_ws_chunk_id_echoed_when_provided(client):
    with client.websocket_connect("/api/ws/transcribe") as ws:
        ws.send_json({"lang": "sna", "target": "pt"})
        ws.receive_json()
        ws.send_json({"chunk_id": 42})
        ws.send_bytes(_pcm_frame([0] * 1600))
        msg = ws.receive_json()
        assert msg.get("chunk_id") == 42


def test_ws_uncovered_translation_pair(client):
    with client.websocket_connect("/api/ws/transcribe") as ws:
        ws.send_json({"lang": "seh", "target": "en"})  # Sena → English: not covered
        ws.receive_json()
        ws.send_bytes(_pcm_frame([0] * 1600))
        msg = ws.receive_json()
        assert msg["engine"] == "none"
        assert msg["covered"] is False
        assert msg["translation"] == ""
