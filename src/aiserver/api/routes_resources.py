"""Routes for /resources."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from aiserver import resources


router = APIRouter()


@router.get("/resources/{iso}")
async def get_resources_route(iso: str) -> dict[str, Any]:
    try:
        return resources.get_resources(iso)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
