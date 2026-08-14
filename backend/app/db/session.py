"""Async SQLAlchemy engine/session setup.

DATABASE_URL is expected in its plain form (what Neon/dev give you directly,
e.g. `postgresql://...?sslmode=require` or `sqlite:///./dev.db`) —
_normalize_async_url() rewrites it to the async-driver form so nobody has to
hand-edit it.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# libpq-style query params (Neon includes these by default) that asyncpg's
# connect() doesn't accept as keyword arguments the way psycopg does —
# SQLAlchemy forwards unrecognized URL query params verbatim, so leaving
# these in blows up with "connect() got an unexpected keyword argument
# 'sslmode'". sslmode still needs honoring, just via asyncpg's `ssl` connect
# arg instead of a URL query param.
_ASYNCPG_UNSUPPORTED_QUERY_PARAMS = {"sslmode", "channel_binding"}


def _normalize_async_url(url: str) -> tuple[str, dict[str, str]]:
    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://") :]
    elif url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://") :]
    elif url.startswith("sqlite://") and "+" not in url.split("://", 1)[0]:
        return "sqlite+aiosqlite://" + url[len("sqlite://") :], {}
    else:
        return url, {}

    parts = urlsplit(url)
    connect_args: dict[str, str] = {}
    kept_params = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key == "sslmode":
            connect_args["ssl"] = value
        elif key in _ASYNCPG_UNSUPPORTED_QUERY_PARAMS:
            continue
        else:
            kept_params.append((key, value))
    url = urlunsplit(parts._replace(query=urlencode(kept_params)))
    return url, connect_args


DATABASE_URL, _connect_args = _normalize_async_url(
    os.environ.get("DATABASE_URL") or "sqlite:///./dev.db"
)

engine = create_async_engine(
    DATABASE_URL,
    connect_args=_connect_args,
    pool_pre_ping=True,
    pool_recycle=300,
)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:
        yield session
