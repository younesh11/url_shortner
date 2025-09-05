# backend/app/main.py
from __future__ import annotations

import logging
import os
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import settings
from app.api import api_router


def _allowed_origins() -> list[str]:
    csv = os.getenv("ALLOWED_ORIGINS")
    if csv:
        return [o.strip() for o in csv.split(",") if o.strip()]

    one = os.getenv("FRONTEND_ORIGIN")
    if one:
        return [one]

    if settings.env == "dev":
        return ["http://localhost:8501"]
    if settings.env == "test":
        return ["http://localhost", "http://testserver", "http://localhost:8501"]
    return []  # prod: same-origin unless explicitly set via env


app = FastAPI(title="URL Shortener API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_logger = logging.getLogger("uvicorn.access")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    # keep duration as a header; uvicorn formatter won’t log it anyway
    response.headers["X-Process-Time-ms"] = f"{(time.monotonic() - start) * 1000:.2f}"

    client = request.client.host if request.client else "-"
    http_version = request.scope.get("http_version", "HTTP/1.1")

    _logger.info('%s - "%s %s %s" %s',
                 client, request.method, request.url.path, http_version, response.status_code)
    return response



app.include_router(api_router)
