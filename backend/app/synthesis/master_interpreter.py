"""Master Interpreter — the synthesis layer ("หัวหน้าทีมหลัก").

Takes the 3 engines' EngineResult objects — plus, optionally, forecast
data (Solar Arc/Transit/Lunar Return/Relocation, from app/modules/uranian/
solar_arc.py and transit.py) — and asks Gemini to cross-reference them
into one reading. The rules below are load-bearing — do not soften or
remove them when editing the prompt:

  1. No personal bias — interpret only from the raw findings passed in.
  2. No user history — never reference anything outside this session's
     input (see CLAUDE.md, PRD.md section 4.4).
  3. Three-step method — convergence, then divergence, then
     complementary framing (see PRD.md section 4.4) — extended to weigh
     forecast data as a fourth, timing-focused layer when present.

If the Gemini call fails or times out (Phase 6 QA requirement), synthesize()
falls back to _fallback_synthesis(), which builds a SynthesisOutput directly
from the engines' own themes/summaries (and forecast's own picture labels)
— plain set overlap for convergence, no invented interpretation, so it
never violates rule 1 above either.
"""

from __future__ import annotations

import json
import logging
import os

from google import genai
from google.genai import errors, types
from pydantic import BaseModel

from app.core.schema import EngineResult, ForecastResponse, SynthesisOutput

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
คุณคือหัวหน้าทีมนักพยากรณ์มืออาชีพ เชี่ยวชาญทั้งโหราศาสตร์ยูเรเนียน ไพ่ทาโรต์ และไพ่ออราเคิล
กฎที่ต้องปฏิบัติตามอย่างเคร่งครัด:
1. ห้ามใส่ความเห็นส่วนตัวหรือความเชื่อของคุณเอง ตีความจากข้อมูลดิบที่ได้รับเท่านั้น
2. ห้ามอ้างอิงข้อมูลใดๆ นอกเหนือจากที่ส่งมาในข้อความนี้ (ไม่มีประวัติผู้ใช้)
3. วิเคราะห์ตามลำดับ 3 ขั้นตอนเสมอ:
   ก) หาจุดร่วม (convergence) — ประเด็นที่ศาสตร์ต่างๆ ชี้ไปทางเดียวกัน
   ข) จัดการความขัดแย้ง (divergence) — อธิบายอย่างสมเหตุสมผล ไม่เลือกทิ้งศาสตร์ใดศาสตร์หนึ่ง
   ค) เติมเต็มมุมที่ขาด (complementary) — แต่ละศาสตร์เสริมมุมที่อีกศาสตร์ไม่ครอบคลุมอย่างไร
4. ข้อความที่ส่งมาอาจมี key "forecast" เพิ่มเติมนอกเหนือจาก uranian/tarot/oracle — เป็นผล
   คำนวณ Solar Arc / Transit / Lunar Return / Relocation ล่วงหน้า (Uranian planetary
   pictures ที่ขับเคลื่อนด้วยเวลาหรือสถานที่ต่างจากตอนเกิด) ถ้ามี key นี้ ให้นำมาพิจารณาร่วมกับ
   3 ศาสตร์หลักเป็น "ชั้นจังหวะเวลา" เสริม — ใช้หลัก 3 ขั้นตอนเดียวกัน (จุดร่วม/ความขัดแย้ง/เติมเต็ม)
   แต่ครอบคลุมทุกส่วนของ forecast ที่ส่งมาด้วย ไม่ใช่แค่ 3 ศาสตร์หลัก ถ้าไม่มี key "forecast" มาเลย
   ให้วิเคราะห์แค่ 3 ศาสตร์หลักตามปกติ

