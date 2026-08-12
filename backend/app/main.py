from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.schema import BirthData, ReadingRecord, SynthesisOutput
from app.db.models import Base, Reading, User
from app.db.session import engine, get_db_session
from app.modules.oracle.engine import draw as oracle_draw
from app.modules.tarot.engine import draw as tarot_draw
from app.modules.uranian.engine import calculate as uranian_calculate
from app.synthesis.master_interpreter import synthesize

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Fail loudly at startup rather than 500-ing on the first authenticated
    # request if this was left unset.
    if not os.environ.get("INTERNAL_API_SECRET"):
        raise RuntimeError("INTERNAL_API_SECRET is not set")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield


app = FastAPI(title="Fortune App API", lifespan=lifespan)

_frontend_origins = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_frontend_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/reading", response_model=SynthesisOutput)
async def get_reading(
    birth_data: BirthData,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> SynthesisOutput:
    # Run all 3 engines concurrently — see CLAUDE.md performance requirement.
    uranian_result, tarot_result, oracle_result = await asyncio.gather(
        uranian_calculate(birth_data),
        tarot_draw(),
        oracle_draw(),
    )
    result = await synthesize(uranian_result, tarot_result, oracle_result)

    db.add(
        Reading(
            user_id=user.id,
            birth_data=birth_data.model_dump(mode="json"),
            synthesis_output=result.model_dump(mode="json"),
        )
    )
    await db.commit()

    return result


@app.get("/api/readings", response_model=list[ReadingRecord])
async def list_readings(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[ReadingRecord]:
    result = await db.execute(
        select(Reading)
        .where(Reading.user_id == user.id)
        .order_by(Reading.created_at.desc(), Reading.id.desc())
    )
    return [
        ReadingRecord(
            id=row.id,
            created_at=row.created_at,
            birth_data=row.birth_data,
            synthesis=row.synthesis_output,
        )
        for row in result.scalars()
    ]
