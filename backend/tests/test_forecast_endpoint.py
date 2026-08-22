"""Tests for POST /api/forecast — the Uranian-only Solar Arc/Transit/
Lunar Return/Relocation add-ons. Unlike /api/reading, this endpoint
doesn't call synthesize() (raw picture tables, not an LLM reading) and
isn't persisted to history, so it needs neither the synthesize mock nor
a /api/readings round-trip.
"""

from __future__ import annotations

from app.core.schema import BirthData
from app.modules.uranian.engine import (
    _compute_positions,
    _house_cusps,
    _house_placements,
    _julian_day_ut,
)

BIRTH_DATA = {
    "date": "1990-07-22",
    "time": "15:52:00",
    "place": "Trang, Thailand",
    "latitude": 7.5563,
    "longitude": 99.6114,
    "timezone": "Asia/Bangkok",
}

BIRTH_DATA_NO_TIME = {**BIRTH_DATA, "time": None}


def _auth_headers(
    user_id: str = "sub-a", email: str = "a@x.com", secret: str = "test-internal-secret"
) -> dict:
    return {"X-Internal-Secret": secret, "X-User-Id": user_id, "X-User-Email": email}


async def test_forecast_requires_auth(client):
    res = await client.post("/api/forecast", json={"birth_data": BIRTH_DATA})
    assert res.status_code == 401


async def test_forecast_with_no_options_returns_all_null(client):
    res = await client.post(
        "/api/forecast", json={"birth_data": BIRTH_DATA}, headers=_auth_headers()
    )
    assert res.status_code == 200
    body = res.json()
    assert body == {"solar_arc": None, "transit": None, "lunar_return": None, "relocation": None}


async def test_forecast_solar_arc(client):
    res = await client.post(
        "/api/forecast",
        json={"birth_data": BIRTH_DATA, "solar_arc": {"target_date": "2026-08-13"}},
        headers=_auth_headers(),
    )
    assert res.status_code == 200
    body = res.json()["solar_arc"]
    assert 30 < body["arc_degrees"] < 40  # ~36 years old by this target date
    for picture in body["pictures"]:
        assert picture["type"] in {"type1", "type2"}
        assert picture["orb"] >= 0
        assert picture["label"]
        assert len(picture["factors"]) in {3, 4}
    # house_placements: the directed positions of the 18 house_meanings.yaml
    # factors, read against the *radix* house cusps (known birth time here).
    assert len(body["house_placements"]) == 18
    for placement in body["house_placements"]:
        assert 1 <= placement["house_number"] <= 12
        assert "directed" in placement["label"]


async def test_forecast_solar_arc_without_known_birth_time_has_no_house_placements(client):
    res = await client.post(
        "/api/forecast",
        json={"birth_data": BIRTH_DATA_NO_TIME, "solar_arc": {"target_date": "2026-08-13"}},
        headers=_auth_headers(),
    )
    assert res.status_code == 200
    assert res.json()["solar_arc"]["house_placements"] == []


async def test_forecast_transit(client):
    res = await client.post(
        "/api/forecast",
        json={"birth_data": BIRTH_DATA, "transit": {"target_date": "2026-08-13"}},
        headers=_auth_headers(),
    )
    assert res.status_code == 200
    body = res.json()["transit"]
    for picture in body["pictures"]:
        assert picture["orb"] <= 1.0  # transit's tight orb
    for hit in body["fine_timing"]:
        assert hit["orb"] <= 0.5  # fine-timing's even tighter orb
        assert hit["transit_factor"].startswith("t:")
    # house_placements: today's real transiting positions of the 18
    # house_meanings.yaml factors, read against the radix house cusps.
    assert len(body["house_placements"]) == 18
    for placement in body["house_placements"]:
        assert 1 <= placement["house_number"] <= 12
        assert "ปัจจุบัน" in placement["label"]


async def test_forecast_transit_without_known_birth_time_has_no_house_placements(client):
    res = await client.post(
        "/api/forecast",
        json={"birth_data": BIRTH_DATA_NO_TIME, "transit": {"target_date": "2026-08-13"}},
        headers=_auth_headers(),
    )
    assert res.status_code == 200
    assert res.json()["transit"]["house_placements"] == []


async def test_forecast_lunar_return(client):
    res = await client.post(
        "/api/forecast",
        json={"birth_data": BIRTH_DATA, "lunar_return": {"search_start": "2026-08-13"}},
        headers=_auth_headers(),
    )
    assert res.status_code == 200
    body = res.json()["lunar_return"]
    assert body["return_at"] >= "2026-08-13"


async def test_forecast_relocation(client):
    res = await client.post(
        "/api/forecast",
        json={
            "birth_data": BIRTH_DATA,
            "relocation": {"place": "Bangkok", "latitude": 13.7563, "longitude": 100.5018},
        },
        headers=_auth_headers(),
    )
    assert res.status_code == 200
    body = res.json()["relocation"]
    assert 0.0 <= body["ascendant"] < 360.0
    assert 0.0 <= body["midheaven"] < 360.0
    # house_placements: the (unmoved) radix planets, read against *new*
    # house cusps computed for the relocated site.
    assert len(body["house_placements"]) == 18
    for placement in body["house_placements"]:
        assert 1 <= placement["house_number"] <= 12
        assert "ที่พิกัดใหม่" in placement["label"]


async def test_forecast_relocation_house_placements_use_relocated_not_radix_cusps(client):
    relocation = {"place": "Bangkok", "latitude": 13.7563, "longitude": 100.5018}
    res = await client.post(
        "/api/forecast",
        json={"birth_data": BIRTH_DATA, "relocation": relocation},
        headers=_auth_headers(),
    )
    assert res.status_code == 200
    body = res.json()["relocation"]

    birth_data = BirthData(**BIRTH_DATA)
    jd, known_time = _julian_day_ut(birth_data)
    natal_positions = _compute_positions(jd, birth_data, known_time)
    radix_cusps = _house_cusps(jd, birth_data.latitude, birth_data.longitude)
    relocated_cusps = _house_cusps(jd, relocation["latitude"], relocation["longitude"])

    expected_relocated = _house_placements(natal_positions, relocated_cusps)
    expected_radix = _house_placements(natal_positions, radix_cusps)
    actual = {p["factor"]: p["house_number"] for p in body["house_placements"]}

    assert actual == expected_relocated
    # Sanity check the test itself isn't vacuous: this birth/relocation pair
    # must actually produce a different house layout, or a bug that silently
    # reused radix_cusps for relocation would pass undetected.
    assert actual != expected_radix


async def test_forecast_relocation_requires_known_birth_time(client):
    res = await client.post(
        "/api/forecast",
        json={
            "birth_data": BIRTH_DATA_NO_TIME,
            "relocation": {"place": "Bangkok", "latitude": 13.7563, "longitude": 100.5018},
        },
        headers=_auth_headers(),
    )
    assert res.status_code == 422


async def test_forecast_all_options_at_once(client):
    res = await client.post(
        "/api/forecast",
        json={
            "birth_data": BIRTH_DATA,
            "solar_arc": {"target_date": "2026-08-13"},
            "transit": {"target_date": "2026-08-13"},
            "lunar_return": {"search_start": "2026-08-13"},
            "relocation": {"place": "Bangkok", "latitude": 13.7563, "longitude": 100.5018},
        },
        headers=_auth_headers(),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["solar_arc"] is not None
    assert body["transit"] is not None
    assert body["lunar_return"] is not None
    assert body["relocation"] is not None