ตอบกลับเป็น JSON เท่านั้น ตรงตาม schema:
{
  "final_reading": "...",
  "convergent_themes": ["..."],
  "divergent_notes": ["..."]
}
ห้ามมีข้อความอื่นนอกเหนือจาก JSON"""

_ENGINE_LABELS_TH = {
    "uranian": "โหราศาสตร์ยูเรเนียน",
    "tarot": "ไพ่ทาโรต์",
    "oracle": "ไพ่ออราเคิล",
}

SYNTHESIS_TIMEOUT_SECONDS = 20.0


class _LLMSynthesis(BaseModel):
    """Shape Gemini must produce — passed as response_schema so the SDK
    constrains generation to valid JSON matching this exactly, instead of
    us hand-parsing response.text (which drifted through three different
    malformed-JSON failure modes: truncation, trailing content, then
    plain syntax errors — a hand-rolled parser kept chasing symptoms)."""

    final_reading: str
    convergent_themes: list[str]
    divergent_notes: list[str]


async def synthesize(
    uranian: EngineResult,
    tarot: EngineResult,
    oracle: EngineResult,
    forecast: ForecastResponse | None = None,
) -> SynthesisOutput:
    client = genai.Client()  # reads GEMINI_API_KEY (or GOOGLE_API_KEY) from env
    model = os.environ.get("SYNTHESIS_MODEL", "gemini-3.5-flash")

    payload = {
        "uranian": uranian.model_dump(),
        "tarot": tarot.model_dump(),
        "oracle": oracle.model_dump(),
    }
    if forecast is not None:
        payload["forecast"] = forecast.model_dump(mode="json")

    try:
        response = await client.aio.models.generate_content(
            model=model,
            contents=json.dumps(payload, ensure_ascii=False),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=4096,
                # Structured JSON output doesn't need extended reasoning, and
                # leaving this on AUTOMATIC (the model default) was silently
                # eating the token budget on thinking before ever emitting
                # the JSON, truncating it mid-string.
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                response_mime_type="application/json",
                response_schema=_LLMSynthesis,
                http_options=types.HttpOptions(timeout=int(SYNTHESIS_TIMEOUT_SECONDS * 1000)),
            ),
        )
        parsed = response.parsed
        if not isinstance(parsed, _LLMSynthesis):
            raise TypeError(f"Gemini returned no valid parsed output (got {parsed!r})")

        return SynthesisOutput(
            final_reading=parsed.final_reading,
            convergent_themes=parsed.convergent_themes,
            divergent_notes=parsed.divergent_notes,
            per_engine_breakdown={"uranian": uranian, "tarot": tarot, "oracle": oracle},
            forecast=forecast,
        )
    except (errors.APIError, TypeError, ValueError) as exc:
        # TypeError covers the genai SDK's own "missing/invalid API key"
        # failure, which it raises before ever making a request.
        logger.warning("Synthesis via Gemini failed, falling back to raw engine summary: %s", exc)
        return _fallback_synthesis(uranian, tarot, oracle, forecast)


def _forecast_summary_lines(forecast: ForecastResponse) -> list[str]:
    """Short raw-data lines for the fallback reading — same "no invented
    interpretation" spirit as the engine summaries below, just listing
    the tightest picture labels rather than composing prose about them."""
    lines: list[str] = []
    if forecast.solar_arc:
        top = [p.label for p in forecast.solar_arc.pictures[:3]]
        if top:
            lines.append(
                f"Solar Arc (ส่วนโค้ง {forecast.solar_arc.arc_degrees:.1f}°): " + " / ".join(top)
            )
    if forecast.transit:
        top = [p.label for p in forecast.transit.pictures[:3]]
        if top:
            lines.append("Transit: " + " / ".join(top))
    if forecast.lunar_return:
        lines.append(f"Lunar Return: {forecast.lunar_return.return_at.isoformat()}")
    if forecast.relocation:
        lines.append(
            f"Relocation: ลัคนา {forecast.relocation.ascendant:.1f}° "
            f"มิเดียม {forecast.relocation.midheaven:.1f}°"
        )
    return lines


def _fallback_synthesis(
    uranian: EngineResult,
    tarot: EngineResult,
    oracle: EngineResult,
    forecast: ForecastResponse | None = None,
) -> SynthesisOutput:
    engines = {"uranian": uranian, "tarot": tarot, "oracle": oracle}

    theme_counts: dict[str, int] = {}
    for result in engines.values():
        for theme in result.themes:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
    convergent_themes = [theme for theme, count in theme_counts.items() if count >= 2]

    divergent_notes = [
        f"{_ENGINE_LABELS_TH[name]}: {', '.join(result.themes)}"
        for name, result in engines.items()
        if result.themes
    ]

    final_reading = (
        "ระบบสังเคราะห์คำทำนายอัตโนมัติไม่พร้อมใช้งานชั่วคราว นี่คือสรุปผลดิบจากทั้ง 3 ศาสตร์แทน:\n\n"
        + "\n\n".join(
            f"{_ENGINE_LABELS_TH[name]}: {result.summary}" for name, result in engines.items()
        )
    )
    if forecast is not None:
        forecast_lines = _forecast_summary_lines(forecast)
        if forecast_lines:
            final_reading += "\n\nข้อมูลการพยากรณ์ล่วงหน้า:\n" + "\n".join(forecast_lines)

    return SynthesisOutput(
        final_reading=final_reading,
        convergent_themes=convergent_themes,
        divergent_notes=divergent_notes,
        per_engine_breakdown=engines,
        forecast=forecast,
    )
