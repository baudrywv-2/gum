"""GUM FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import check_database_connection
from app.routers import evidence, formats, gaps, health, opportunities, providers, reports


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
            "Opportunity Intelligence Engine — Milestone 8 web dashboard "
            "(discovery-first SaaS UI wired to the shared API)."
        ),
        version="0.8.0",
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
    application.include_router(gaps.router)
    application.include_router(formats.router)
    application.include_router(reports.router)
    return application


app = create_app()
