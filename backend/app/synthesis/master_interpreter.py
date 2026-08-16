"""Master Interpreter — the synthesis layer ("หัวหน้าทีมหลัก").

Takes whichever of the 3 engines' EngineResult objects the user chose to
run (see CLAUDE.md — each discipline is independently skippable now) —
plus, optionally, forecast data (Solar Arc/Transit/Lunar Return/
Relocation, from app/modules/uranian/solar_arc.py and transit.py) and an
oracle_question the user typed before drawing — and asks Gemini to
cross-reference them into one reading. The rules below are load-bearing
— do not soften or remove them when editing the prompt:

  1. No personal bias — interpret only from the raw findings passed in.
  2. No user history — never reference anything outside this session's
     input (see CLAUDE.md, PRD.md section 4.4).
  3. Three-step method — convergence, then divergence, then
     complementary framing (see PRD.md section 4.4) — extended to weigh
     forecast data as a fourth, timing-focused layer when present, and
     skipped in favor of a focused single-discipline reading when only
     one engine ran.

If the Gemini call fails or times out (Phase 6 QA requirement), synthesize()
falls back to _fallback_synthesis(), which builds a SynthesisOutput directly
from the engines' own themes/summaries (and forecast's own picture labels)
— plain set overlap for convergence, no invented interpretation, so it
never violates rule 1 above either.

synthesize_followup() handles the separate "ask more" flow on the result
screen (POST /api/reading/follow-up): a newly-drawn oracle EngineResult
plus a follow-up question, synthesized as a priority continuation of a
previous SynthesisOutput the client already has — never data pulled back
from stored /history (same "no user history" rule, see FollowUpRequest).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os

import httpx
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
3. ข้อความที่ส่งมาจะมีเฉพาะ key ของศาสตร์ที่ผู้ใช้เลือกใช้เท่านั้น (uranian/tarot/oracle — อาจมีแค่
   1 หรือ 2 ใน 3 key นี้ เพราะผู้ใช้ข้ามศาสตร์ที่ไม่ต้องการได้) ห้ามอ้างถึงศาสตร์ที่ไม่มี key ส่งมา
   เลยแม้แต่น้อย:
   - ถ้ามีมากกว่า 1 ศาสตร์: วิเคราะห์ตามลำดับ 3 ขั้นตอนเสมอ
     ก) หาจุดร่วม (convergence) — ประเด็นที่ศาสตร์ต่างๆ ที่ส่งมาชี้ไปทางเดียวกัน
     ข) จัดการความขัดแย้ง (divergence) — อธิบายอย่างสมเหตุสมผล ไม่เลือกทิ้งศาสตร์ใดศาสตร์หนึ่ง
     ค) เติมเต็มมุมที่ขาด (complementary) — แต่ละศาสตร์เสริมมุมที่อีกศาสตร์ไม่ครอบคลุมอย่างไร
   - ถ้ามีศาสตร์เดียว: ไม่ต้องหาจุดร่วม/ความขัดแย้ง (convergent_themes/divergent_notes ปล่อยว่างได้)
     ให้ตีความศาสตร์นั้นแบบเจาะลึกแทน
4. ข้อความที่ส่งมาอาจมี key "forecast" เพิ่มเติมนอกเหนือจาก uranian/tarot/oracle — เป็นผล
   คำนวณ Solar Arc / Transit / Lunar Return / Relocation ล่วงหน้า (Uranian planetary
   pictures ที่ขับเคลื่อนด้วยเวลาหรือสถานที่ต่างจากตอนเกิด) ถ้ามี key นี้ ให้นำมาพิจารณาร่วมด้วย
   เป็น "ชั้นจังหวะเวลา" เสริม โดยใช้หลักการเดียวกันกับข้อ 3 ถ้าไม่มี key "forecast" มาเลย ไม่ต้องพูดถึง
5. ข้อความที่ส่งมาอาจมี key "oracle_question" — คำถามที่ผู้ใช้พิมพ์ไว้ก่อนจั่วไพ่ออราเคิลโดยเฉพาะ
   (มักมาคู่กับกรณีที่ใช้ไพ่ออราเคิลศาสตร์เดียว) ถ้ามี key นี้ ให้ใช้เป็นบริบทหลักในการตีความไพ่ออราเคิล
   และตอบคำถามนั้นให้ตรงประเด็นที่สุด
6. ห้ามนำความหมายดิบของแต่ละ finding (ไพ่/ตำแหน่งดาว/picture) มาแปะต่อกันเฉย ๆ ทีละข้อ —
   final_reading ต้องเป็นการสังเคราะห์ที่แปลความหมายดิบทั้งหมดให้เข้ากับบริบทของคำถามหรือสถานการณ์
   ผู้ใช้ เป็นคำอธิบาย/คำแนะนำเดียวที่ลื่นไหลเป็นเนื้อเดียวกัน ไม่ใช่สรุปความหมายทีละใบ/ทีละจุดแยกกัน
7. finding บางรายการ (โดยเฉพาะไพ่ออราเคิล) จะมี key "voice" เพิ่มเติม — เป็นคำพูดของไพ่ใบนั้นในมุมมอง
   บุคคลที่หนึ่ง ("ฉันคือ...") ใช้ "voice" เป็นแรงบันดาลใจให้ final_reading สื่อโทนเสียงและบุคลิกของ
   ไพ่ใบนั้นเวลาอ้างถึงมัน ราวกับไพ่กำลังพูดกับผู้ใช้โดยตรง แต่ห้ามคัดลอกข้อความใน "voice" มาแปะทั้ง
   ประโยคหรือทั้งย่อหน้า ต้องหลอมรวมโทนเสียงนั้นเป็นเนื้อเดียวกับคำทำนายที่สังเคราะห์แล้วอย่างเป็นธรรมชาติ
8. ต้องตอบเป็นภาษาไทยทุก field ในผลลัพธ์ (final_reading, convergent_themes, divergent_notes)
   ทับศัพท์ได้เฉพาะคำศัพท์เฉพาะทางที่ไม่มีคำแปลไทยที่ใช้กันทั่วไป (เช่น ชื่อเทคนิค Solar Arc,
   Transit หรือชื่อไพ่ทาโรต์ที่นิยมเรียกทับศัพท์) ห้ามตอบเป็นประโยคหรือข้อความยาวเป็นภาษาอังกฤษทั้งท่อน

ตอบกลับเป็น JSON เท่านั้น ตรงตาม schema:
{
  "final_reading": "...",
  "convergent_themes": ["..."],
  "divergent_notes": ["..."]
}
ห้ามมีข้อความอื่นนอกเหนือจาก JSON"""

