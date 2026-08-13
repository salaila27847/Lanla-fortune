"""Solar Arc Directions — a Uranian forecasting technique built on
secondary progression ("one day after birth = one year of life").

Reference: backend/app/knowledge_base/uranian/research/
uranian-solar-arc-transits-advanced.md, chapter 10.

The technique in three steps:

1. **Progressed Sun** — the Sun's real ephemeris position on the
   progression day that corresponds to the owner's age at some target
   date (age N years → N days after birth).
2. **Solar arc** — the forward angular distance between that progressed
   Sun and the natal Sun (roughly 1°/year, but not exactly, since the
   Sun's daily motion varies slightly through the year).
3. **Directed positions** — *every* natal factor advanced by that same
   arc (unlike ordinary secondary progression, where each body moves at
   its own rate — Solar Arc Directions moves them all together). A
   "directed planetary picture" is then any Type I/II midpoint
   structure (same 90°-dial technique as the natal engine) that
   involves at least one directed factor together with the radix
   (natal) chart — those are the configurations "activated" by the
   passage of time.

This module is calculation-only: it is deliberately **not** wired into
`calculate()`/`EngineResult` or any API endpoint yet, since surfacing it
to users needs a target-date input that `BirthData` doesn't have. See
docs/task-breakdown.md Phase 11 for the follow-up decision.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from datetime import time as dt_time
from itertools import combinations
from typing import Any
from zoneinfo import ZoneInfo

import swisseph as swe

from app.core.schema import BirthData
from app.modules.uranian.engine import (
    PERSONAL_POINT_IDS,
    TYPE1_ORB_DEGREES,
    TYPE2_ORB_DEGREES,
    _dial90_orb,
    _julian_day_ut,
    _midpoint,
)

DAYS_PER_YEAR = 365.2425  # Gregorian mean year — the "1 day = 1 year" progression rate

RADIX_PREFIX = "r:"
DIRECTED_PREFIX = "d:"


def _birth_datetime_utc(birth_data: BirthData) -> datetime:
    """Same local-time-or-noon-default handling as engine._julian_day_ut,
    but returning the datetime itself (needed here to add the age offset
    before converting to a Julian day)."""
    local_time = birth_data.time or dt_time(12, 0)
    local_dt = datetime.combine(birth_data.date, local_time, tzinfo=ZoneInfo(birth_data.timezone))
    return local_dt.astimezone(ZoneInfo("UTC"))


def progressed_sun_longitude(birth_data: BirthData, target_date: date) -> float:
    """The Sun's ephemeris longitude on the progression day for the
    owner's age at target_date."""
    birth_utc = _birth_datetime_utc(birth_data)
    target_utc = _birth_datetime_utc(birth_data.model_copy(update={"date": target_date}))
    age_years = (target_utc - birth_utc).days / DAYS_PER_YEAR

    progressed_dt = birth_utc + timedelta(days=age_years)
    jd = swe.julday(
        progressed_dt.year,
        progressed_dt.month,
        progressed_dt.day,
        progressed_dt.hour + progressed_dt.minute / 60 + progressed_dt.second / 3600,
    )
    return swe.calc_ut(jd, swe.SUN)[0][0]


def solar_arc_degrees(birth_data: BirthData, target_date: date) -> float:
    """Forward angular distance the Sun has progressed by target_date —
    always in [0, 360), since the Sun only ever moves prograde."""
    natal_jd, _known_time = _julian_day_ut(birth_data)
    natal_sun = swe.calc_ut(natal_jd, swe.SUN)[0][0]
    return (progressed_sun_longitude(birth_data, target_date) - natal_sun) % 360


def directed_positions(natal_positions: dict[str, float], arc: float) -> dict[str, float]:
    """Every natal factor advanced by the same solar arc — the
    defining rule of Solar Arc Directions."""
    return {factor_id: (longitude + arc) % 360 for factor_id, longitude in natal_positions.items()}


def _base_factor(key: str) -> str:
    return key.split(":", 1)[1]


def _is_directed(key: str) -> bool:
    return key.startswith(DIRECTED_PREFIX)


def _is_personal_point(key: str) -> bool:
    return _base_factor(key) in PERSONAL_POINT_IDS


def find_directed_pictures(
    natal_positions: dict[str, float],
    directed_positions_: dict[str, float],
    orb_type1: float = TYPE1_ORB_DEGREES,
    orb_type2: float = TYPE2_ORB_DEGREES,
) -> list[dict[str, Any]]:
    """Type I/II planetary pictures across the combined radix+directed
    chart. Radix and directed copies of the *same* factor are never
    paired with each other (that "midpoint" would just be a fixed
    function of the arc, not a real configuration). Pictures that are
    entirely radix are dropped (already covered by the natal engine —
    they don't represent anything time-based), and, matching the natal
    engine's convention, pictures need at least one personal point."""
    positions: dict[str, float] = {f"{RADIX_PREFIX}{k}": v for k, v in natal_positions.items()}
    positions.update({f"{DIRECTED_PREFIX}{k}": v for k, v in directed_positions_.items()})

    midpoints: dict[frozenset[str], float] = {}
    for a, b in combinations(positions, 2):
        if _base_factor(a) == _base_factor(b):
            continue
        midpoints[frozenset((a, b))] = _midpoint(positions[a], positions[b])

    found: list[dict[str, Any]] = []

    for pair, mp in midpoints.items():
        for factor, longitude in positions.items():
            if factor in pair:
                continue
            orb = _dial90_orb(longitude, mp)
            if orb <= orb_type1:
                a, b = sorted(pair)
                found.append(
                    {
                        "type": "type1",
                        "pair": (a, b),
                        "hit": factor,
                        "factors": frozenset(pair | {factor}),
                        "orb": orb,
                    }
                )

    pair_items = list(midpoints.items())
    for i, (pair_a, mp_a) in enumerate(pair_items):
        for pair_b, mp_b in pair_items[i + 1 :]:
            if pair_a & pair_b:
                continue
            # Same two bodies on both sides (e.g. radix Sun/Venus = directed
            # Sun/Venus) is a near-fixed function of the arc alone, not a
            # chart-specific configuration — skip it, but allow partial
            # overlaps (e.g. radix Sun/Moon = directed Sun/Venus), which
            # genuinely depend on the individual factors' positions.
            if {_base_factor(p) for p in pair_a} == {_base_factor(p) for p in pair_b}:
                continue
            orb = _dial90_orb(mp_a, mp_b)
            if orb <= orb_type2:
                found.append(
                    {
                        "type": "type2",
                        "pair": tuple(sorted(pair_a)),
                        "pair_b": tuple(sorted(pair_b)),
                        "factors": frozenset(pair_a | pair_b),
                        "orb": orb,
                    }
                )

    found = [
        picture
        for picture in found
        if any(_is_directed(f) for f in picture["factors"])
        and any(_is_personal_point(f) for f in picture["factors"])
    ]
    found.sort(key=lambda picture: picture["orb"])
    return found


def solar_arc_pictures(
    birth_data: BirthData,
    natal_positions: dict[str, float],
    target_date: date,
) -> list[dict[str, Any]]:
    """Convenience entry point: compute the arc for target_date, direct
    every natal factor by it, and return the resulting pictures. Callers
    that already have natal_positions (e.g. from
    uranian.engine._compute_positions) should pass it in rather than
    recomputing it."""
    arc = solar_arc_degrees(birth_data, target_date)
    directed = directed_positions(natal_positions, arc)
    return find_directed_pictures(natal_positions, directed)
