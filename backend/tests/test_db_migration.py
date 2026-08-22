"""Tests for app.db.session.ensure_user_birth_data_columns() — the
startup step that backfills User.birth_* columns onto a `users` table
that already existed before this feature shipped (Base.metadata.create_all()
only creates missing *tables*, never alters an existing one).
"""

from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.session import _USER_BIRTH_DATA_COLUMNS, ensure_user_birth_data_columns


async def _get_columns(conn) -> set[str]:
    return {
        col["name"]
        for col in await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_columns("users"))
    }


async def test_backfills_missing_columns_onto_a_pre_existing_table():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.begin() as conn:
            # The pre-feature schema: no birth_* columns at all.
            await conn.execute(
                text(
                    "CREATE TABLE users (id INTEGER PRIMARY KEY, google_sub VARCHAR UNIQUE, "
                    "email VARCHAR, name VARCHAR, created_at DATETIME)"
                )
            )
            await conn.execute(
                text(
                    "INSERT INTO users (id, google_sub, email, name) "
                    "VALUES (1, 'sub-1', 'a@x.com', 'A')"
                )
            )

        async with engine.begin() as conn:
            assert await _get_columns(conn) == {"id", "google_sub", "email", "name", "created_at"}
            await ensure_user_birth_data_columns(conn)
            assert await _get_columns(conn) == {
                "id",
                "google_sub",
                "email",
                "name",
                "created_at",
                *_USER_BIRTH_DATA_COLUMNS,
            }

        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT google_sub, email, name, birth_date FROM users WHERE id = 1")
            )
            row = result.one()
            assert row.google_sub == "sub-1"
            assert row.email == "a@x.com"
            assert row.name == "A"
            assert row.birth_date is None  # existing row, backfilled column defaults to NULL
    finally:
        await engine.dispose()


async def test_is_a_no_op_on_a_table_that_already_has_the_columns():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.begin() as conn:
            columns_sql = ", ".join(
                f"{name} {sql_type}" for name, sql_type in _USER_BIRTH_DATA_COLUMNS.items()
            )
            await conn.execute(
                text(
                    "CREATE TABLE users (id INTEGER PRIMARY KEY, google_sub VARCHAR UNIQUE, "
                    f"email VARCHAR, name VARCHAR, created_at DATETIME, {columns_sql})"
                )
            )

        async with engine.begin() as conn:
            before = await _get_columns(conn)
            await ensure_user_birth_data_columns(conn)  # must not raise (e.g. duplicate column)
            after = await _get_columns(conn)
            assert before == after
    finally:
        await engine.dispose()
