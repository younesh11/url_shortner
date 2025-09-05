# backend/app/services/url_service.py
from __future__ import annotations

import re
import secrets
from datetime import datetime, timezone
from typing import Optional, Tuple
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db import repository as repo
from app.db.repository import DuplicateCodeError
from app.models.link import Link




class InvalidURLError(ValueError):
    pass


class InvalidAliasError(ValueError):
    pass


class AliasTakenError(ValueError):
    pass


class RetryExhaustedError(RuntimeError):
    pass



_ALIAS_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{2,29}$")


_GEN_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789"


_RESERVED_ALIASES = {
    "api",
    "health",
    "docs",
    "openapi.json",
    "redoc",
    "favicon.ico",
    "static",
    "metrics",
}


def _as_aware_utc(dt: datetime) -> datetime:
    """Normalize any datetime to timezone-aware UTC (treat naive as UTC)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def normalize_url(url: str, *, max_len: int = 2048) -> str:
    """
    Trim and normalize a URL.
    - If scheme missing, default to https://
    - Only allow http/https
    - Enforce a reasonable max length
    """
    if not isinstance(url, str):
        raise InvalidURLError("URL must be a string")

    u = url.strip()
    if not u:
        raise InvalidURLError("URL is required")


    parsed = urlparse(u)
    if not parsed.scheme:
        u = "https://" + u
        parsed = urlparse(u)

    if parsed.scheme not in {"http", "https"}:
        raise InvalidURLError("Only http and https URLs are allowed")

    if not parsed.netloc:
        raise InvalidURLError("URL must include a host")

    if len(u) > max_len:
        raise InvalidURLError("URL is too long")

    return u


def is_reserved_alias(alias: str) -> bool:
    return alias.lower() in _RESERVED_ALIASES


def validate_alias(alias: str) -> str:
    """
    Validate user-provided alias:
    - lowercase, match pattern, not reserved
    Returns canonical (lowercased) alias.
    """
    if alias is None:
        raise InvalidAliasError("Alias is required")
    a = alias.strip().lower()
    if not _ALIAS_RE.fullmatch(a):
        raise InvalidAliasError(
            "Alias must be 3–30 chars: letters, digits, '_' or '-' (start with letter/digit)"
        )
    if is_reserved_alias(a):
        raise InvalidAliasError("This alias is reserved")
    return a


def generate_code(length: int | None = None) -> str:
    """
    Generate a random short code using allowed characters.
    """
    n = length or settings.short_code_length
    return "".join(secrets.choice(_GEN_CHARS) for _ in range(n))


def build_short_url(base_url: str, code: str) -> str:
    """
    Compose a short URL using a base URL (e.g., str(request.base_url)).
    """
    base = base_url.rstrip("/")
    return f"{base}/{code}"




def create_short_link(
    db: Session,
    *,
    url: str,
    alias: Optional[str] = None,
    expires_at: Optional[datetime] = None,
) -> Tuple[str, Link]:
    """
    Core create flow:
      - normalize+validate URL
      - if alias provided: validate and insert (409 on conflict)
      - else: generate code, retry on conflict up to a small limit
    Returns (code, Link)
    """
    norm_url = normalize_url(url)

    # Normalize & validate expiry (must be future; compare in UTC)
    if expires_at is not None:
        expires_at = _as_aware_utc(expires_at)
        if expires_at <= datetime.now(timezone.utc):
            raise InvalidURLError("Expiry must be in the future")

    if alias:
        code = validate_alias(alias)
        try:
            link = repo.create_link(
                db,
                short_code=code,
                long_url=norm_url,
                is_custom_alias=True,
                expires_at=expires_at,
            )
        except DuplicateCodeError as _:
            raise AliasTakenError("Alias already taken")
        return code, link


    max_retries = 6
    last_err: Exception | None = None
    for _ in range(max_retries):
        code = generate_code(settings.short_code_length)
        if is_reserved_alias(code):
            continue  
        try:
            link = repo.create_link(
                db,
                short_code=code,
                long_url=norm_url,
                is_custom_alias=False,
                expires_at=expires_at,
            )
            return code, link
        except DuplicateCodeError as e:
            last_err = e
            continue

    raise RetryExhaustedError("Could not generate a unique short code; try again")


def resolve(
    db: Session,
    *,
    code: str,
) -> dict:
    """
    Resolve metadata for a code without redirecting.
    Returns: {exists: bool, expired: bool, long_url?: str}
    """

    link = repo.get_link_by_code(db, code)
    if not link:
        return {"exists": False, "expired": False}

    now = datetime.now(timezone.utc)
    expired = False
    if link.expires_at:
        exp = _as_aware_utc(link.expires_at)
        expired = exp <= now

    payload = {"exists": True, "expired": expired}
    if not expired:
        payload["long_url"] = link.long_url  
    return payload


def lookup_active_for_redirect(db: Session, *, code: str) -> Optional[Link]:
    """
    Fetch only if the link exists and is not expired (used by redirect route).
    """
    return repo.get_active_link_by_code(db, code)
