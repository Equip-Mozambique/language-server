"""Routes for /readiness."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from aiserver import readiness
from aiserver.languages import LANGS


router = APIRouter()


@router.get("/readiness/{iso}")
async def get_readiness_route(iso: str) -> dict[str, Any]:
    try:
        reports = readiness.readiness_all(iso)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    out = {axis: r.as_dict() for axis, r in reports.items()}
    out["overall"] = readiness.overall_score(reports)
    return out


@router.get("/readiness")
async def list_readiness_route() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for iso, lang in LANGS.items():
        try:
            reports = readiness.readiness_all(iso)
        except Exception as e:
            out.append({"iso": iso, "name": lang.name, "error": str(e)})
            continue
        out.append({
            "iso": iso,
            "name": lang.name,
            "country": lang.country,
            "overall": readiness.overall_score(reports),
            "asr": reports["asr"].as_dict(),
            "tts": reports["tts"].as_dict(),
            "text": reports["text"].as_dict(),
        })
    return out
