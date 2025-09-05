# backend/app/db/session.py
from __future__ import annotations

from contextlib import contextmanager
from threading import Lock
from typing import Iterator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.settings import settings


class Base(DeclarativeBase):
    """Base for all ORM models (e.g., class Link(Base): ...)."""
    pass


class Database:
    """
     Wrapper around SQLAlchemy engine + sessions.

    - Lazy initialization (no connection until first use)
    - Thread-safe engine/session creation
    - Per-request dependency: db.get_db
    - Dev helpers: db.create_all(), db.ping(), db.dispose()
    """

    def __init__(self, url: str) -> None:
        self.url = url
        self._engine = None
        self._SessionLocal: Optional[sessionmaker[Session]] = None
        self._lock = Lock()

    # ----- internal helpers -----
    def _connect_args(self) -> dict:
        # SQLite needs this flag for multithreaded servers
        return {"check_same_thread": False} if self.url.startswith("sqlite") else {}

    def _init_if_needed(self) -> None:
        if self._engine is None:
            with self._lock:
                if self._engine is None:  # double-checked locking
                    engine = create_engine(
                        self.url,
                        future=True,
                        pool_pre_ping=True,
                        connect_args=self._connect_args(),
                    )
                    SessionLocal = sessionmaker(
                        bind=engine,
                        class_=Session,
                        autoflush=False,
                        autocommit=False,
                        future=True,
                    )
                    self._engine = engine
                    self._SessionLocal = SessionLocal

    # ----- public properties -----
    @property
    def engine(self):
        self._init_if_needed()
        return self._engine

    @property
    def SessionLocal(self) -> sessionmaker[Session]:
        self._init_if_needed()
        assert self._SessionLocal is not None  # for type-checkers
        return self._SessionLocal

    # ----- usage patterns -----
    @contextmanager
    def session(self) -> Iterator[Session]:
        """
        Context-managed session:
            with db.session() as s:
                ...
        """
        s = self.SessionLocal()
        try:
            yield s
        finally:
            s.close()

    def get_db(self) -> Iterator[Session]:
        """
        FastAPI dependency:
            def endpoint(db: Session = Depends(db.get_db)): ...
        """
        s = self.SessionLocal()
        try:
            yield s
        finally:
            s.close()

    # ----- ops/helpers -----
    def ping(self) -> None:
        """Raise if DB is unreachable."""
        with self.engine.connect() as conn:
            conn.execute(text("SELECT 1"))

    def create_all(self) -> None:
        """Dev/Test convenience: create tables for all ORM models."""
        Base.metadata.create_all(bind=self.engine)

    def dispose(self) -> None:
        """Close all pooled connections (e.g., on shutdown)."""
        if self._engine is not None:
            self._engine.dispose()


# App-wide singleton (configured from validated settings)
db = Database(settings.database_url)

# Optional convenience re-exports (importable in other modules)
get_db = db.get_db
