"""Tests for the Solar Arc Directions calculation module — see
app/modules/uranian/solar_arc.py for the technique and its current scope
(calculation-only, not wired into calculate()/EngineResult/any endpoint).
"""

from __future__ import annotations

from datetime import date, time

import pytest

from app.core.schema import BirthData
from app.modules.uranian.solar_arc import (
    directed_positions,
    find_directed_pictures,
    progressed_sun_longitude,
    solar_arc_degrees,
    solar_arc_pictures,
)

BIRTH_WITH_TIME = BirthData(
    date=date(1990, 7, 22),
    time=time(15, 52),
    place="Trang, Thailand",
    latitude=7.5563,
    longitude=99.6114,
    timezone="Asia/Bangkok",
)


def test_solar_arc_is_roughly_one_degree_per_year():
    # 30 years old: solar arc should be in the same ballpark as 30 days'
    # worth of the Sun's real motion (~0.9856°/day average).
    arc = solar_arc_degrees(BIRTH_WITH_TIME, date(2020, 7, 22))
    assert 25.0 < arc < 35.0


def test_solar_arc_is_zero_at_birth():
    arc = solar_arc_degrees(BIRTH_WITH_TIME, BIRTH_WITH_TIME.date)
    assert arc == pytest.approx(0.0, abs=0.01)


def test_solar_arc_grows_with_age():
    arc_10 = solar_arc_degrees(BIRTH_WITH_TIME, date(2000, 7, 22))
    arc_30 = solar_arc_degrees(BIRTH_WITH_TIME, date(2020, 7, 22))
    assert arc_10 < arc_30


def test_progressed_sun_is_a_valid_longitude():
    lon = progressed_sun_longitude(BIRTH_WITH_TIME, date(2020, 7, 22))
    assert 0.0 <= lon < 360.0


def test_directed_positions_adds_the_same_arc_to_every_factor():
    natal = {"SUN": 10.0, "MOON": 350.0, "M": 90.0}
    directed = directed_positions(natal, arc=20.0)
    assert directed == {"SUN": 30.0, "MOON": 10.0, "M": 110.0}  # MOON wraps past 360


def test_solar_arc_pictures_smoke_test_on_a_real_chart():
    from app.modules.uranian.engine import _compute_positions, _julian_day_ut

    jd, known_time = _julian_day_ut(BIRTH_WITH_TIME)
    natal_positions = _compute_positions(jd, BIRTH_WITH_TIME, known_time)
    pictures = solar_arc_pictures(BIRTH_WITH_TIME, natal_positions, date(2026, 8, 13))
    for picture in pictures:
        assert picture["type"] in {"type1", "type2"}
        assert picture["orb"] >= 0


# ---------- find_directed_pictures (synthetic positions) ----------


def test_directed_factor_hitting_a_radix_midpoint_is_detected():
    # radix M/KRONOS midpoint = 20; directed M (natal 0 + arc 20 = 20)
    # sits right on it — a classic "directed body activates a radix
    # midpoint" configuration, even though M appears on both sides.
    natal = {"M": 0.0, "KRONOS": 40.0, "SATURN": 200.0}
    directed = directed_positions(natal, arc=20.0)
    pictures = find_directed_pictures(natal, directed)
    matches = [p for p in pictures if p["factors"] == frozenset({"r:M", "r:KRONOS", "d:M"})]
    assert len(matches) == 1
    assert matches[0]["orb"] < 0.01


def test_all_radix_picture_is_excluded():
    # r:M/r:KRONOS=r:SATURN is a valid Type I picture on its own, but it's
    # purely radix (no directed factor), so the natal engine already
    # covers it — solar_arc's picture-finder should drop it.
    natal = {"M": 0.0, "KRONOS": 40.0, "SATURN": 200.0}
    directed = directed_positions(natal, arc=45.0)  # keeps directed copies well away
    pictures = find_directed_pictures(natal, directed)
    assert not any(p["factors"] == frozenset({"r:M", "r:KRONOS", "r:SATURN"}) for p in pictures)


def test_same_body_pair_on_both_sides_is_excluded():
    # radix Sun/Venus = directed Sun/Venus, at an arc (90°) that makes the
    # two midpoints coincide — this is a near-fixed function of the arc
    # alone (not chart-specific), so it should be filtered out.
    natal = {"SUN": 0.0, "VENUS": 20.0}
    directed = directed_positions(natal, arc=90.0)
    pictures = find_directed_pictures(natal, directed)
    assert not any(
        p["factors"] == frozenset({"r:SUN", "r:VENUS", "d:SUN", "d:VENUS"}) for p in pictures
    )


def test_partial_overlap_type2_picture_is_kept():
    # radix Sun/Moon = directed Sun/Venus — Sun appears on both sides but
    # via different bodies paired with it, so this is a genuine,
    # chart-specific configuration and must NOT be excluded.
    natal = {"SUN": 0.0, "MOON": 20.0, "VENUS": 11.0}
    directed = directed_positions(natal, arc=4.5)
    pictures = find_directed_pictures(natal, directed)
    matches = [
        p for p in pictures if p["factors"] == frozenset({"r:SUN", "r:MOON", "d:SUN", "d:VENUS"})
    ]
    assert len(matches) == 1
    assert matches[0]["orb"] < 0.01


def test_pictures_without_a_personal_point_are_filtered_out():
    natal = {"MERCURY": 0.0, "SATURN": 40.0, "VENUS": 20.0}
    directed = directed_positions(natal, arc=20.0)
    pictures = find_directed_pictures(natal, directed)
    assert pictures == []
