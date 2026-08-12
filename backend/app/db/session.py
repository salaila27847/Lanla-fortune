"""Async SQLAlchemy engine/session setup.

DATABASE_URL is expected in its plain form (what Neon/dev give you directly,
e.g. `postgresql://...` or `sqlite:///./dev.db`) — _normalize_async_url()
rewrites it to the async-driver form so nobody has to hand-edit it.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def _normalize_async_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://") :]
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://") :]
    if url.startswith("sqlite://") and "+" not in url.split("://", 1)[0]:
        return "sqlite+aiosqlite://" + url[len("sqlite://") :]
    return url


DATABASE_URL = _normalize_async_url(os.environ.get("DATABASE_URL") or "sqlite:///./dev.db")

engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:
        yield session
