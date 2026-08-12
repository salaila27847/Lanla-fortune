"""Tests for the login-gated reading history feature: the internal-secret
auth dependency and per-user persistence of /api/reading + /api/readings.
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


def _auth_headers(user_id: str, email: str, secret: str = "test-internal-secret") -> dict:
    return {"X-Internal-Secret": secret, "X-User-Id": user_id, "X-User-Email": email}


async def _fake_synthesize(uranian: EngineResult, tarot: EngineResult, oracle: EngineResult):
    return SynthesisOutput(
        final_reading="fake reading",
        convergent_themes=["x"],
        divergent_notes=[],
        per_engine_breakdown={"uranian": uranian, "tarot": tarot, "oracle": oracle},
    )


@pytest.fixture(autouse=True)
def _mock_synthesize(monkeypatch):
    # Tests shouldn't hit the real Claude API — same spirit as
    # test_master_interpreter_fallback.py's monkeypatching of AsyncAnthropic.
    monkeypatch.setattr(main_module, "synthesize", _fake_synthesize)


async def test_missing_internal_secret_is_unauthorized(client):
    res = await client.get("/api/readings", headers={"X-User-Id": "u1", "X-User-Email": "u1@x.com"})
    assert res.status_code == 401


async def test_wrong_internal_secret_is_unauthorized(client):
    res = await client.get("/api/readings", headers=_auth_headers("u1", "u1@x.com", secret="wrong"))
    assert res.status_code == 401


async def test_post_reading_persists_row_for_the_authenticated_user(client):
    res = await client.post(
        "/api/reading", json=BIRTH_DATA, headers=_auth_headers("sub-a", "a@x.com")
    )
    assert res.status_code == 200
    assert res.json()["final_reading"] == "fake reading"

    history = await client.get("/api/readings", headers=_auth_headers("sub-a", "a@x.com"))
    assert history.status_code == 200
    body = history.json()
    assert len(body) == 1
    assert body[0]["birth_data"]["place"] == "Chiang Mai"
    assert body[0]["synthesis"]["final_reading"] == "fake reading"


async def test_readings_are_isolated_between_users(client):
    await client.post(
        "/api/reading",
        json={**BIRTH_DATA, "place": "Chiang Mai"},
        headers=_auth_headers("sub-a", "a@x.com"),
    )
    await client.post(
        "/api/reading",
        json={**BIRTH_DATA, "place": "Phuket"},
        headers=_auth_headers("sub-b", "b@x.com"),
    )

    history_a = (
        await client.get("/api/readings", headers=_auth_headers("sub-a", "a@x.com"))
    ).json()
    history_b = (
        await client.get("/api/readings", headers=_auth_headers("sub-b", "b@x.com"))
    ).json()

    assert [r["birth_data"]["place"] for r in history_a] == ["Chiang Mai"]
    assert [r["birth_data"]["place"] for r in history_b] == ["Phuket"]


async def test_readings_ordered_newest_first(client):
    await client.post(
        "/api/reading",
        json={**BIRTH_DATA, "place": "First"},
        headers=_auth_headers("sub-a", "a@x.com"),
    )
    await client.post(
        "/api/reading",
        json={**BIRTH_DATA, "place": "Second"},
        headers=_auth_headers("sub-a", "a@x.com"),
    )

    history = (await client.get("/api/readings", headers=_auth_headers("sub-a", "a@x.com"))).json()
    assert [r["birth_data"]["place"] for r in history] == ["Second", "First"]
