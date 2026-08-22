"""SQLAlchemy models for the login-gated reading-history feature, plus
each user's remembered birth data (see User.birth_* below).

birth_data/synthesis_output are stored as generic JSON (not JSONB) so the
same models work unchanged against SQLite (dev) and Postgres (prod).

Base.metadata.create_all() (called at startup, app/main.py's lifespan)
only creates *missing* tables — it never alters an existing one. The
User.birth_* columns below were added after `users` already existed in
production, so app/db/session.py's ensure_user_birth_data_columns() runs
right after create_all() to backfill them onto any table that predates
this feature. A freshly created table already has them from this model
definition, so that step is a no-op there (fresh dev DB, or the test
suite's `client` fixture).
"""

from __future__ import annotations

from datetime import date, datetime
from datetime import time as dt_time

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

    # Remembered birth data — set from the most recent /api/reading that
    # included birth_data, so a returning user doesn't have to re-enter it
    # every time (see GET/DELETE /api/profile/birth-data in main.py). This
    # is a per-user profile fact the user explicitly typed in, not the
    # "browsing/session history" CLAUDE.md's privacy rule is about — that
    # rule bars feeding *past readings' content* back into a new reading's
    # interpretation, not remembering a fact (a birthday) that never
    # changes. All nullable: a user may never have submitted birth data
    # (oracle-only readings), or may have asked to forget it.
    birth_date: Mapped[date | None] = mapped_column(default=None)
    birth_time: Mapped[dt_time | None] = mapped_column(default=None)
    birth_place: Mapped[str | None] = mapped_column(default=None)
    birth_latitude: Mapped[float | None] = mapped_column(default=None)
    birth_longitude: Mapped[float | None] = mapped_column(default=None)
    birth_timezone: Mapped[str | None] = mapped_column(default=None)

    readings: Mapped[list[Reading]] = relationship(back_populates="user")


class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    # Nullable since a reading may skip Uranian entirely (oracle-only, or
    # oracle+tarot with no birth data) — see CLAUDE.md's per-discipline
    # skip buttons, and /api/reading/follow-up, which never has birth data.
    birth_data: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=None)
    synthesis_output: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)

    user: Mapped[User] = relationship(back_populates="readings")
