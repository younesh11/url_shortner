from __future__ import annotations

from collections import deque
from threading import Lock
from time import time
from typing import Deque, Dict

from fastapi import HTTPException, Request, status

from app.core.settings import settings

_WINDOW = 60.0  # seconds
_buckets: Dict[str, Deque[float]] = {}
_lock = Lock()

def _now() -> float:
    return time()

def reset() -> None:
    """Test helper: clear all counters."""
    with _lock:
        _buckets.clear()

def key_from_request(request: Request) -> str:

    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"

def allow(key: str, *, limit: int, window: float = _WINDOW) -> bool:
    now = _now()
    with _lock:
        q = _buckets.setdefault(key, deque())

        while q and now - q[0] >= window:
            q.popleft()
        if len(q) >= limit:
            return False
        q.append(now)
        return True

def rate_limit_or_429(request: Request) -> None:
    """FastAPI dependency: raises 429 if over limit."""
    key = key_from_request(request)
    limit = settings.rate_limit_per_min
    if not allow(key, limit=limit, window=_WINDOW):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
        )
