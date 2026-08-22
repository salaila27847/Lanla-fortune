"""Tests for remembered birth data: GET/DELETE /api/profile/birth-data,
and /api/reading auto-saving birth_data onto the user's profile so a
returning user's form can be prefilled instead of retyped every time.
"""

from __future__ import annotations

import pytest

from app import main as main_module
from app.core.schema import EngineResult, SynthesisOutput

BIRTH_DATA = {
    "date": "1990-05-15",
    "time": "08:30:00",
    "place": "Chiang Mai",
    "latitude": 18.7883,
    "longitude": 98.9853,
    "timezone": "Asia/Bangkok",
}

OTHER_BIRTH_DATA = {
    "date": "1985-11-02",
    "time": "20:00:00",
    "place": "Phuket",
    "latitude": 7.8804,
    "longitude": 98.3923,
    "timezone": "Asia/Bangkok",
}

ORACLE_PICKS = ["animal_horse", "animal_turtle", "shadow_dry_well", "animal_ox", "animal_rabbit"]


def _auth_headers(user_id: str, email: str, secret: str = "test-internal-secret") -> dict:
    return {"X-Internal-Secret": secret, "X-User-Id": user_id, "X-User-Email": email}


async def _fake_synthesize(
    uranian: EngineResult | None = None,
    tarot: EngineResult | None = None,
    oracle: EngineResult | None = None,
    forecast=None,
    oracle_question: str | None = None,
):
    engines = {
        name: result
        for name, result in (("uranian", uranian), ("tarot", tarot), ("oracle", oracle))
        if result is not None
    }
    return SynthesisOutput(
        final_reading="fake reading",
        convergent_themes=["x"],
        divergent_notes=[],
        per_engine_breakdown=engines,
        forecast=forecast,
        oracle_question=oracle_question,
    )


@pytest.fixture(autouse=True)
def _mock_synthesize(monkeypatch):
    monkeypatch.setattr(main_module, "synthesize", _fake_synthesize)


async def test_get_saved_birth_data_requires_auth(client):
    res = await client.get("/api/profile/birth-data")
    assert res.status_code == 401


async def test_delete_saved_birth_data_requires_auth(client):
    res = await client.delete("/api/profile/birth-data")
    assert res.status_code == 401


async def test_get_saved_birth_data_is_null_before_any_reading(client):
    res = await client.get("/api/profile/birth-data", headers=_auth_headers("sub-a", "a@x.com"))
    assert res.status_code == 200
    assert res.json() is None


async def test_reading_with_birth_data_saves_it_for_profile_prefill(client):
    await client.post(
        "/api/reading", json={"birth_data": BIRTH_DATA}, headers=_auth_headers("sub-a", "a@x.com")
    )

    res = await client.get("/api/profile/birth-data", headers=_auth_headers("sub-a", "a@x.com"))
    assert res.status_code == 200
    assert res.json() == BIRTH_DATA


async def test_saved_birth_data_reflects_the_most_recent_reading(client):
    await client.post(
        "/api/reading", json={"birth_data": BIRTH_DATA}, headers=_auth_headers("sub-a", "a@x.com")
    )
    await client.post(
        "/api/reading",
        json={"birth_data": OTHER_BIRTH_DATA},
        headers=_auth_headers("sub-a", "a@x.com"),
    )

    res = await client.get("/api/profile/birth-data", headers=_auth_headers("sub-a", "a@x.com"))
    assert res.json() == OTHER_BIRTH_DATA


async def test_saved_birth_data_isolated_between_users(client):
    await client.post(
        "/api/reading", json={"birth_data": BIRTH_DATA}, headers=_auth_headers("sub-a", "a@x.com")
    )
    await client.post(
        "/api/reading",
        json={"birth_data": OTHER_BIRTH_DATA},
        headers=_auth_headers("sub-b", "b@x.com"),
    )

    saved_a = (
        await client.get("/api/profile/birth-data", headers=_auth_headers("sub-a", "a@x.com"))
    ).json()
    saved_b = (
        await client.get("/api/profile/birth-data", headers=_auth_headers("sub-b", "b@x.com"))
    ).json()

    assert saved_a == BIRTH_DATA
    assert saved_b == OTHER_BIRTH_DATA


async def test_reading_without_birth_data_does_not_clear_saved_profile(client):
    await client.post(
        "/api/reading", json={"birth_data": BIRTH_DATA}, headers=_auth_headers("sub-a", "a@x.com")
    )
    await client.post(
        "/api/reading",
        json={"oracle": {"picks": ORACLE_PICKS, "question": "จะเป็นอย่างไร"}},
        headers=_auth_headers("sub-a", "a@x.com"),
    )

    res = await client.get("/api/profile/birth-data", headers=_auth_headers("sub-a", "a@x.com"))
    assert res.json() == BIRTH_DATA


async def test_delete_saved_birth_data_clears_it(client):
    await client.post(
        "/api/reading", json={"birth_data": BIRTH_DATA}, headers=_auth_headers("sub-a", "a@x.com")
    )

    delete_res = await client.delete(
        "/api/profile/birth-data", headers=_auth_headers("sub-a", "a@x.com")
    )
    assert delete_res.status_code == 204

    res = await client.get("/api/profile/birth-data", headers=_auth_headers("sub-a", "a@x.com"))
    assert res.json() is None


async def test_delete_saved_birth_data_does_not_delete_past_readings(client):
    await client.post(
        "/api/reading", json={"birth_data": BIRTH_DATA}, headers=_auth_headers("sub-a", "a@x.com")
    )
    await client.delete("/api/profile/birth-data", headers=_auth_headers("sub-a", "a@x.com"))

    history = (await client.get("/api/readings", headers=_auth_headers("sub-a", "a@x.com"))).json()
    assert len(history) == 1
    assert history[0]["birth_data"]["place"] == "Chiang Mai"
