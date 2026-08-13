"""Tests for POST /api/forecast — the Uranian-only Solar Arc/Transit/
Lunar Return/Relocation add-ons. Unlike /api/reading, this endpoint
doesn't call synthesize() (raw picture tables, not an LLM reading) and
isn't persisted to history, so it needs neither the synthesize mock nor
a /api/readings round-trip.
"""

from __future__ import annotations

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
