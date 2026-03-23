"""
Application entry point for the Postgres AI Copilot API.

This module creates the FastAPI application, registers routes, and exposes
basic service-level endpoints such as health checks.
"""

from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(title="Postgres AI Copilot", version="0.1.0")
app.include_router(router)


@app.get("/health")
def health() -> dict[str, str]:
    """Return a simple health-check response for local development and tooling."""
    return {"status": "ok"}