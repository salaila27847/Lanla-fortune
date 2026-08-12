"""Shared data contracts — see docs/data-schema.md.

All 3 engines (uranian, tarot, oracle) must return an EngineResult.
The Master Interpreter (synthesis layer) only ever consumes this shape,
so it never needs to know the internals of any one engine.
"""

from __future__ import annotations

from datetime import date
from datetime import time as dt_time
from typing import Literal

from pydantic import BaseModel, Field


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
    latitude: float
    longitude: float
    timezone: str


class CardDraw(BaseModel):
    deck: str
    card_id: str
    position_in_spread: str | None = None
    reversed: bool = False


class SynthesisOutput(BaseModel):
    final_reading: str
    convergent_themes: list[str]
    divergent_notes: list[str]
    per_engine_breakdown: dict[str, EngineResult]
