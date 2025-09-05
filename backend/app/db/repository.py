# backend/app/db/repository.py
from __future__ import annotations

from typing import Optional

import sqlalchemy as sa
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.link import Link


class DuplicateCodeError(Exception):
    """Raised when short_code is already taken (unique constraint)."""


# --- Internal helpers -------------------------------------------------------

def _is_unique_violation(e: IntegrityError, *, column_hint: str = "short_code") -> bool:
    """
    Best-effort detection of a UNIQUE constraint violation for the given column.
    Works for SQLite and (most) Postgres messages without driver-specific deps.
    """
    msg = (str(getattr(e, "orig", e)) or "").lower()

    # SQLite: "UNIQUE constraint failed: links.short_code"
    if "unique" in msg and column_hint in msg:
        return True

    # Postgres: "duplicate key value violates unique constraint 'links_short_code_key'"
    if "duplicate key value violates unique constraint" in msg and column_hint in msg:
        return True

    return False


# --- Create -----------------------------------------------------------------

def create_link(
    db: Session,
    *,
    short_code: str,
    long_url: str,
    is_custom_alias: bool = False,
    expires_at: Optional[object] = None,  # datetime | None; kept loose for SQLite leniency
) -> Link:
    """
    Insert a new link row.
    Commits on success, raises DuplicateCodeError on short_code conflict,
    re-raises other integrity errors.
    """
    link = Link(
        short_code=short_code,
        long_url=long_url,
        is_custom_alias=is_custom_alias,
        expires_at=expires_at,
    )
    db.add(link)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        if _is_unique_violation(e, column_hint="short_code"):
            raise DuplicateCodeError(f"short_code '{short_code}' is already taken")
        raise
    db.refresh(link)
    return link


# --- Read -------------------------------------------------------------------

def get_link_by_code(db: Session, code: str) -> Optional[Link]:
    """
    Fetch by short_code. With SQLite's NOCASE collation on the column,
    equality here is case-insensitive and uses the index.
    """
    stmt = select(Link).where(Link.short_code == code).limit(1)
    return db.execute(stmt).scalars().first()


def get_active_link_by_code(db: Session, code: str) -> Optional[Link]:
    """
    Fetch only if not expired (expires_at is NULL or > CURRENT_TIMESTAMP).
    Uses DB-side time for portability.
    """
    not_expired = sa.or_(Link.expires_at.is_(None), Link.expires_at > func.current_timestamp())
    stmt = select(Link).where(Link.short_code == code, not_expired).limit(1)
    return db.execute(stmt).scalars().first()


def code_exists(db: Session, code: str) -> bool:
    """Fast existence check (case-insensitive on SQLite due to column collation)."""
    stmt = select(sa.literal(True)).where(Link.short_code == code).limit(1)
    return db.execute(stmt).scalar() is True


# --- Update -----------------------------------------------------------------

def increment_click_count(db: Session, code: str) -> int:
    """
    Atomically increment click_count for a code.
    Returns number of rows updated (0 if code not found).
    """
    stmt = (
        update(Link)
        .where(Link.short_code == code)
        .values(click_count=Link.click_count + 1)
    )
    res = db.execute(stmt)
    db.commit()
    return int(res.rowcount or 0)


# --- Maintenance / cleanup ---------------------------------------------------

def delete_expired_links(db: Session) -> int:
    """
    Delete rows with expires_at <= CURRENT_TIMESTAMP.
    Returns number of rows deleted.
    """
    stmt = delete(Link).where(
        Link.expires_at.is_not(None),
        Link.expires_at <= func.current_timestamp(),
    )
    res = db.execute(stmt)
    db.commit()
    return int(res.rowcount or 0)
