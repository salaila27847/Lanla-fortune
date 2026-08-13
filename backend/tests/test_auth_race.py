"""Regression test for a race in get_current_user() found while manually
testing /api/forecast: the frontend fires /api/reading and /api/forecast
at once (Promise.all), so for a brand-new user both requests' first-ever
get_current_user() calls can race to INSERT the same google_sub. Uses a
temp-file SQLite DB (not :memory:) so the two sessions are genuinely
independent connections — a shared StaticPool connection can't hold two
concurrent transactions and wouldn't reproduce the real race.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.auth import get_current_user
from app.db.models import Base, User


@pytest.fixture
async def session_maker(tmp_path):
    db_path = tmp_path / "race_test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


async def test_get_current_user_recovers_from_concurrent_insert_race(session_maker, monkeypatch):
    """Simulates the exact interleaving: our session's SELECT finds no
    user yet, then — before we flush our own INSERT — a concurrent
    request commits the same brand-new user through a separate
    connection, so our flush hits a real UNIQUE constraint conflict."""
    async with session_maker() as session:
        original_execute = session.execute
        state = {"select_seen": False}

        async def execute_then_let_other_request_win(*args, **kwargs):
            result = await original_execute(*args, **kwargs)
            if not state["select_seen"]:
                state["select_seen"] = True
                async with session_maker() as winner_session:
                    winner_session.add(
                        User(google_sub="race-user", email="race@example.com", name="Race")
                    )
                    await winner_session.commit()
            return result

        monkeypatch.setattr(session, "execute", execute_then_let_other_request_win)

        user = await get_current_user(
            x_internal_secret=os.environ["INTERNAL_API_SECRET"],
            x_user_id="race-user",
            x_user_email="race@example.com",
            x_user_name="Race",
            db=session,
        )

    assert user.google_sub == "race-user"
    assert user.email == "race@example.com"

    async with session_maker() as verify_session:
        from sqlalchemy import select

        result = await verify_session.execute(select(User).where(User.google_sub == "race-user"))
        assert len(result.scalars().all()) == 1  # exactly one row, no duplicate/crash
