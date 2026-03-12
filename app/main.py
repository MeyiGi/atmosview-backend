"""
main.py

Application entrypoint.

Responsibilities:
  1. Create and configure the FastAPI application.
  2. Build the DI container on startup and attach it to app.state.
  3. Run DB migrations (create tables) on first boot.
  4. Register routers and exception handlers.
  5. Nothing else.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.config.settings import get_settings
from app.infrastructure.container import build_container
from app.infrastructure.persistence.database import get_engine
from app.infrastructure.persistence.models.request_log import Base
from app.presentation.exception_handlers import register_exception_handlers
from app.presentation.routers import logs, weather, wrf

logging.basicConfig(
    level=get_settings().LOG_LEVEL,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup ---
    app.state.container = build_container()
    Base.metadata.create_all(bind=get_engine())
    yield
    # --- shutdown (nothing to clean up yet) ---


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=(
            "REST API for meteorological data visualisation.\n\n"
            "Reads GRIB and WRF output files, clips to Central Asia, "
            "and returns rendered PNG maps."
        ),
        lifespan=lifespan,
        docs_url="/",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(weather.router)
    app.include_router(wrf.router)
    app.include_router(logs.router)

    return app


app = create_app()
