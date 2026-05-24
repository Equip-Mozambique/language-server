"""Routes for /tts."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from aiserver import tts
from aiserver.languages import get


router = APIRouter()

MAX_TEXT_LEN = 4000


class TTSRequest(BaseModel):
    lang: str = Field(min_length=2, max_length=8)
    text: str = Field(min_length=1)
    voice: str | None = None


@router.post("/tts")
async def synthesize(req: TTSRequest):
    try:
        lang = get(req.lang)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown language: {req.lang}")

    if len(req.text) > MAX_TEXT_LEN:
        raise HTTPException(status_code=413, detail="text too long")

    if lang.mms_tts is None:
        raise HTTPException(status_code=400, detail=f"No MMS-TTS model for {req.lang}")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        out_path = Path(tmp.name)

    tts.synthesize(req.text, req.lang, out_path)

    return FileResponse(
        path=str(out_path),
        media_type="audio/wav",
        filename=f"{req.lang}.wav",
    )
