"""FastAPI application entry point."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI


def _preload() -> None:
    from aiserver.stt import _mms, _whisper  # noqa: F401 - cache-warming
    _whisper()
    _mms()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.environ.get("AISERVER_PRELOAD_MODELS") == "1":
        _preload()
    yield


app = FastAPI(title="ai-server", lifespan=lifespan)

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
