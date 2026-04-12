"""Application FastAPI : montage des routes, static, lifespan."""

from __future__ import annotations

import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from kimvieware_orchestrator.api.legacy import router as legacy_api_router
from kimvieware_orchestrator.api.v1.router import api_v1_router
from kimvieware_orchestrator.infrastructure.phase_updates_consumer import (
    run_phase_updates_consumer,
)
from kimvieware_orchestrator.paths import get_orchestrator_root
from kimvieware_orchestrator.web.pages import router as web_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    thread = threading.Thread(target=run_phase_updates_consumer, daemon=True)
    thread.start()
    yield


def create_app() -> FastAPI:
    root = get_orchestrator_root()
    application = FastAPI(title="KIMVIEware Orchestrator", lifespan=lifespan)

    static_dir = root / "static"
    if static_dir.is_dir():
        application.mount(
            "/static",
            StaticFiles(directory=str(static_dir)),
            name="static",
        )

    application.include_router(web_router)
    application.include_router(legacy_api_router)
    application.include_router(api_v1_router)

    @application.get("/health")
    def health():
        return {"status": "ok"}

    return application


app = create_app()
