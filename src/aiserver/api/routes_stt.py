"""Routes for /transcribe (file POST) and /ws/transcribe (live chunks)."""

from __future__ import annotations

import struct
import tempfile
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from aiserver import stt, translate
from aiserver.languages import LANGS, get


router = APIRouter()

MAX_AUDIO_BYTES = 200 * 1024 * 1024  # 200 MB
ALLOWED_TARGETS = {"en", "pt"}


class TranscribeResponse(BaseModel):
    lang: str
    target: str
    transcript: str
    translation: str
    engine: str
    covered: bool


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_file(
    lang: str = Query(..., min_length=2, max_length=8),
    target: Literal["en", "pt"] = Query(...),
    audio: UploadFile = File(...),
) -> TranscribeResponse:
    """Transcribe an uploaded audio file in `lang`, translate to `target`."""

    try:
        get(lang)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown language: {lang}")

    contents = await audio.read()
    if len(contents) == 0:
        raise HTTPException(status_code=422, detail="empty audio payload")
    if len(contents) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="audio too large")

    suffix = Path(audio.filename or "audio.wav").suffix or ".wav"
    if suffix not in {".wav", ".mp3", ".flac", ".ogg", ".webm", ".m4a"}:
        suffix = ".wav"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = Path(tmp.name)

    try:
        transcript = stt.transcribe(tmp_path, lang)
    finally:
        tmp_path.unlink(missing_ok=True)

    # Translation. For text-only path, never use whisper-translate (it needs audio).
    # If whisper-translate plan is chosen, future refactor will re-run Whisper on the
    # audio with task="translate"; for v1 we fall through to NLLB or none.
    plan = translate.plan_translation(lang, target)
    if plan["engine"] == "whisper-translate":
        # text-level fallback for v1
        out = translate.translate_text(transcript, lang, target)
    else:
        out = translate.translate_text(transcript, lang, target)

    return TranscribeResponse(
        lang=lang,
        target=target,
        transcript=transcript,
        translation=out["text"],
        engine=out["engine"],
        covered=out["covered"],
    )


def _pcm_le16_to_float32(pcm: bytes):
    """Decode signed-16-bit little-endian PCM bytes to float32 in [-1, 1]."""
    import numpy as np

    if not pcm:
        return np.zeros(0, dtype="float32")
    n = len(pcm) // 2
    samples = struct.unpack(f"<{n}h", pcm[: n * 2])
    arr = np.asarray(samples, dtype="float32") / 32768.0
    return arr


@router.websocket("/ws/transcribe")
async def ws_transcribe(ws: WebSocket) -> None:
    """Receive PCM-int16 chunks at 16 kHz; reply per-chunk transcript + translation."""
    await ws.accept()

    # Handshake — first message must be JSON with lang + target.
    try:
        cfg = await ws.receive_json()
    except (ValueError, WebSocketDisconnect):
        await ws.close(code=1003)
        return

    lang_iso = cfg.get("lang", "")
    target = cfg.get("target", "en")

    if lang_iso not in LANGS:
        await ws.send_json({"ok": False, "error": f"unknown lang: {lang_iso}"})
        await ws.close(code=1008)
        return
    if target not in {"en", "pt"}:
        await ws.send_json({"ok": False, "error": f"invalid target: {target}"})
        await ws.close(code=1008)
        return

    await ws.send_json({"ok": True, "lang": lang_iso, "target": target})

    pending_chunk_id: int | None = None

    try:
        while True:
            msg = await ws.receive()
            if msg.get("type") == "websocket.disconnect":
                break
            if "text" in msg and msg["text"] is not None:
                # Optional JSON envelope for the next binary frame.
                try:
                    envelope = __import__("json").loads(msg["text"])
                    pending_chunk_id = envelope.get("chunk_id")
                except Exception:
                    pending_chunk_id = None
                continue
            if "bytes" in msg and msg["bytes"] is not None:
                samples = _pcm_le16_to_float32(msg["bytes"])
                try:
                    transcript = stt.transcribe_array(samples, 16_000, lang_iso)
                except Exception as e:
                    await ws.send_json(
                        {"chunk_id": pending_chunk_id, "error": f"stt_failed: {e}"}
                    )
                    pending_chunk_id = None
                    continue
                out = translate.translate_text(transcript, lang_iso, target)
                await ws.send_json(
                    {
                        "chunk_id": pending_chunk_id,
                        "transcript": transcript,
                        "translation": out["text"],
                        "engine": out["engine"],
                        "covered": out["covered"],
                    }
                )
                pending_chunk_id = None
    except WebSocketDisconnect:
        return
