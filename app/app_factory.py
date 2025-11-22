from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router as employees_router
from .db import init_db


def create_app() -> FastAPI:
    init_db()

    app = FastAPI(title="Leave Management API (FastAPI + FastMCP + SQLite + Basic Auth)")

    # CORS (relax for dev; tighten for prod)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(employees_router)

    return app
