"""Tests for the real Uranian engine (Phase 3 — replaces the Phase 1
mock). Keep test_engine_contracts.py's schema check separate; this file
checks the actual astronomical calculation and knowledge-base content.
"""

from __future__ import annotations

from datetime import date, time

import pytest

from app.core.schema import BirthData
from app.modules.uranian.engine import (
    TNP_SWE_IDS,
    _dial90_orb,
    _load_points,
    _load_signs,
    _midpoint,
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
