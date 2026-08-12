"""Tests for the Phase 6 QA requirement: Gemini API timeout/failure must
have a fallback instead of surfacing a raw 500 to the user.
"""

from __future__ import annotations

import pytest

from app.core.schema import EngineResult, Finding
from app.synthesis import master_interpreter
from app.synthesis.master_interpreter import _fallback_synthesis, synthesize


def _make_result(engine: str, themes: list[str], summary: str = "summary") -> EngineResult:
    return EngineResult(
        engine=engine,  # type: ignore[arg-type]
        summary=summary,
        themes=themes,
        raw_findings=[Finding(label="x", meaning="y", weight=0.5)],
        confidence=0.5,
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
