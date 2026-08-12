"""Shared fixtures for HTTP-level tests (auth + reading persistence).

Sets safe env defaults *before* app.main (and its module-level DB engine)
gets imported by any test module, since app.db.session reads DATABASE_URL
at import time.
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("INTERNAL_API_SECRET", "test-internal-secret")
os.environ.setdefault("GEMINI_API_KEY", "test-key")

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.models import Base
from app.db.session import get_db_session
from app.main import app


@pytest.fixture
async def client():
    # Dedicated in-memory engine per test, isolated from whatever the app's
    # own module-level engine points at. StaticPool is required — plain
    # in-memory SQLite gives each new connection its own empty DB otherwise,
    # so the fixture and the overridden dependency would silently diverge.
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(test_engine, expire_on_commit=False)

    async def override_get_db_session():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    await test_engine.dispose()
