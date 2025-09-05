from __future__ import annotations

from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Link(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)

    # Case-insensitive in SQLite so `Home` and `home` collide (good).
    short_code: Mapped[str] = mapped_column(
        sa.String(64, collation="NOCASE"),
        nullable=False,
        unique=True,
        index=True,
    )

    long_url: Mapped[str] = mapped_column(sa.Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.text("CURRENT_TIMESTAMP"),  # UTC in SQLite
        nullable=False,
    )

    expires_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)

    is_custom_alias: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.text("0")
    )

    click_count: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default=sa.text("0")
    )
