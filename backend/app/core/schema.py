"""Shared data contracts — see docs/data-schema.md.

All 3 engines (uranian, tarot, oracle) must return an EngineResult.
The Master Interpreter (synthesis layer) only ever consumes this shape,
so it never needs to know the internals of any one engine.
"""

from __future__ import annotations

from datetime import date, datetime
from datetime import time as dt_time
from typing import Literal
from zoneinfo import available_timezones

from pydantic import BaseModel, Field, field_validator

_VALID_TIMEZONES = frozenset(available_timezones())


class Finding(BaseModel):
    label: str
    meaning: str
    weight: float = Field(ge=0, le=1)


class EngineResult(BaseModel):
    engine: Literal["uranian", "tarot", "oracle"]
    summary: str
    themes: list[str]
    raw_findings: list[Finding]
    confidence: float = Field(ge=0, le=1)


class BirthData(BaseModel):
    date: date
    time: dt_time | None = None
    place: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    timezone: str

    @field_validator("timezone")
    @classmethod
    def _validate_timezone(cls, value: str) -> str:
        if value not in _VALID_TIMEZONES:
            raise ValueError(f"Unknown IANA timezone: {value!r}")
        return value


class CardDraw(BaseModel):
    deck: str
    card_id: str
    position_in_spread: str | None = None
    reversed: bool = False


class SolarArcRequest(BaseModel):
    target_date: date


class TransitRequest(BaseModel):
    target_date: date


class LunarReturnRequest(BaseModel):
    search_start: date


class RelocationRequest(BaseModel):
    place: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class ForecastRequest(BaseModel):
    """Body for POST /api/forecast (standalone forecast lookup, no
    reading/synthesis). POST /api/reading accepts the identical set of
    optional sub-requests via ReadingRequest below, so a reading can
    fold forecast data into its Gemini synthesis in the same call."""

    birth_data: BirthData
    solar_arc: SolarArcRequest | None = None
    transit: TransitRequest | None = None
    lunar_return: LunarReturnRequest | None = None
    relocation: RelocationRequest | None = None


class PictureResult(BaseModel):
    type: Literal["type1", "type2"]
    label: str
    factors: list[str]
    orb: float


class SolarArcResult(BaseModel):
    arc_degrees: float
    pictures: list[PictureResult]


class TransitResult(BaseModel):
    pictures: list[PictureResult]


class LunarReturnResult(BaseModel):
    return_at: datetime


class RelocationResult(BaseModel):
    ascendant: float
    midheaven: float


class ForecastResponse(BaseModel):
    solar_arc: SolarArcResult | None = None
    transit: TransitResult | None = None
    lunar_return: LunarReturnResult | None = None
    relocation: RelocationResult | None = None


class ReadingRequest(BaseModel):
    """Body for POST /api/reading. The optional forecast sub-requests are
    the same shape as ForecastRequest — when any is present, the reading
    endpoint computes that forecast data too and feeds it into
    synthesize() alongside the 3 engines, so the reading's final_reading
    can weave in Solar Arc/Transit/Lunar Return/Relocation."""

    birth_data: BirthData
    solar_arc: SolarArcRequest | None = None
    transit: TransitRequest | None = None
    lunar_return: LunarReturnRequest | None = None
    relocation: RelocationRequest | None = None


class SynthesisOutput(BaseModel):
    final_reading: str
    convergent_themes: list[str]
    divergent_notes: list[str]
    per_engine_breakdown: dict[str, EngineResult]
    forecast: ForecastResponse | None = None


class ReadingRecord(BaseModel):
    id: int
    created_at: datetime
    birth_data: BirthData
    synthesis: SynthesisOutput
