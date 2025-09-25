from __future__ import annotations

from fastapi import FastAPI

from . import auth, health, ingest, jobs, webhooks


def register_routes(app: FastAPI) -> None:
    app.include_router(auth.router)
    app.include_router(health.router)
    app.include_router(ingest.router)
    app.include_router(jobs.router)
    app.include_router(webhooks.router)
