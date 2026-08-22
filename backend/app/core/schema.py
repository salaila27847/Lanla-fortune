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

from pydantic import BaseModel, Field, field_validator, model_validator

_VALID_TIMEZONES = frozenset(available_timezones())


class Finding(BaseModel):
    label: str
    meaning: str
    weight: float = Field(ge=0, le=1)
    voice: str | None = None


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


class OracleDrawRequest(BaseModel):
    """Body for POST /api/oracle/draw — fetches a full shuffled deck so
    the client can lay out real cards face-down and reveal genuine picks,
    instead of a cosmetic grid whose positions never mapped to anything
    (see app/modules/oracle/engine.py's shuffle())."""

    deck: str | None = None


class OracleCardPreview(BaseModel):
    card_id: str
    name_th: str
    category_th: str
    meaning: str
    keywords: list[str]


class OracleDeckResponse(BaseModel):
    cards: list[OracleCardPreview]


class TarotDrawRequest(BaseModel):
    """Body for POST /api/tarot/draw — same idea as OracleDrawRequest for
    the 78-card tarot deck. Orientation (reversed) is decided per card at
    shuffle time too, so it's fixed before the reveal rather than
    re-rolled afterward."""

    spread: str = "three_card"


class TarotCardPreview(BaseModel):
    card_id: str
    name_th: str
    reversed: bool
    meaning: str
    keywords: list[str]


class TarotDeckResponse(BaseModel):
    positions: list[str]
    cards: list[TarotCardPreview]


class TarotPick(BaseModel):
    """One card the user actually tapped and revealed, in tap order — id
    and orientation as delivered by /api/tarot/draw. Trusted as-is (no
    server-side session/token — see CLAUDE.md's "trust client" decision);
    the backend always re-looks-up the meaning from its own knowledge
    base by card_id, so a client can misreport at most *which* card it
    claims to have picked, never the meaning attached to it."""

    card_id: str
    reversed: bool


class TarotRequest(BaseModel):
    """Present in ReadingRequest only when the user chose to use Tarot —
    its absence is how the reading endpoint knows to skip the engine
    entirely (see CLAUDE.md item: skip button per discipline). `picks`
    must be cards (by id) drawn from the same shuffled deck /api/tarot/draw
    returned, one per spread position — the endpoint validates the count
    against spreads.yaml since that's not expressible statically here."""

    spread: str = "three_card"
    picks: list[TarotPick]


class OracleRequest(BaseModel):
    """Present in ReadingRequest only when the user chose to use Oracle.
    `picks` are card ids in tap order, 3-9 of them (system-randomized by
    the caller before drawing, never a user-chosen count) from a deck the
    client fetched via /api/oracle/draw — see docs/data-schema.md.
    question is required when Oracle is the *only* engine chosen
    (validated on ReadingRequest below) and unused otherwise."""

    picks: list[str] = Field(min_length=3, max_length=9)
    question: str | None = Field(default=None, min_length=1, max_length=1000)
    deck: str | None = None


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


class FineTimingHit(BaseModel):
    """A fast-moving transiting body landing on the 22.5° (16th-harmonic)
    family of a radix/directed personal point — the day-level timing
    filter from the dial hierarchy (90° dial = is this theme active,
    22.5° dial = is it today). See transit.find_fine_timing_hits()."""

    label: str
    transit_factor: str
    reference_factor: str
    orb: float


class HousePlacementResult(BaseModel):
    """Which Meridian-system house a factor falls in, for the forecast
    endpoints — the same house-placement technique the natal engine uses
    (see uranian.engine._house_placements), applied to directed/transit/
    relocated positions instead of the radix chart. factor/house_number
    are the raw values (for programmatic use); label is the ready-to-show
    Thai string."""

    factor: str
    house_number: int
    label: str


class SolarArcResult(BaseModel):
    arc_degrees: float
    pictures: list[PictureResult]
    house_placements: list[HousePlacementResult] = []


class TransitResult(BaseModel):
    pictures: list[PictureResult]
    fine_timing: list[FineTimingHit] = []
    house_placements: list[HousePlacementResult] = []


class LunarReturnResult(BaseModel):
    return_at: datetime


class RelocationResult(BaseModel):
    ascendant: float
    midheaven: float
    house_placements: list[HousePlacementResult] = []


class ForecastResponse(BaseModel):
    solar_arc: SolarArcResult | None = None
    transit: TransitResult | None = None
    lunar_return: LunarReturnResult | None = None
    relocation: RelocationResult | None = None


class ReadingRequest(BaseModel):
    """Body for POST /api/reading. Each of birth_data/tarot/oracle is now
    optional and independently gates whether that engine runs — the user
    can skip any 1 or 2 of the 3 disciplines (see CLAUDE.md). The
    forecast sub-requests are the same shape as ForecastRequest — when
    any is present, the reading endpoint computes that forecast data too
    and feeds it into synthesize() alongside whichever engines ran, so
    the reading's final_reading can weave in Solar Arc/Transit/Lunar
    Return/Relocation. At least one of birth_data/tarot/oracle must be
    present; forecast sub-requests require birth_data (they're Uranian
    add-ons); an oracle-only reading (no birth_data, no tarot) requires
    oracle.question, since the standalone-Oracle flow asks the question
    before letting the user draw cards."""

    birth_data: BirthData | None = None
    tarot: TarotRequest | None = None
    oracle: OracleRequest | None = None
    solar_arc: SolarArcRequest | None = None
    transit: TransitRequest | None = None
    lunar_return: LunarReturnRequest | None = None
    relocation: RelocationRequest | None = None

    @model_validator(mode="after")
    def _validate_engine_selection(self) -> ReadingRequest:
        if not (self.birth_data or self.tarot or self.oracle):
            raise ValueError("ต้องเลือกอย่างน้อย 1 ศาสตร์ (ยูเรเนียน/ทาโรต์/ออราเคิล)")
        if (
            self.solar_arc or self.transit or self.lunar_return or self.relocation
        ) and not self.birth_data:
            raise ValueError("ต้องมีข้อมูลวันเกิดจึงจะคำนวณการพยากรณ์ล่วงหน้าได้")
        oracle_only = self.oracle and not self.birth_data and not self.tarot
        if oracle_only and not (self.oracle.question and self.oracle.question.strip()):
            raise ValueError("ต้องระบุคำถามก่อนจั่วไพ่ออราเคิลเมื่อไม่ได้ใช้ศาสตร์อื่นร่วมด้วย")
        return self


class SynthesisOutput(BaseModel):
    final_reading: str
    convergent_themes: list[str]
    divergent_notes: list[str]
    per_engine_breakdown: dict[str, EngineResult]
    forecast: ForecastResponse | None = None
    oracle_question: str | None = None


class FollowUpRequest(BaseModel):
    """Body for POST /api/reading/follow-up — the "ask more" flow on the
    result screen. The client sends back the exact SynthesisOutput it
    already has (this session's current reading, not anything pulled
    from stored /history — see CLAUDE.md's "no user history" rule) plus
    a new question and the picks (card ids, tap order, 3-9 of them) it
    revealed from a fresh deck fetched via /api/oracle/draw. The new
    oracle draw takes priority in the synthesis while staying continuous
    with the previous reading."""

    previous: SynthesisOutput
    question: str = Field(min_length=1, max_length=1000)
    oracle_picks: list[str] = Field(min_length=3, max_length=9)


class ReadingRecord(BaseModel):
    id: int
    created_at: datetime
    birth_data: BirthData | None = None
    synthesis: SynthesisOutput
