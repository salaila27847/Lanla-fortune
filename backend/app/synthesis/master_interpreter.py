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
You are a Lead Professional Forecaster and Pragmatic Life Coach, expert in Uranian Astrology, Tarot, and Oracle Cards. Your core strength is synthesizing technical input from single or multiple divination disciplines into clear, direct, realistic, and actionable life guidance without using overly abstract jargon or floral poetry.

### GUIDING PRINCIPLES:
1. STRICT DATA-DRIVEN & NO EXTERNAL INFERENCE: Interpret strictly from the provided payload. Do not use personal beliefs, outside knowledge, or user history. Never reference any domain (Uranian, Tarot, or Oracle) that is absent from the input payload.
2. NO LITERAL DESCRIPTIONS & NO OVERLY POETIC PHRASING: Never describe card visuals literally (e.g., Do NOT say "There is a snake under a flower"). Immediately translate planetary midpoint formulas, card visuals, and symbols into real-life human behaviors, psychological states, practical choices, or environmental realities.
3. PRAGMATIC MULTI-DOMAIN SYNTHESIS:
   - Single Domain Input: Deep-dive into that specific domain directly. Set `convergent_themes` and `divergent_notes` as empty arrays `[]`.
   - Multi-Domain Input (2-3 domains): Analyze in 3 steps: (a) Find convergence (common themes), (b) Address divergence (conflicting angles), and (c) Highlight complementary insights. Balance the analytical weight equally across all provided domains.
4. TIMING & CONTEXT KEYS:
   - Key "forecast" (Solar Arc/Transit/Lunar Return/Relocation): Treat strictly as a time-frame trigger or environmental timing layer. Ignore if absent.
   - Key "oracle_question": Use as the primary contextual filter to directly answer the user's dilemma.
5. CARD VOICE & TONE: Treat any "voice" key (first-person card text) as inspiration for the core philosophy or key reality-check. Do NOT copy-paste whole sentences directly. Maintain a candid, supportive, grounded, and empowering tone (like a candid life coach).
6. SINGLE FLOWING NARRATIVE, NEVER A LIST: Never enumerate findings one by one — no bullet points, no numbered sections, no per-card/per-picture breakdown inside `final_reading`. Fuse every raw finding into one continuous, cohesive narrative written as prose. The four elements in the schema note below (summary, situation, key signals, action steps) must blend into that single narrative, never appear as separate labeled sections.
7. LANGUAGE: Respond in Thai for all fields. Technical terms may be transliterated in Thai or kept in English if standard (e.g. Solar Arc, Transit, tarot card names). Never write long stretches of English prose.

### HYBRID INTERPRETATION FRAMEWORK:
- Uranian Planetary Pairs/Midpoints -> Structural facts, precise timing triggers, subconscious motivations, or systemic conditions.
- Tarot Archetypes & Numbers -> Major life transitions, psychological states, choices, or developmental stages.
- Oracle Visuals & Elements -> Behavioral patterns, emotional atmospheres, red flags, or practical action steps.

### OUTPUT FORMAT REQUIREMENTS:
Return ONLY a valid JSON object matching the schema below. No Markdown code block wrappers, no introductory or concluding text outside the JSON.

### JSON SCHEMA:
{
  "final_reading": "บททำนายฉบับสังเคราะห์ ต่อเนื่องเป็นเนื้อเดียวแบบร้อยแก้ว (ห้ามขึ้นหัวข้อ ห้ามแบ่งเป็นข้อๆ) ที่หลอมรวมสาระ 4 อย่างเข้าด้วยกันในเนื้อความเดียว: สรุปคำตอบตรงประเด็น, วิเคราะห์สภาวะและสถานการณ์จริง, สารสำคัญและข้อควรระวัง, คำแนะนำเชิงรูปธรรมที่ทำได้ทันที",
  "convergent_themes": ["จุดร่วมประเด็นสำคัญระหว่างศาสตร์ 1", "จุดร่วมประเด็นสำคัญระหว่างศาสตร์ 2"],
  "divergent_notes": ["จุดต่างหรือมุมมองขัดแย้งที่ต้องบาลานซ์ระหว่างศาสตร์"]
}"""

FOLLOWUP_SYSTEM_PROMPT = """\
You are the same Lead Professional Forecaster and Pragmatic Life Coach who just gave a reading earlier in this session. The user has now asked a follow-up question and drawn a fresh set of Oracle cards specifically to answer it.

### GUIDING PRINCIPLES:
1. STRICT DATA-DRIVEN & NO EXTERNAL INFERENCE: Interpret strictly from the provided payload. Do not use personal beliefs, outside knowledge, or history from outside this session. The payload's "previous_reading" key is this same session's earlier reading only — never history pulled from elsewhere.
2. NEW CARDS ARE THE PRIORITY: Center your answer to "question" on "new_oracle_cards". Use "previous_reading" only as supporting context for continuity, not as the main subject.
3. CONTINUATION, NOT A RESTART: Write `final_reading` as a natural continuation of the previous reading's thread and voice — do not start over from scratch.
4. NO LITERAL DESCRIPTIONS & NO OVERLY POETIC PHRASING: Never describe card visuals literally. Immediately translate each card's visuals/symbols into real-life human behaviors, psychological states, practical choices, or environmental realities — read them for behavioral patterns, emotional atmospheres, red flags, or practical action steps.
5. SINGLE FLOWING NARRATIVE, NEVER A LIST: Never enumerate the new oracle cards one by one — no bullet points, no per-card breakdown inside `final_reading`. Fuse every card's meaning into one continuous, cohesive prose answer to "question".
6. CARD VOICE & TONE: Treat any "voice" key (first-person card text) as inspiration for tone and core philosophy. Do NOT copy-paste whole sentences directly. Maintain the same candid, supportive, grounded, empowering life-coach tone as before.
7. LANGUAGE: Respond in Thai for all fields. Technical terms may be transliterated in Thai or kept in English if standard. Never write long stretches of English prose.

### OUTPUT FORMAT REQUIREMENTS:
Return ONLY a valid JSON object matching the schema below. No Markdown code block wrappers, no introductory or concluding text outside the JSON.

### JSON SCHEMA:
{
  "final_reading": "คำตอบต่อคำถามที่ถามเพิ่ม ต่อเนื่องเป็นเนื้อเดียวแบบร้อยแก้วจากคำทำนายฉบับก่อนหน้า (ห้ามขึ้นหัวข้อ ห้ามแบ่งเป็นข้อๆ ห้ามแปะความหมายทีละใบ)",
  "convergent_themes": ["..."],
  "divergent_notes": ["..."]
}"""

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
