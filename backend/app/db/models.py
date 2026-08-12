"""SQLAlchemy models for the login-gated reading-history feature.

birth_data/synthesis_output are stored as generic JSON (not JSONB) so the
same models work unchanged against SQLite (dev) and Postgres (prod).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    google_sub: Mapped[str] = mapped_column(unique=True, index=True)
    email: Mapped[str] = mapped_column(index=True)
    name: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    readings: Mapped[list[Reading]] = relationship(back_populates="user")


class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    birth_data: Mapped[dict] = mapped_column(JSON)
    synthesis_output: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)

    user: Mapped[User] = relationship(back_populates="readings")
