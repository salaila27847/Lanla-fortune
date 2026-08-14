"""Tests for the Phase 6 QA requirement: Gemini API timeout/failure must
have a fallback instead of surfacing a raw 500 to the user.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest
from google.genai import errors

from app.core.schema import (
    EngineResult,
    Finding,
    ForecastResponse,
    LunarReturnResult,
    PictureResult,
    SolarArcResult,
)
from app.synthesis import master_interpreter
from app.synthesis.master_interpreter import (
    _fallback_followup,
    _fallback_synthesis,
    synthesize,
    synthesize_followup,
)


def _make_result(engine: str, themes: list[str], summary: str = "summary") -> EngineResult:
    return EngineResult(
        engine=engine,  # type: ignore[arg-type]
        summary=summary,
        themes=themes,
        raw_findings=[Finding(label="x", meaning="y", weight=0.5)],
        confidence=0.5,
    )


def _make_forecast() -> ForecastResponse:
    return ForecastResponse(
        solar_arc=SolarArcResult(
            arc_degrees=12.3,
            pictures=[
                PictureResult(
                    type="type1",
                    label="Sun/Moon = Venus",
                    factors=["r:MOON", "r:SUN", "d:VENUS"],
                    orb=0.1,
                )
            ],
        ),
        lunar_return=LunarReturnResult(return_at=datetime(2026, 9, 1, tzinfo=timezone.utc)),
    )


def test_fallback_convergent_themes_require_at_least_two_engines():
    uranian = _make_result("uranian", ["การเปลี่ยนแปลง", "การงาน"])
    tarot = _make_result("tarot", ["การเปลี่ยนแปลง", "ความรัก"])
    oracle = _make_result("oracle", ["ความไว้วางใจ"])

    result = _fallback_synthesis(uranian, tarot, oracle)

    assert result.convergent_themes == ["การเปลี่ยนแปลง"]
    assert len(result.divergent_notes) == 3
    assert result.per_engine_breakdown == {"uranian": uranian, "tarot": tarot, "oracle": oracle}
    assert "ไม่พร้อมใช้งานชั่วคราว" in result.final_reading


def test_fallback_never_invents_meaning_beyond_engine_summaries():
    uranian = _make_result("uranian", [], summary="U summary")
    tarot = _make_result("tarot", [], summary="T summary")
    oracle = _make_result("oracle", [], summary="O summary")

    result = _fallback_synthesis(uranian, tarot, oracle)

    assert "U summary" in result.final_reading
    assert "T summary" in result.final_reading


def test_fallback_includes_forecast_picture_labels_when_present():
    uranian = _make_result("uranian", [], summary="U summary")
    tarot = _make_result("tarot", [], summary="T summary")
    oracle = _make_result("oracle", [], summary="O summary")
    forecast = _make_forecast()

    result = _fallback_synthesis(uranian, tarot, oracle, forecast)

    assert "Sun/Moon = Venus" in result.final_reading
    assert "2026-09-01" in result.final_reading
    assert result.forecast == forecast


def test_fallback_omits_forecast_section_when_absent():
    uranian = _make_result("uranian", [], summary="U summary")
    tarot = _make_result("tarot", [], summary="T summary")
    oracle = _make_result("oracle", [], summary="O summary")

    result = _fallback_synthesis(uranian, tarot, oracle)

    assert "ข้อมูลการพยากรณ์ล่วงหน้า" not in result.final_reading
    assert result.forecast is None
    assert "O summary" in result.final_reading
    assert result.convergent_themes == []
    assert result.divergent_notes == []


class _FakeModels:
    async def generate_content(self, *args, **kwargs):
        raise TypeError("simulated missing/invalid API key")


class _FakeAio:
    def __init__(self):
        self.models = _FakeModels()


class _FakeGenAIClient:
    def __init__(self, *args, **kwargs):
        self.aio = _FakeAio()


@pytest.mark.asyncio
async def test_synthesize_falls_back_when_gemini_call_fails(monkeypatch):
    monkeypatch.setattr(master_interpreter.genai, "Client", _FakeGenAIClient)

    uranian = _make_result("uranian", ["ก"])
    tarot = _make_result("tarot", ["ก"])
    oracle = _make_result("oracle", ["ข"])

    result = await synthesize(uranian, tarot, oracle)

    assert "ไม่พร้อมใช้งานชั่วคราว" in result.final_reading
    assert result.convergent_themes == ["ก"]


class _FakeResponse:
    def __init__(self, parsed):
        self.parsed = parsed


def _make_fake_client(parsed):
    class _FakeModelsWithParsed:
        async def generate_content(self, *args, **kwargs):
            return _FakeResponse(parsed)

    class _FakeAioWithParsed:
        def __init__(self):
            self.models = _FakeModelsWithParsed()

    class _FakeGenAIClientWithParsed:
        def __init__(self, *args, **kwargs):
            self.aio = _FakeAioWithParsed()

    return _FakeGenAIClientWithParsed


@pytest.mark.asyncio
async def test_synthesize_uses_gemini_structured_output(monkeypatch):
    # response_schema makes the SDK itself validate/parse the response
    # (response.parsed) instead of us hand-parsing response.text — this
    # replaced three rounds of chasing individual malformed-JSON symptoms
    # (truncation, trailing content, syntax errors) with one systemic fix.
    fake_parsed = master_interpreter._LLMSynthesis(
        final_reading="ok", convergent_themes=["ก"], divergent_notes=[]
    )
    monkeypatch.setattr(master_interpreter.genai, "Client", _make_fake_client(fake_parsed))

    uranian = _make_result("uranian", ["ก"])
    tarot = _make_result("tarot", ["ก"])
    oracle = _make_result("oracle", ["ข"])

    result = await synthesize(uranian, tarot, oracle)

    assert result.final_reading == "ok"
    assert result.convergent_themes == ["ก"]
    assert "ไม่พร้อมใช้งานชั่วคราว" not in result.final_reading


@pytest.mark.asyncio
async def test_synthesize_falls_back_when_gemini_returns_no_parsed_output(monkeypatch):
    monkeypatch.setattr(master_interpreter.genai, "Client", _make_fake_client(None))

    uranian = _make_result("uranian", ["ก"])
    tarot = _make_result("tarot", ["ก"])
    oracle = _make_result("oracle", ["ข"])

    result = await synthesize(uranian, tarot, oracle)

    assert "ไม่พร้อมใช้งานชั่วคราว" in result.final_reading
    assert result.convergent_themes == ["ก"]


@pytest.mark.asyncio
async def test_synthesize_includes_forecast_in_the_gemini_payload_and_response(monkeypatch):
    captured_contents = {}

    class _FakeModelsCapturing:
        async def generate_content(self, *args, **kwargs):
            captured_contents["value"] = kwargs["contents"]
            fake_parsed = master_interpreter._LLMSynthesis(
                final_reading="ok", convergent_themes=[], divergent_notes=[]
            )
            return _FakeResponse(fake_parsed)

    class _FakeAioCapturing:
        def __init__(self):
            self.models = _FakeModelsCapturing()

    class _FakeGenAIClientCapturing:
        def __init__(self, *args, **kwargs):
            self.aio = _FakeAioCapturing()

    monkeypatch.setattr(master_interpreter.genai, "Client", _FakeGenAIClientCapturing)

    uranian = _make_result("uranian", ["ก"])
    tarot = _make_result("tarot", ["ก"])
    oracle = _make_result("oracle", ["ข"])
    forecast = _make_forecast()

    result = await synthesize(uranian, tarot, oracle, forecast)

    payload = json.loads(captured_contents["value"])
    assert "forecast" in payload
    assert payload["forecast"]["solar_arc"]["arc_degrees"] == 12.3
    assert result.forecast == forecast


@pytest.mark.asyncio
async def test_synthesize_omits_forecast_from_payload_when_absent(monkeypatch):
    captured_contents = {}

    class _FakeModelsCapturing:
        async def generate_content(self, *args, **kwargs):
            captured_contents["value"] = kwargs["contents"]
            fake_parsed = master_interpreter._LLMSynthesis(
                final_reading="ok", convergent_themes=[], divergent_notes=[]
            )
            return _FakeResponse(fake_parsed)

    class _FakeAioCapturing:
        def __init__(self):
            self.models = _FakeModelsCapturing()

    class _FakeGenAIClientCapturing:
        def __init__(self, *args, **kwargs):
            self.aio = _FakeAioCapturing()

    monkeypatch.setattr(master_interpreter.genai, "Client", _FakeGenAIClientCapturing)

    uranian = _make_result("uranian", ["ก"])
    tarot = _make_result("tarot", ["ก"])
    oracle = _make_result("oracle", ["ข"])

    result = await synthesize(uranian, tarot, oracle)

    payload = json.loads(captured_contents["value"])
    assert "forecast" not in payload
    assert result.forecast is None


def test_fallback_with_only_one_engine_present():
    oracle = _make_result("oracle", ["ก"], summary="O summary")

    result = _fallback_synthesis(oracle=oracle)

    assert result.per_engine_breakdown == {"oracle": oracle}
    assert result.convergent_themes == []
    assert "O summary" in result.final_reading


def test_fallback_includes_oracle_question_when_present():
    oracle = _make_result("oracle", [], summary="O summary")

    result = _fallback_synthesis(oracle=oracle, oracle_question="ความรักจะเป็นอย่างไร")

    assert result.oracle_question == "ความรักจะเป็นอย่างไร"
    assert "ความรักจะเป็นอย่างไร" in result.final_reading


@pytest.mark.asyncio
async def test_synthesize_with_only_oracle_engine_omits_other_keys_from_payload(monkeypatch):
    captured_contents = {}

    class _FakeModelsCapturing:
        async def generate_content(self, *args, **kwargs):
            captured_contents["value"] = kwargs["contents"]
            fake_parsed = master_interpreter._LLMSynthesis(
                final_reading="ok", convergent_themes=[], divergent_notes=[]
            )
            return _FakeResponse(fake_parsed)

    class _FakeAioCapturing:
        def __init__(self):
            self.models = _FakeModelsCapturing()

    class _FakeGenAIClientCapturing:
        def __init__(self, *args, **kwargs):
            self.aio = _FakeAioCapturing()

    monkeypatch.setattr(master_interpreter.genai, "Client", _FakeGenAIClientCapturing)

    oracle = _make_result("oracle", ["ก"])

    result = await synthesize(oracle=oracle, oracle_question="วันนี้จะเป็นอย่างไร")

    payload = json.loads(captured_contents["value"])
    assert set(payload.keys()) == {"oracle", "oracle_question"}
    assert result.per_engine_breakdown == {"oracle": oracle}
    assert result.oracle_question == "วันนี้จะเป็นอย่างไร"


@pytest.mark.asyncio
async def test_synthesize_followup_uses_gemini_and_merges_new_oracle_into_breakdown(monkeypatch):
    previous_oracle = _make_result("oracle", ["เก่า"], summary="old oracle summary")
    previous = master_interpreter.SynthesisOutput(
        final_reading="คำทำนายเดิม",
        convergent_themes=[],
        divergent_notes=[],
        per_engine_breakdown={"oracle": previous_oracle},
    )
    new_oracle = _make_result("oracle", ["ใหม่"], summary="new oracle summary")

    fake_parsed = master_interpreter._LLMSynthesis(
        final_reading="ต่อเนื่องจากเดิม", convergent_themes=[], divergent_notes=[]
    )
    monkeypatch.setattr(master_interpreter.genai, "Client", _make_fake_client(fake_parsed))

    result = await synthesize_followup(previous, new_oracle, "แล้วเรื่องงานล่ะ")

    assert result.final_reading == "ต่อเนื่องจากเดิม"
    assert result.per_engine_breakdown == {"oracle": new_oracle}
    assert result.oracle_question == "แล้วเรื่องงานล่ะ"


@pytest.mark.asyncio
async def test_synthesize_followup_falls_back_when_gemini_call_fails(monkeypatch):
    monkeypatch.setattr(master_interpreter.genai, "Client", _FakeGenAIClient)

    previous = master_interpreter.SynthesisOutput(
        final_reading="คำทำนายเดิม",
        convergent_themes=[],
        divergent_notes=[],
        per_engine_breakdown={},
    )
    new_oracle = _make_result("oracle", ["ใหม่"], summary="new oracle summary")

    result = await synthesize_followup(previous, new_oracle, "แล้วเรื่องงานล่ะ")

    assert "คำทำนายเดิม" in result.final_reading
    assert "new oracle summary" in result.final_reading
    assert result.oracle_question == "แล้วเรื่องงานล่ะ"


def test_fallback_followup_appends_new_oracle_to_previous_reading():
    previous = master_interpreter.SynthesisOutput(
        final_reading="คำทำนายเดิม",
        convergent_themes=["x"],
        divergent_notes=[],
        per_engine_breakdown={},
    )
    new_oracle = _make_result("oracle", [], summary="new oracle summary")

    result = _fallback_followup(previous, new_oracle, "คำถามเพิ่มเติม")

    assert result.final_reading.startswith("คำทำนายเดิม")
    assert "new oracle summary" in result.final_reading
    assert result.convergent_themes == ["x"]
    assert result.per_engine_breakdown == {"oracle": new_oracle}
    assert result.oracle_question == "คำถามเพิ่มเติม"


def _server_error(code: int = 503) -> errors.ServerError:
    return errors.ServerError(code, {"error": {"message": "high demand", "status": "UNAVAILABLE"}})


def _client_error(code: int = 400) -> errors.ClientError:
    return errors.ClientError(
        code, {"error": {"message": "bad request", "status": "INVALID_ARGUMENT"}}
    )


def _fake_client_with_call_log(behaviors: list):
    """behaviors: list of exceptions to raise, or None to return a
    successful parsed response, one per call to generate_content."""
    calls = {"count": 0, "configs": []}

    class _FakeModelsSequenced:
        async def generate_content(self, *args, **kwargs):
            calls["configs"].append(kwargs["config"])
            behavior = behaviors[calls["count"]]
            calls["count"] += 1
            if behavior is not None:
                raise behavior
            fake_parsed = master_interpreter._LLMSynthesis(
                final_reading="recovered", convergent_themes=[], divergent_notes=[]
            )
            return _FakeResponse(fake_parsed)

    class _FakeAioSequenced:
        def __init__(self):
            self.models = _FakeModelsSequenced()

    class _FakeGenAIClientSequenced:
        def __init__(self, *args, **kwargs):
            self.aio = _FakeAioSequenced()

    return _FakeGenAIClientSequenced, calls


def _mock_sleep(monkeypatch, record: list | None = None):
    async def _fake_sleep(seconds):
        if record is not None:
            record.append(seconds)

    monkeypatch.setattr(master_interpreter.asyncio, "sleep", _fake_sleep)


@pytest.mark.asyncio
async def test_synthesize_retries_retryable_error_then_succeeds(monkeypatch):
    sleep_calls: list = []
    _mock_sleep(monkeypatch, record=sleep_calls)
    client_cls, calls = _fake_client_with_call_log([_server_error(503), None])
    monkeypatch.setattr(master_interpreter.genai, "Client", client_cls)

    oracle = _make_result("oracle", ["ก"])

    result = await synthesize(oracle=oracle)

    assert result.final_reading == "recovered"
    assert calls["count"] == 2
    assert len(sleep_calls) == 1


@pytest.mark.asyncio
async def test_synthesize_falls_back_after_exhausting_retries_on_persistent_5xx(monkeypatch):
    _mock_sleep(monkeypatch)
    client_cls, calls = _fake_client_with_call_log(
        [_server_error(503), _server_error(503), _server_error(503)]
    )
    monkeypatch.setattr(master_interpreter.genai, "Client", client_cls)

    oracle = _make_result("oracle", ["ก"], summary="O summary")

    result = await synthesize(oracle=oracle)

    assert "ไม่พร้อมใช้งานชั่วคราว" in result.final_reading
    assert calls["count"] == master_interpreter._MAX_ATTEMPTS


@pytest.mark.asyncio
async def test_synthesize_does_not_retry_non_retryable_client_error(monkeypatch):
    _mock_sleep(monkeypatch)
    client_cls, calls = _fake_client_with_call_log([_client_error(400)])
    monkeypatch.setattr(master_interpreter.genai, "Client", client_cls)

    oracle = _make_result("oracle", ["ก"], summary="O summary")

    result = await synthesize(oracle=oracle)

    assert "ไม่พร้อมใช้งานชั่วคราว" in result.final_reading
    assert calls["count"] == 1


@pytest.mark.asyncio
async def test_generate_synthesis_disables_automatic_function_calling(monkeypatch):
    client_cls, calls = _fake_client_with_call_log([None])
    monkeypatch.setattr(master_interpreter.genai, "Client", client_cls)

    oracle = _make_result("oracle", ["ก"])

    await synthesize(oracle=oracle)

    assert calls["configs"][0].automatic_function_calling.disable is True
