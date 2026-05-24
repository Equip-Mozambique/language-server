"""Routes for /uploads: corpus ingest and listing."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from aiserver import corpus
from aiserver.languages import LANGS


router = APIRouter()

MAX_UPLOAD_BYTES = 500 * 1024 * 1024  # 500 MB


@router.post("/uploads", status_code=201)
async def create_upload(
    iso: str = Form(...),
    audio: UploadFile = File(...),
    filename_orig: str | None = Form(default=None),
    media_type: str | None = Form(default=None),
    speaker_id: str | None = Form(default=None),
    dialect: str | None = Form(default=None),
    register: str | None = Form(default=None),
    license: str | None = Form(default=None),
    transcript: str | None = Form(default=None),
) -> JSONResponse:
    if iso not in LANGS:
        raise HTTPException(status_code=404, detail=f"Unknown language: {iso}")

    payload = await audio.read()
    if not payload:
        raise HTTPException(status_code=422, detail="empty audio payload")
    if len(payload) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="upload too large")

    meta: dict[str, Any] = {
        "filename_orig": filename_orig or audio.filename,
        "media_type": media_type or audio.content_type,
        "speaker_id": speaker_id,
        "dialect": dialect,
        "register": register,
        "license": license,
        "transcript": transcript,
    }
    try:
        row = corpus.add_upload(iso, payload, meta)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return JSONResponse(content=row, status_code=201)


@router.get("/uploads/{iso}")
async def list_uploads_route(iso: str) -> list[dict[str, Any]]:
    if iso not in LANGS:
        raise HTTPException(status_code=404, detail=f"Unknown language: {iso}")
    return corpus.list_uploads(iso)
