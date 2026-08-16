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

PREVIOUS_SYNTHESIS = {
    "final_reading": "คำทำนายฉบับก่อนหน้า",
    "convergent_themes": [],
    "divergent_notes": [],
    "per_engine_breakdown": {
        "oracle": {
            "engine": "oracle",
            "summary": "s",
            "themes": ["t"],
            "raw_findings": [{"label": "l", "meaning": "m", "weight": 0.5}],
            "confidence": 0.5,
        }
    },
    "forecast": None,
    "oracle_question": None,
}


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


async def _fake_synthesize_followup(previous: SynthesisOutput, oracle: EngineResult, question: str):
    return SynthesisOutput(
        final_reading="fake follow-up reading",
        convergent_themes=[],
        divergent_notes=[],
        per_engine_breakdown={**previous.per_engine_breakdown, "oracle": oracle},
        forecast=previous.forecast,
        oracle_question=question,
    )


@pytest.fixture(autouse=True)
def _mock_synthesize(monkeypatch):
    # Tests shouldn't hit the real Gemini API — same spirit as
    # test_master_interpreter_fallback.py's monkeypatching of genai.Client.
    monkeypatch.setattr(main_module, "synthesize", _fake_synthesize)
    monkeypatch.setattr(main_module, "synthesize_followup", _fake_synthesize_followup)


async def test_missing_internal_secret_is_unauthorized(client):
    res = await client.get("/api/readings", headers={"X-User-Id": "u1", "X-User-Email": "u1@x.com"})
    assert res.status_code == 401


async def test_wrong_internal_secret_is_unauthorized(client):
    res = await client.get("/api/readings", headers=_auth_headers("u1", "u1@x.com", secret="wrong"))
    assert res.status_code == 401


