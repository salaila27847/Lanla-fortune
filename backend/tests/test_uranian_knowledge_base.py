"""Tests for the real Uranian engine (Phase 3 — replaces the Phase 1
mock). Keep test_engine_contracts.py's schema check separate; this file
checks the actual astronomical calculation and knowledge-base content.
"""

from __future__ import annotations

from datetime import date, time

import pytest

from app.core.schema import BirthData
from app.modules.uranian.engine import (
    PERSONAL_POINT_IDS,
    TNP_SWE_IDS,
    _dial90_orb,
    _factor_category,
    _factor_display_name,
    _factor_keywords,
    _find_pictures,
    _load_axis_meanings,
    _load_factors,
    _load_planetary_pictures,
    _load_points,
    _load_signs,
    _midpoint,
    _midpoint_matrix,
    _picture_finding,
    _sign_for_longitude,
    calculate,
)

BIRTH_WITH_TIME = BirthData(
    date=date(1990, 1, 1),
    time=time(6, 30),
    place="Bangkok",
    latitude=13.7563,
    longitude=100.5018,
    timezone="Asia/Bangkok",
)

BIRTH_WITHOUT_TIME = BirthData(
    date=date(1990, 1, 1),
    time=None,
    place="Bangkok",
    latitude=13.7563,
    longitude=100.5018,
    timezone="Asia/Bangkok",
)


def test_points_kb_covers_all_eight_tnps():
    points = _load_points()
    assert set(points) == set(TNP_SWE_IDS)
    for point in points.values():
        assert point["meaning_core"]
        assert point["keywords"]


def test_signs_kb_has_twelve_signs_in_order():
    signs = _load_signs()
    assert len(signs) == 12
    assert [s["start_degree"] for s in signs] == [i * 30 for i in range(12)]


def test_sign_lookup_wraps_correctly():
    assert _sign_for_longitude(0)["id"] == "aries"
    assert _sign_for_longitude(29.9)["id"] == "aries"
    assert _sign_for_longitude(30)["id"] == "taurus"
    assert _sign_for_longitude(359.9)["id"] == "pisces"


def test_midpoint_uses_shorter_arc():
    assert _midpoint(10, 20) == 15
    # 350 and 10 are 20 apart via 0, not 340 apart the long way
    assert _midpoint(350, 10) == 0


def test_dial90_orb_wraps_within_quadrant():
    assert _dial90_orb(10, 10) == 0
    assert _dial90_orb(10, 100) == pytest.approx(0.0, abs=1e-9)
    assert _dial90_orb(0, 45) == 45


@pytest.mark.asyncio
async def test_calculate_with_known_time():
    result = await calculate(BIRTH_WITH_TIME)
    assert result.engine == "uranian"
    assert result.confidence == 0.55
    assert len(result.raw_findings) >= 8
    assert "mock" not in result.summary.lower()


@pytest.mark.asyncio
async def test_calculate_without_known_time_has_lower_confidence_and_caveat():
    result = await calculate(BIRTH_WITHOUT_TIME)
    assert result.confidence == 0.35
    assert any("ไม่ทราบเวลาเกิด" in f.label for f in result.raw_findings)


@pytest.mark.asyncio
async def test_calculate_is_deterministic_for_the_same_birth_data():
    first = await calculate(BIRTH_WITH_TIME)
    second = await calculate(BIRTH_WITH_TIME)
    assert [f.label for f in first.raw_findings] == [f.label for f in second.raw_findings]


# ---------- factors.yaml / planetary_pictures.yaml / axis_meanings.yaml ----------


def test_factors_kb_covers_the_other_fourteen_factors():
    factors = _load_factors()
    expected = {"SUN", "MOON", "M", "A", "NODE", "ARIES"} | {
        "MERCURY",
        "VENUS",
        "MARS",
        "JUPITER",
        "SATURN",
        "URANUS",
        "NEPTUNE",
        "PLUTO",
    }
    assert set(factors) == expected
    for factor in factors.values():
        assert factor["meaning_core"]
        assert factor["keywords"]
        assert factor["category"] in {"personal_point", "planet"}


def test_all_twenty_two_factors_are_resolvable():
    """factors.yaml (14) + points.yaml (8 TNPs, lowercase ids) together must
    cover every factor id the engine can produce in a picture."""
    all_ids = set(_load_factors()) | {tnp.upper() for tnp in TNP_SWE_IDS}
    assert len(all_ids) == 22
    for factor_id in all_ids:
        assert _factor_display_name(factor_id)
        assert _factor_keywords(factor_id)


