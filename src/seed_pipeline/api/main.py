"""FastAPI application factory.

This module defines the FastAPI app used to serve the seed pipeline
APIs.  It includes a simple health check endpoint and mounts the
routers defined in the `routers` subpackage.  CORS is enabled for
development convenience; adjust the allowed origins as appropriate for
production.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import seeds


def create_app() -> FastAPI:
    app = FastAPI(title="Seed Pipeline API")
    # Enable CORS for all origins in development; restrict in prod
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz")
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    # Include routers
    app.include_router(seeds.router)
    return app


app = create_app()