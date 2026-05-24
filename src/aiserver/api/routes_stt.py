"""Routes for /transcribe (file POST) and /ws/transcribe (live chunks; TBD)."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from aiserver import stt, translate
from aiserver.languages import get


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
