from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.schema import (
    BirthData,
    FollowUpRequest,
    ForecastRequest,
    ForecastResponse,
    LunarReturnRequest,
    LunarReturnResult,
    PictureResult,
    ReadingRecord,
    ReadingRequest,
    RelocationRequest,
    RelocationResult,
    SolarArcRequest,
    SolarArcResult,
    SynthesisOutput,
    TransitRequest,
    TransitResult,
)
from app.db.models import Base, Reading, User
from app.db.session import engine, get_db_session
from app.modules.oracle.engine import draw as oracle_draw
from app.modules.tarot.engine import draw as tarot_draw
from app.modules.uranian.engine import _compute_positions, _factor_display_name, _julian_day_ut
from app.modules.uranian.engine import calculate as uranian_calculate
from app.modules.uranian.solar_arc import (
    directed_positions,
    find_directed_pictures,
    solar_arc_degrees,
)
from app.modules.uranian.transit import find_lunar_return, relocated_angles, transit_forecast
from app.synthesis.master_interpreter import synthesize, synthesize_followup

FORECAST_PICTURE_LIMIT = 30  # a "raw table" view, wider than the natal engine's top-10 reading cap

_FORECAST_LAYER_LABELS_TH = {"r": "เกิด", "d": "directed", "t": "ปัจจุบัน"}


def _format_forecast_factor(key: str) -> str:
    layer, base = key.split(":", 1)
    return f"{_factor_display_name(base)} ({_FORECAST_LAYER_LABELS_TH[layer]})"


def _forecast_picture_label(picture: dict[str, Any]) -> str:
    if picture["type"] == "type1":
        a, b = picture["pair"]
        c = picture["hit"]
        return f"{_format_forecast_factor(a)}/{_format_forecast_factor(b)} = {_format_forecast_factor(c)}"
    a, b = picture["pair"]
    c, d = picture["pair_b"]
    return (
        f"{_format_forecast_factor(a)}/{_format_forecast_factor(b)} = "
        f"{_format_forecast_factor(c)}/{_format_forecast_factor(d)}"
    )


def _to_picture_result(picture: dict[str, Any]) -> PictureResult:
    return PictureResult(
        type=picture["type"],
        label=_forecast_picture_label(picture),
        factors=sorted(picture["factors"]),
        orb=round(picture["orb"], 3),
    )


def _compute_forecast(
    birth_data: BirthData,
    solar_arc: SolarArcRequest | None,
    transit: TransitRequest | None,
    lunar_return: LunarReturnRequest | None,
    relocation: RelocationRequest | None,
) -> ForecastResponse:
    """Shared by /api/reading and /api/forecast so the two endpoints
    can't drift — each sub-request is independent and only computed
    when present. transit_forecast() is given birth_data so Daily M/A
    (and, through it, Transit Axes) are included automatically whenever
    a transit forecast is requested."""
    jd, known_time = _julian_day_ut(birth_data)
    natal_positions = _compute_positions(jd, birth_data, known_time)

    response = ForecastResponse()

    if solar_arc:
        arc = solar_arc_degrees(birth_data, solar_arc.target_date)
        directed = directed_positions(natal_positions, arc)
        pictures = find_directed_pictures(natal_positions, directed)
        response.solar_arc = SolarArcResult(
            arc_degrees=round(arc, 3),
            pictures=[_to_picture_result(p) for p in pictures[:FORECAST_PICTURE_LIMIT]],
        )

    if transit:
        pictures = transit_forecast(natal_positions, transit.target_date, birth_data=birth_data)
        response.transit = TransitResult(
            pictures=[_to_picture_result(p) for p in pictures[:FORECAST_PICTURE_LIMIT]]
        )

    if lunar_return:
        return_at = find_lunar_return(natal_positions["MOON"], lunar_return.search_start)
        response.lunar_return = LunarReturnResult(return_at=return_at)

    if relocation:
        if not known_time:
            raise HTTPException(422, "ต้องทราบเวลาเกิดจึงจะคำนวณดวงย้ายถิ่นได้")
        angles = relocated_angles(birth_data, relocation.latitude, relocation.longitude)
        response.relocation = RelocationResult(ascendant=angles["A"], midheaven=angles["M"])

    return response


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
    request: ReadingRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> SynthesisOutput:
    birth_data = request.birth_data

    # Run only the engines the user actually chose, concurrently — see
    # CLAUDE.md performance requirement + the per-discipline skip buttons
    # (ReadingRequest guarantees at least one of these 3 is present).
    tasks: dict[str, Any] = {}
    if birth_data is not None:
        tasks["uranian"] = uranian_calculate(birth_data)
    if request.tarot is not None:
        tasks["tarot"] = tarot_draw(request.tarot.spread)
    if request.oracle is not None:
        tasks["oracle"] = oracle_draw(count=request.oracle.card_count)

    results = await asyncio.gather(*tasks.values())
    engine_results = dict(zip(tasks.keys(), results, strict=True))

    forecast_response: ForecastResponse | None = None
    if birth_data is not None and (
        request.solar_arc or request.transit or request.lunar_return or request.relocation
    ):
        forecast_response = _compute_forecast(
            birth_data, request.solar_arc, request.transit, request.lunar_return, request.relocation
        )

    result = await synthesize(
        uranian=engine_results.get("uranian"),
        tarot=engine_results.get("tarot"),
        oracle=engine_results.get("oracle"),
        forecast=forecast_response,
        oracle_question=request.oracle.question if request.oracle else None,
    )

    db.add(
        Reading(
            user_id=user.id,
            birth_data=birth_data.model_dump(mode="json") if birth_data is not None else None,
            synthesis_output=result.model_dump(mode="json"),
        )
    )
    await db.commit()

    return result


@app.post("/api/reading/follow-up", response_model=SynthesisOutput)
async def get_reading_followup(
    request: FollowUpRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> SynthesisOutput:
    """The "ask more" flow on the result screen: draws a fresh, randomly
    sized (3-9) batch of oracle cards and synthesizes them as a priority
    continuation of `request.previous` — the reading the client already
    has in this session (see FollowUpRequest; never reads stored
    /history, per CLAUDE.md's "no user history" rule)."""
    oracle_result = await oracle_draw(count=request.oracle_count)
    result = await synthesize_followup(request.previous, oracle_result, request.question)

    db.add(
        Reading(
            user_id=user.id,
            birth_data=None,
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


@app.post("/api/forecast", response_model=ForecastResponse)
async def get_forecast(
    request: ForecastRequest,
    _user: User = Depends(get_current_user),  # auth-gated like /api/reading; result isn't persisted
) -> ForecastResponse:
    """Uranian-only forecast add-ons (Solar Arc, Transit, Lunar Return,
    Relocation) as raw picture tables — for a standalone lookup with no
    tarot/oracle draw and no Gemini synthesis. Not persisted to reading
    history, unlike /api/reading (which can also fold this same data
    into its synthesized narrative — see ReadingRequest)."""
    return _compute_forecast(
        request.birth_data,
        request.solar_arc,
        request.transit,
        request.lunar_return,
        request.relocation,
    )
