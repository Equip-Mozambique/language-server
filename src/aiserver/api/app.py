"""FastAPI application entry point."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response
from starlette.types import Scope


class SPAStaticFiles(StaticFiles):
    """StaticFiles that falls back to index.html for unknown paths (SPA routes)."""

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as e:
            if e.status_code == 404:
                return await super().get_response("index.html", scope)
            raise


def _preload() -> None:
    from aiserver.stt import _mms, _whisper  # noqa: F401 - cache-warming
    _whisper()
    _mms()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.environ.get("AISERVER_PRELOAD_MODELS") == "1":
        _preload()
    yield


app = FastAPI(title="BatePapo", lifespan=lifespan)

from .routes_langs import router as langs_router  # noqa: E402
from .routes_stt import router as stt_router  # noqa: E402
from .routes_tts import router as tts_router  # noqa: E402
from .routes_uploads import router as uploads_router  # noqa: E402
from .routes_resources import router as resources_router  # noqa: E402

app.include_router(langs_router, prefix="/api")
app.include_router(stt_router, prefix="/api")
app.include_router(tts_router, prefix="/api")
app.include_router(uploads_router, prefix="/api")
app.include_router(resources_router, prefix="/api")


def _frontend_dir() -> Path | None:
    """Resolve the Angular static-build directory if present."""
    env = os.environ.get("AISERVER_FRONTEND_DIR")
    if env:
        p = Path(env)
        return p if p.exists() else None
    candidates = [
        Path(__file__).resolve().parents[3] / "frontend" / "dist" / "frontend" / "browser",
        Path(__file__).resolve().parents[3] / "frontend" / "dist" / "ai-server" / "browser",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


_static = _frontend_dir()
if _static is not None:
    app.mount("/", SPAStaticFiles(directory=str(_static), html=True), name="frontend")
