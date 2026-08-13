"""Transits, Station Points, Lunar Returns, and Relocation — the
remaining Uranian forecasting techniques from the handoff package's
research docs, chapters 11-12 (everything except Solar Arc Directions,
which is in solar_arc.py).

Reference: backend/app/knowledge_base/uranian/research/
uranian-solar-arc-transits-advanced.md

Covers, per the doc's "features the team should build" summary table:

- **Transit forecast** — real (not directed) planetary positions on a
  target date, checked against the radix (and optionally directed)
  chart for Type I/II pictures, at the tight orb (≤1°) the source
  material specifies for transits.
- **Station points** — the dates a slow-moving body turns retrograde or
  direct, which the doc singles out as especially significant when the
  station lands on a personal point.
- **Lunar Return** — the ~27.3-day cycle date when the transiting Moon
  returns to its natal degree, used for monthly-resolution forecasting.
- **Relocation** — Ascendant/Midheaven recomputed for the same birth
  moment at a different location.

Not covered here (see docs/task-breakdown.md): "Daily Meridian and
Ascendant" (a *current-moment* M/A, distinct from relocation's
*different-place* M/A) and "Transit Axes" beyond what
find_transit_pictures already does by treating transit factors as just
another layer in the same Type I/II search.

Like solar_arc.py, this module is calculation-only: not wired into
calculate()/EngineResult or any API endpoint yet.
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
    CLASSICAL_SWE_IDS,
    PERSONAL_POINT_IDS,
    TNP_SWE_IDS,
    _dial90_orb,
    _julian_day_ut,
    _midpoint,
)

TRANSIT_ORB_DEGREES = 1.0  # tight orb — Uranian transits are read as near-exact events, not applying/separating ranges

SLOW_TRANSIT_FACTORS = frozenset(
    {
        "JUPITER",
        "SATURN",
        "URANUS",
        "NEPTUNE",
        "PLUTO",
        "CUPIDO",
        "HADES",
        "ZEUS",
        "KRONOS",
        "APOLLON",
        "ADMETOS",
        "VULKANUS",
        "POSEIDON",
    }
)  # "most significant" per the source doc — slow bodies give longer-lasting, more significant effects

RADIX_PREFIX = "r:"
DIRECTED_PREFIX = "d:"
TRANSIT_PREFIX = "t:"


def transit_positions(target_date: date, target_time: dt_time | None = None) -> dict[str, float]:
    """Real ephemeris longitudes for the 10 classical bodies, 8 TNPs, and
    the (true) Node on target_date — noon UTC by default, since transits
    are normally read at day resolution; pass target_time for hour-level
    precision (e.g. pinning down a station moment)."""
    dt = datetime.combine(target_date, target_time or dt_time(12, 0), tzinfo=ZoneInfo("UTC"))
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60 + dt.second / 3600)

    positions: dict[str, float] = {
        factor_id: swe.calc_ut(jd, swe_id)[0][0] for factor_id, swe_id in CLASSICAL_SWE_IDS.items()
    }
    for point_id, swe_id in TNP_SWE_IDS.items():
        positions[point_id.upper()] = swe.calc_ut(jd, swe_id)[0][0]
    positions["NODE"] = swe.calc_ut(jd, swe.TRUE_NODE)[0][0]
    return positions


def _base_factor(key: str) -> str:
    return key.split(":", 1)[1]


def _layer(key: str) -> str:
    return key.split(":", 1)[0]


def _is_arc_locked_pair(pair_a: frozenset[str], pair_b: frozenset[str]) -> bool:
    """True when pair_a and pair_b, between them, consist of exactly the
    radix *and* directed copies of the same two bodies — however those
    four factor-instances happen to be split into the two pairs. Since
    directed = radix + one constant arc for every body, any such split
    is a near-fixed function of the arc alone (e.g. both
    radix-Sun/Venus=directed-Sun/Venus *and* the "cross" pairing
    radix-Sun/directed-Venus=directed-Sun/radix-Venus reduce to the same
    algebraic identity — midpoint(x, y+k) == midpoint(x+k, y) for a
    shared k), so neither is a chart-specific configuration.

    Transit motion isn't a constant offset from radix, so any
    combination involving a transit factor is left alone — e.g. radix
    Sun/Venus vs transit Sun/Venus is a genuine, date-specific question."""
    combined = pair_a | pair_b
    if len(combined) != 4:
        return False
    bodies = {_base_factor(f) for f in combined}
    if len(bodies) != 2:
        return False
    return all(
        {_layer(f) for f in combined if _base_factor(f) == body} == {"r", "d"} for body in bodies
    )


def find_transit_pictures(
    natal_positions: dict[str, float],
    transit_positions_: dict[str, float],
    directed_positions_: dict[str, float] | None = None,
    orb_type1: float = TRANSIT_ORB_DEGREES,
    orb_type2: float = TRANSIT_ORB_DEGREES,
) -> list[dict[str, Any]]:
    """Type I/II planetary pictures across the combined radix (+
    optional directed) + transit chart, at the tight orb Uranian
    technique uses for transits (unlike the natal/solar-arc engines,
    Type II isn't given a wider orb here — the source doc treats
    transits as near-exact events).

    A picture must involve at least one transit (or directed) factor —
    pure radix pictures are already covered by the natal engine — and at
    least one *radix or directed* personal point, matching the source
    material's rule that a transit-transit aspect only matters "if it
    lands on a personal point in the birth chart" (a transiting Sun/
    Moon/Node passing through the sky isn't itself a personal point;
    only the fixed radix/directed reference points are)."""
    positions: dict[str, float] = {f"{RADIX_PREFIX}{k}": v for k, v in natal_positions.items()}
    if directed_positions_:
        positions.update({f"{DIRECTED_PREFIX}{k}": v for k, v in directed_positions_.items()})
    positions.update({f"{TRANSIT_PREFIX}{k}": v for k, v in transit_positions_.items()})

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
            if pair_a & pair_b or _is_arc_locked_pair(pair_a, pair_b):
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

    def _has_moving_factor(factors: frozenset[str]) -> bool:
        return any(_layer(f) in {"d", "t"} for f in factors)

    def _has_reference_personal_point(factors: frozenset[str]) -> bool:
        return any(
            _layer(f) in {"r", "d"} and _base_factor(f) in PERSONAL_POINT_IDS for f in factors
        )

    found = [
        p
        for p in found
        if _has_moving_factor(p["factors"]) and _has_reference_personal_point(p["factors"])
    ]
    found.sort(key=lambda p: p["orb"])
    return found


def transit_forecast(
    natal_positions: dict[str, float],
    target_date: date,
    directed_positions_: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    """Convenience entry point: compute transit positions for
    target_date and return the resulting pictures against natal_positions
    (and directed_positions_, if given)."""
    return find_transit_pictures(
        natal_positions, transit_positions(target_date), directed_positions_
    )


def daily_speed(factor_id: str, target_date: date) -> float:
    """Longitudinal speed (degrees/day) of factor_id at UTC noon on
    target_date — positive means direct motion, negative retrograde."""
    swe_id = CLASSICAL_SWE_IDS.get(factor_id, TNP_SWE_IDS.get(factor_id.lower()))
    if swe_id is None:
        raise ValueError(f"Unknown factor for speed lookup: {factor_id!r}")
    dt = datetime.combine(target_date, dt_time(12, 0), tzinfo=ZoneInfo("UTC"))
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour)
    return swe.calc_ut(jd, swe_id)[0][3]


def find_stations_in_range(factor_id: str, start_date: date, end_date: date) -> list[date]:
    """Dates in [start_date, end_date) where factor_id's daily speed
    changes sign — i.e. it stations retrograde or direct. Scans day by
    day: station events for the slow bodies this technique cares about
    are weeks-to-months apart, so daily resolution reliably catches
    them (exact-hour timing isn't attempted here)."""
    stations: list[date] = []
    current = start_date
    previous_speed = daily_speed(factor_id, current)
    current += timedelta(days=1)
    while current < end_date:
        speed = daily_speed(factor_id, current)
        if (previous_speed >= 0) != (speed >= 0):
            stations.append(current)
        previous_speed = speed
        current += timedelta(days=1)
    return stations


def _wrapped_diff(a: float, b: float) -> float:
    """Signed difference a-b wrapped into (-180, 180]."""
    return ((a - b + 180) % 360) - 180


def find_lunar_return(
    natal_moon_longitude: float, search_start: date, max_days: int = 30
) -> datetime:
    """The next UTC datetime on/after search_start when the transiting
    Moon returns to natal_moon_longitude (a ~27.3-day cycle).

    The Moon's ecliptic longitude always moves prograde (it never
    stations), so a 6-hour sampling grid can bracket the crossing
    unambiguously — bisecting within that bracket then narrows it to
    well under a minute."""

    def moon_longitude(dt: datetime) -> float:
        jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60 + dt.second / 3600)
        return swe.calc_ut(jd, swe.MOON)[0][0]

    step = timedelta(hours=6)
    t0 = datetime.combine(search_start, dt_time(0, 0), tzinfo=ZoneInfo("UTC"))
    limit = t0 + timedelta(days=max_days)

    prev_t = t0
    prev_diff = _wrapped_diff(moon_longitude(t0), natal_moon_longitude)
    t = t0 + step
    while t <= limit:
        diff = _wrapped_diff(moon_longitude(t), natal_moon_longitude)
        if prev_diff <= 0 <= diff:
            lo, hi = prev_t, t
            for _ in range(20):
                mid = lo + (hi - lo) / 2
                mid_diff = _wrapped_diff(moon_longitude(mid), natal_moon_longitude)
                lo, hi = (lo, mid) if mid_diff >= 0 else (mid, hi)
            return lo + (hi - lo) / 2
        prev_t, prev_diff = t, diff
        t += step

    raise ValueError(f"No lunar return found within {max_days} days of {search_start}")


def relocated_angles(
    birth_data: BirthData, new_latitude: float, new_longitude: float
) -> dict[str, float]:
    """Ascendant/Midheaven recomputed for the same birth moment (UTC) at
    a different location — the "relocation chart" technique. Uses the
    same Placidus houses call as the natal engine, even though only the
    angles (ascmc), not the house cusps, are needed here."""
    jd, known_time = _julian_day_ut(birth_data)
    if not known_time:
        raise ValueError("Relocation requires a known birth time")
    _, ascmc = swe.houses(jd, new_latitude, new_longitude, b"P")
    return {"A": ascmc[0], "M": ascmc[1]}