async def test_post_reading_persists_row_for_the_authenticated_user(client):
    res = await client.post(
        "/api/reading", json={"birth_data": BIRTH_DATA}, headers=_auth_headers("sub-a", "a@x.com")
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
        json={"birth_data": {**BIRTH_DATA, "place": "Chiang Mai"}},
        headers=_auth_headers("sub-a", "a@x.com"),
    )
    await client.post(
        "/api/reading",
        json={"birth_data": {**BIRTH_DATA, "place": "Phuket"}},
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


async def test_reading_with_forecast_options_includes_forecast_in_response_and_history(client):
    res = await client.post(
        "/api/reading",
        json={
            "birth_data": BIRTH_DATA,
            "solar_arc": {"target_date": "2026-08-13"},
        },
        headers=_auth_headers("sub-a", "a@x.com"),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["forecast"] is not None
    assert body["forecast"]["solar_arc"] is not None
    assert body["forecast"]["transit"] is None

    history = (await client.get("/api/readings", headers=_auth_headers("sub-a", "a@x.com"))).json()
    assert history[0]["synthesis"]["forecast"]["solar_arc"] is not None


async def test_reading_without_forecast_options_has_null_forecast(client):
    res = await client.post(
        "/api/reading", json={"birth_data": BIRTH_DATA}, headers=_auth_headers("sub-a", "a@x.com")
    )
    assert res.status_code == 200
    assert res.json()["forecast"] is None


async def test_readings_ordered_newest_first(client):
    await client.post(
        "/api/reading",
        json={"birth_data": {**BIRTH_DATA, "place": "First"}},
        headers=_auth_headers("sub-a", "a@x.com"),
    )
    await client.post(
        "/api/reading",
        json={"birth_data": {**BIRTH_DATA, "place": "Second"}},
        headers=_auth_headers("sub-a", "a@x.com"),
    )

    history = (await client.get("/api/readings", headers=_auth_headers("sub-a", "a@x.com"))).json()
    assert [r["birth_data"]["place"] for r in history] == ["Second", "First"]


async def test_reading_requires_at_least_one_discipline(client):
    res = await client.post("/api/reading", json={}, headers=_auth_headers("sub-a", "a@x.com"))
    assert res.status_code == 422


async def test_reading_forecast_option_without_birth_data_is_rejected(client):
    res = await client.post(
        "/api/reading",
        json={"tarot": {"spread": "three_card"}, "solar_arc": {"target_date": "2026-08-13"}},
        headers=_auth_headers("sub-a", "a@x.com"),
    )
    assert res.status_code == 422


ORACLE_PICKS_5 = ["animal_horse", "animal_turtle", "shadow_dry_well", "animal_ox", "animal_rabbit"]
ORACLE_PICKS_4 = ["animal_horse", "animal_turtle", "shadow_dry_well", "animal_ox"]
CELTIC_CROSS_PICKS = [{"card_id": f"major_{i:02d}", "reversed": False} for i in range(10)]


async def test_reading_oracle_only_requires_a_question(client):
    res = await client.post(
        "/api/reading",
        json={"oracle": {"picks": ORACLE_PICKS_5}},
        headers=_auth_headers("sub-a", "a@x.com"),
    )
    assert res.status_code == 422


async def test_reading_oracle_picks_out_of_range_is_rejected(client):
    res = await client.post(
        "/api/reading",
        json={"oracle": {"picks": ORACLE_PICKS_5[:2], "question": "จะเป็นอย่างไร"}},
        headers=_auth_headers("sub-a", "a@x.com"),
    )
    assert res.status_code == 422


async def test_reading_tarot_and_oracle_only_persists_null_birth_data(client):
    res = await client.post(
        "/api/reading",
        json={
            "tarot": {"spread": "celtic_cross", "picks": CELTIC_CROSS_PICKS},
            "oracle": {"picks": ORACLE_PICKS_5},
        },
        headers=_auth_headers("sub-a", "a@x.com"),
    )
    assert res.status_code == 200
    body = res.json()
    assert set(body["per_engine_breakdown"].keys()) == {"tarot", "oracle"}

    history = (await client.get("/api/readings", headers=_auth_headers("sub-a", "a@x.com"))).json()
    assert history[0]["birth_data"] is None


async def test_reading_oracle_only_with_question_includes_it_in_response(client):
    res = await client.post(
        "/api/reading",
        json={"oracle": {"picks": ORACLE_PICKS_4, "question": "ความรักของฉันจะเป็นอย่างไร"}},
        headers=_auth_headers("sub-a", "a@x.com"),
    )
    assert res.status_code == 200
    body = res.json()
    assert set(body["per_engine_breakdown"].keys()) == {"oracle"}
    assert body["oracle_question"] == "ความรักของฉันจะเป็นอย่างไร"


async def test_reading_follow_up_persists_with_null_birth_data(client):
    res = await client.post(
        "/api/reading/follow-up",
        json={
            "previous": PREVIOUS_SYNTHESIS,
            "question": "แล้วเรื่องงานล่ะ",
            "oracle_picks": ORACLE_PICKS_5,
        },
        headers=_auth_headers("sub-a", "a@x.com"),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["final_reading"] == "fake follow-up reading"
    assert body["oracle_question"] == "แล้วเรื่องงานล่ะ"

    history = (await client.get("/api/readings", headers=_auth_headers("sub-a", "a@x.com"))).json()
    assert history[0]["birth_data"] is None
    assert history[0]["synthesis"]["final_reading"] == "fake follow-up reading"


async def test_draw_oracle_deck_returns_full_shuffled_deck(client):
    res = await client.post("/api/oracle/draw", json={}, headers=_auth_headers("sub-a", "a@x.com"))
    assert res.status_code == 200
    cards = res.json()["cards"]
    assert len(cards) == 88
    assert len({c["card_id"] for c in cards}) == 88
    assert all({"name_th", "category_th", "meaning", "keywords"} <= c.keys() for c in cards)


async def test_draw_tarot_deck_returns_full_shuffled_deck_and_positions(client):
    res = await client.post(
        "/api/tarot/draw", json={"spread": "three_card"}, headers=_auth_headers("sub-a", "a@x.com")
    )
    assert res.status_code == 200
    body = res.json()
    assert body["positions"] == ["อดีต", "ปัจจุบัน", "อนาคต"]
    assert len(body["cards"]) == 78
    assert len({c["card_id"] for c in body["cards"]}) == 78


async def test_draw_tarot_deck_unknown_spread_is_rejected(client):
    res = await client.post(
        "/api/tarot/draw",
        json={"spread": "no-such-spread"},
        headers=_auth_headers("sub-a", "a@x.com"),
    )
    assert res.status_code == 422


async def test_reading_oracle_duplicate_pick_is_rejected(client):
    res = await client.post(
        "/api/reading",
        json={"oracle": {"picks": ["animal_horse", "animal_horse", "animal_ox"], "question": "q"}},
        headers=_auth_headers("sub-a", "a@x.com"),
    )
    assert res.status_code == 422


async def test_reading_oracle_unknown_card_id_is_rejected(client):
    res = await client.post(
        "/api/reading",
        json={
            "oracle": {"picks": ["not-a-real-card", "animal_ox", "animal_rabbit"], "question": "q"}
        },
        headers=_auth_headers("sub-a", "a@x.com"),
    )
    assert res.status_code == 422


async def test_reading_tarot_pick_count_mismatch_is_rejected(client):
    res = await client.post(
        "/api/reading",
        json={"tarot": {"spread": "three_card", "picks": CELTIC_CROSS_PICKS[:2]}},
        headers=_auth_headers("sub-a", "a@x.com"),
    )
    assert res.status_code == 422
