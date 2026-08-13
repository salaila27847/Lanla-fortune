"""Verifies the shared secret the Next.js BFF attaches to server-to-server
calls, then upserts/looks up the User it claims to be acting for.

The Next.js server is the one that actually verified the NextAuth session
(see frontend/src/lib/backend.ts) — this dependency only checks that the
caller knows INTERNAL_API_SECRET, which is never exposed to the browser.
"""

from __future__ import annotations

import hmac
import os

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.db.session import get_db_session


async def get_current_user(
    x_internal_secret: str | None = Header(None),
    x_user_id: str | None = Header(None),
    x_user_email: str | None = Header(None),
    x_user_name: str | None = Header(None),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    internal_secret = os.environ["INTERNAL_API_SECRET"]
    if not x_internal_secret or not hmac.compare_digest(x_internal_secret, internal_secret):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not x_user_id or not x_user_email:
        raise HTTPException(status_code=401, detail="Unauthorized")

    result = await db.execute(select(User).where(User.google_sub == x_user_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(google_sub=x_user_id, email=x_user_email, name=x_user_name)
        db.add(user)
        try:
            await db.flush()
        except IntegrityError:
            # Lost a race with a concurrent request creating the same brand-new
            # user (e.g. the frontend firing /api/reading and /api/forecast at
            # once on someone's first request ever) — roll back our attempted
            # insert and pick up the row the other request just committed.
            await db.rollback()
            result = await db.execute(select(User).where(User.google_sub == x_user_id))
            user = result.scalar_one()
    elif user.email != x_user_email or user.name != x_user_name:
        user.email = x_user_email
        user.name = x_user_name

    return user