FOLLOWUP_SYSTEM_PROMPT = """\
คุณคือหัวหน้าทีมนักพยากรณ์มืออาชีพคนเดิมที่เพิ่งให้คำทำนายไปแล้วในเซสชันนี้ ตอนนี้ผู้ใช้ถามคำถาม
เพิ่มเติมและจั่วไพ่ออราเคิลชุดใหม่มาเพื่อตอบคำถามนี้โดยเฉพาะ
กฎที่ต้องปฏิบัติตามอย่างเคร่งครัด:
1. ห้ามใส่ความเห็นส่วนตัวหรือความเชื่อของคุณเอง ตีความจากข้อมูลดิบที่ได้รับเท่านั้น
2. ห้ามอ้างอิงข้อมูลใดๆ นอกเหนือจากที่ส่งมาในข้อความนี้ (ไม่มีประวัติผู้ใช้จากภายนอกเซสชันนี้) —
   ข้อความจะมี key "previous_reading" ซึ่งเป็นคำทำนายฉบับก่อนหน้าในเซสชันเดียวกันนี้เท่านั้น ไม่ใช่
   ประวัติเก่าที่ดึงมาจากที่อื่น ใช้ได้เพื่อความต่อเนื่องเท่านั้น
3. ให้ความสำคัญกับ "new_oracle_cards" (ไพ่ออราเคิลชุดใหม่) เป็นหลักในการตอบ "question" —
   ใช้ "previous_reading" เป็นบริบทประกอบเพื่อให้คำทำนายต่อเนื่องกัน ไม่ใช่หัวข้อหลัก
4. เขียน final_reading ให้ต่อเนื่องเป็นธรรมชาติจากคำทำนายฉบับก่อนหน้า ไม่ใช่เริ่มต้นใหม่ทั้งหมด
5. ห้ามนำความหมายของไพ่แต่ละใบใน "new_oracle_cards" มาแปะต่อกันเฉย ๆ ทีละใบ — ต้องสังเคราะห์
   ความหมายทั้งหมดให้เป็นคำตอบเดียวที่ตรงกับ "question" ไม่ใช่รายการความหมายแยกทีละใบ
6. ไพ่บางใบใน "new_oracle_cards" จะมี key "voice" เพิ่มเติม — เป็นคำพูดของไพ่ใบนั้นในมุมมองบุคคลที่หนึ่ง
   ("ฉันคือ...") ใช้เป็นแรงบันดาลใจให้ final_reading สื่อโทนเสียงและบุคลิกของไพ่ใบนั้นเวลาอ้างถึงมัน
   แต่ห้ามคัดลอกข้อความใน "voice" มาแปะทั้งประโยคหรือทั้งย่อหน้า ต้องหลอมรวมเป็นเนื้อเดียวกับคำตอบ
7. ต้องตอบเป็นภาษาไทยทุก field ในผลลัพธ์ (final_reading, convergent_themes, divergent_notes)
   ทับศัพท์ได้เฉพาะคำศัพท์เฉพาะทางที่ไม่มีคำแปลไทยที่ใช้กันทั่วไป ห้ามตอบเป็นประโยคหรือข้อความยาว
   เป็นภาษาอังกฤษทั้งท่อน

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

# Gemini's own 503 message ("high demand... please try again later") says
# the fix is a retry, so transient 5xx/429 responses get a couple of quick
# retries before we give up and fall back — see _generate_synthesis().
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_MAX_ATTEMPTS = 3
_RETRY_BACKOFF_SECONDS = 1.0


class _LLMSynthesis(BaseModel):
    """Shape Gemini must produce — passed as response_schema so the SDK
    constrains generation to valid JSON matching this exactly, instead of
    us hand-parsing response.text (which drifted through three different
    malformed-JSON failure modes: truncation, trailing content, then
    plain syntax errors — a hand-rolled parser kept chasing symptoms)."""

    final_reading: str
    convergent_themes: list[str]
    divergent_notes: list[str]


async def _generate_synthesis(
    client: genai.Client, model: str, system_prompt: str, payload: dict[str, object]
) -> _LLMSynthesis:
    """Shared by synthesize() and synthesize_followup(): calls Gemini with
    response_schema=_LLMSynthesis, retrying transient 5xx/429 errors and
    httpx-level transport failures (read/connect timeouts etc. — these
    aren't wrapped into errors.APIError by the SDK, so they need their own
    except clause) with a short backoff before giving up. Raises on a
    non-retryable error or once attempts are exhausted — callers catch
    that and fall back to a non-LLM SynthesisOutput."""
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        # Raised from 4096 alongside re-enabling thinking below — dynamic
        # thinking needs headroom on top of the JSON output itself, or we
        # hit the same silent truncation that -1/AUTOMATIC caused before.
        max_output_tokens=8192,
        # Dynamic thinking (-1, model decides how much to reason) — real
        # synthesis of multiple raw findings into one answer needs it,
        # versus thinking_budget=0 which produced shallow paraphrasing of
        # each finding's meaning back-to-back instead (see SYSTEM_PROMPT
        # rule 6 / FOLLOWUP_SYSTEM_PROMPT rule 5).
        thinking_config=types.ThinkingConfig(thinking_budget=-1),
        response_mime_type="application/json",
        response_schema=_LLMSynthesis,
        http_options=types.HttpOptions(timeout=int(SYNTHESIS_TIMEOUT_SECONDS * 1000)),
        # We never pass tools/function declarations, so the SDK's automatic
        # function-calling wrapper has nothing to do here — disabling it
        # also silences its one-time "direct use of AFC is not recommended"
        # log warning, which otherwise fires on every process's first call.
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    contents = json.dumps(payload, ensure_ascii=False)

    for attempt in range(_MAX_ATTEMPTS):
        try:
            response = await client.aio.models.generate_content(
                model=model, contents=contents, config=config
            )
            parsed = response.parsed
            if not isinstance(parsed, _LLMSynthesis):
                raise TypeError(f"Gemini returned no valid parsed output (got {parsed!r})")
            return parsed
        except errors.APIError as exc:
            last_attempt = attempt == _MAX_ATTEMPTS - 1
            if exc.code not in _RETRYABLE_STATUS_CODES or last_attempt:
                raise
            logger.warning(
                "Gemini call failed with retryable error (attempt %d/%d), retrying: %s",
                attempt + 1,
                _MAX_ATTEMPTS,
                exc,
            )
            await asyncio.sleep(_RETRY_BACKOFF_SECONDS * (attempt + 1))
        except httpx.TransportError as exc:
            # Read/connect/write timeouts, connection resets, etc. — raised
            # directly by httpx (the SDK's HTTP transport), never wrapped
            # into errors.APIError, so this needs its own except clause or
            # it crashes the request with an unhandled 500 instead of
            # retrying/falling back like every other Gemini failure mode.
            last_attempt = attempt == _MAX_ATTEMPTS - 1
            if last_attempt:
                raise
            logger.warning(
                "Gemini call failed with a transport error (attempt %d/%d), retrying: %s",
                attempt + 1,
                _MAX_ATTEMPTS,
                exc,
            )
            await asyncio.sleep(_RETRY_BACKOFF_SECONDS * (attempt + 1))

    raise AssertionError("unreachable — loop always returns or raises")


async def synthesize(
    uranian: EngineResult | None = None,
    tarot: EngineResult | None = None,
    oracle: EngineResult | None = None,
    forecast: ForecastResponse | None = None,
    oracle_question: str | None = None,
) -> SynthesisOutput:
    # Only the disciplines the user actually chose end up in the payload —
    # ReadingRequest already guarantees at least one is present (see
    # schema.py's _validate_engine_selection).
    engines: dict[str, EngineResult] = {
        name: result
        for name, result in (("uranian", uranian), ("tarot", tarot), ("oracle", oracle))
        if result is not None
    }

    client = genai.Client()  # reads GEMINI_API_KEY (or GOOGLE_API_KEY) from env
    model = os.environ.get("SYNTHESIS_MODEL", "gemini-3.1-flash-lite")

    payload: dict[str, object] = {name: result.model_dump() for name, result in engines.items()}
    if forecast is not None:
        payload["forecast"] = forecast.model_dump(mode="json")
    if oracle_question:
        payload["oracle_question"] = oracle_question

    try:
        parsed = await _generate_synthesis(client, model, SYSTEM_PROMPT, payload)

        return SynthesisOutput(
            final_reading=parsed.final_reading,
            convergent_themes=parsed.convergent_themes,
            divergent_notes=parsed.divergent_notes,
            per_engine_breakdown=engines,
            forecast=forecast,
            oracle_question=oracle_question,
        )
    except (errors.APIError, TypeError, ValueError, httpx.TransportError) as exc:
        # TypeError covers the genai SDK's own "missing/invalid API key"
        # failure, which it raises before ever making a request.
        logger.warning("Synthesis via Gemini failed, falling back to raw engine summary: %s", exc)
        return _fallback_synthesis(uranian, tarot, oracle, forecast, oracle_question)


async def synthesize_followup(
    previous: SynthesisOutput,
    oracle: EngineResult,
    question: str,
) -> SynthesisOutput:
    """The "ask more" flow (POST /api/reading/follow-up) — a fresh oracle
    draw takes priority, synthesized as a continuation of `previous`
    (this session's current reading, passed back by the client — see
    FollowUpRequest) rather than a from-scratch reading."""
    client = genai.Client()
    model = os.environ.get("SYNTHESIS_MODEL", "gemini-3.1-flash-lite")

    payload = {
        "previous_reading": previous.final_reading,
        "question": question,
        "new_oracle_cards": oracle.model_dump(),
    }

    try:
        parsed = await _generate_synthesis(client, model, FOLLOWUP_SYSTEM_PROMPT, payload)

        return SynthesisOutput(
            final_reading=parsed.final_reading,
            convergent_themes=parsed.convergent_themes,
            divergent_notes=parsed.divergent_notes,
            per_engine_breakdown={**previous.per_engine_breakdown, "oracle": oracle},
            forecast=previous.forecast,
            oracle_question=question,
        )
    except (errors.APIError, TypeError, ValueError, httpx.TransportError) as exc:
        logger.warning(
            "Follow-up synthesis via Gemini failed, falling back to raw oracle summary: %s", exc
        )
        return _fallback_followup(previous, oracle, question)


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
    uranian: EngineResult | None = None,
    tarot: EngineResult | None = None,
    oracle: EngineResult | None = None,
    forecast: ForecastResponse | None = None,
    oracle_question: str | None = None,
) -> SynthesisOutput:
    engines: dict[str, EngineResult] = {
        name: result
        for name, result in (("uranian", uranian), ("tarot", tarot), ("oracle", oracle))
        if result is not None
    }

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
        "ระบบสังเคราะห์คำทำนายอัตโนมัติไม่พร้อมใช้งานชั่วคราว นี่คือสรุปผลดิบจากศาสตร์ที่เลือกแทน:\n\n"
        + "\n\n".join(
            f"{_ENGINE_LABELS_TH[name]}: {result.summary}" for name, result in engines.items()
        )
    )
    if oracle_question:
        final_reading += f"\n\nคำถามที่ถาม: {oracle_question}"
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
        oracle_question=oracle_question,
    )


def _fallback_followup(
    previous: SynthesisOutput,
    oracle: EngineResult,
    question: str,
) -> SynthesisOutput:
    final_reading = (
        previous.final_reading + "\n\n---\n\nระบบสังเคราะห์คำทำนายอัตโนมัติไม่พร้อมใช้งานชั่วคราว "
        "นี่คือคำถามเพิ่มเติมและผลดิบจากไพ่ออราเคิลชุดใหม่แทน:\n\n"
        f"คำถามที่ถาม: {question}\n\nไพ่ออราเคิล: {oracle.summary}"
    )
    return SynthesisOutput(
        final_reading=final_reading,
        convergent_themes=previous.convergent_themes,
        divergent_notes=previous.divergent_notes,
        per_engine_breakdown={**previous.per_engine_breakdown, "oracle": oracle},
        forecast=previous.forecast,
        oracle_question=question,
    )
