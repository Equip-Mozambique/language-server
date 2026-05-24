"""Routes for /languages."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from aiserver.languages import LANGS, get, resolve

router = APIRouter()


class LangResponse(BaseModel):
    iso: str
    name: str
    country: str
    mms_iso: str | None
    mms_tts: str | None
    whisper_code: str | None
    preferred_stt: str
    preferred_tts: str
    proxy_iso: str | None
    effective_iso: str
    status: str


def _to_response(lang) -> LangResponse:
    eff, status = resolve(lang.iso)
    return LangResponse(
        iso=lang.iso,
        name=lang.name,
        country=lang.country,
        mms_iso=lang.mms_iso,
        mms_tts=lang.mms_tts,
        whisper_code=lang.whisper_code,
        preferred_stt=lang.preferred_stt,
        preferred_tts=lang.preferred_tts,
        proxy_iso=lang.proxy_iso,
        effective_iso=eff,
        status=status,
    )


@router.get("/languages", response_model=list[LangResponse])
async def list_languages() -> list[LangResponse]:
    return [_to_response(LANGS[k]) for k in sorted(LANGS)]


@router.get("/languages/{iso}", response_model=LangResponse)
async def get_language(iso: str) -> LangResponse:
    try:
        lang = get(iso)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _to_response(lang)