def test_factor_category_classifies_tnps_planets_and_personal_points():
    assert _factor_category("CUPIDO") == "transneptunian"
    assert _factor_category("MERCURY") == "planet"
    assert _factor_category("SUN") == "personal_point"


def test_planetary_pictures_kb_has_no_duplicate_pairs():
    pictures = _load_planetary_pictures()
    assert len(pictures) == 50
    for entry in pictures.values():
        assert entry["meaning_th"]
        assert entry["source_ref"]


def test_axis_meanings_kb_has_m_axis_paired_with_every_other_factor():
    axis_m = _load_axis_meanings()["M"]
    all_ids = set(_load_factors()) | {tnp.upper() for tnp in TNP_SWE_IDS}
    assert set(axis_m) == all_ids - {"M"}


# ---------- planetary picture detection (synthetic positions) ----------


def test_type1_picture_detected_when_factor_sits_on_a_midpoint():
    # M-KRONOS midpoint is 20; JUPITER sits right on it.
    positions = {"M": 0.0, "KRONOS": 40.0, "JUPITER": 20.0, "SATURN": 200.0}
    midpoints = _midpoint_matrix(positions)
    pictures = [
        p
        for p in _find_pictures(positions, PERSONAL_POINT_IDS)
        if p["type"] == "type1" and p["factors"] == frozenset({"M", "KRONOS", "JUPITER"})
    ]
    assert len(pictures) == 1
    assert pictures[0]["orb"] < 0.01
    assert midpoints[frozenset({"M", "KRONOS"})] == pytest.approx(20.0)


def test_type1_picture_out_of_orb_is_not_detected():
    positions = {"M": 0.0, "KRONOS": 40.0, "JUPITER": 25.0}  # 5° off the 20° midpoint
    pictures = _find_pictures(positions, PERSONAL_POINT_IDS)
    assert not any(p["factors"] == frozenset({"M", "KRONOS", "JUPITER"}) for p in pictures)


def test_type2_picture_detected_when_two_midpoints_coincide():
    # M/MOON midpoint = 10; VENUS/SUN midpoint = 10 too.
    positions = {"M": 0.0, "MOON": 20.0, "VENUS": 11.0, "SUN": 9.0}
    pictures = [
        p
        for p in _find_pictures(positions, PERSONAL_POINT_IDS)
        if p["type"] == "type2" and p["factors"] == frozenset({"M", "MOON", "VENUS", "SUN"})
    ]
    assert len(pictures) == 1


def test_type2_picture_requires_four_distinct_factors():
    positions = {"M": 0.0, "MOON": 20.0, "SUN": 10.0}
    pictures = _find_pictures(positions, PERSONAL_POINT_IDS)
    assert not any(p["type"] == "type2" for p in pictures)


def test_pictures_without_a_personal_point_are_filtered_out():
    # MERCURY/SATURN midpoint hit by VENUS — no personal point involved.
    positions = {"MERCURY": 0.0, "SATURN": 40.0, "VENUS": 20.0}
    pictures = _find_pictures(positions, PERSONAL_POINT_IDS)
    assert pictures == []


def test_picture_finding_uses_glossary_meaning_when_a_pair_matches():
    picture = {
        "type": "type1",
        "pair": ("MERCURY", "SATURN"),
        "hit": "SUN",
        "factors": frozenset({"MERCURY", "SATURN", "SUN"}),
        "orb": 0.2,
    }
    finding = _picture_finding(picture)
    assert "การเดินทาง" in finding.meaning
    assert finding.weight == 0.75


def test_picture_finding_falls_back_to_generic_composition_when_unmatched():
    picture = {
        "type": "type1",
        "pair": ("VENUS", "JUPITER"),
        "hit": "MOON",
        "factors": frozenset({"VENUS", "JUPITER", "MOON"}),
        "orb": 0.2,
    }
    finding = _picture_finding(picture)
    assert finding.weight == 0.45
    assert "เชื่อมโยงกันในดวงชะตา" in finding.meaning


def test_picture_finding_appends_axis_m_note_when_m_is_involved():
    picture = {
        "type": "type1",
        "pair": ("M", "SATURN"),
        "hit": "SUN",
        "factors": frozenset({"M", "SATURN", "SUN"}),
        "orb": 0.2,
    }
    finding = _picture_finding(picture)
    assert "บนแกน M" in finding.meaning
