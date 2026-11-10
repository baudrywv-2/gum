"""GUM FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import check_database_connection
from app.routers import evidence, health, opportunities, providers


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    if settings.check_db_on_startup:
        check_database_connection()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="GUM API",
        description=(
            "Opportunity Intelligence Engine — Milestone 4 opportunity discovery "
            "(recurring problems, clusters, themes, underserved audiences, "
            "cross-source correlation; mock providers; labeled claims; no fabricated demand)."
        ),
        version="0.4.0",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(health.router)
    application.include_router(providers.router)
    application.include_router(evidence.router)
    application.include_router(opportunities.router)
    return application


app = create_app()
