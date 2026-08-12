"""Master Interpreter — the synthesis layer ("หัวหน้าทีมหลัก").

Takes the 3 engines' EngineResult objects and asks Claude to cross-
reference them into one reading. The rules below are load-bearing —
do not soften or remove them when editing the prompt:

  1. No personal bias — interpret only from the raw findings passed in.
  2. No user history — never reference anything outside this session's
     input (see CLAUDE.md, PRD.md section 4.4).
  3. Three-step method — convergence, then divergence, then
     complementary framing (see PRD.md section 4.4).

If the Claude call fails or times out (Phase 6 QA requirement), synthesize()
falls back to _fallback_synthesis(), which builds a SynthesisOutput directly
from the engines' own themes/summaries — plain set overlap for convergence,
no invented interpretation, so it never violates rule 1 above either.
"""

from __future__ import annotations

import json
import logging
import os

from anthropic import APIError, AsyncAnthropic

from app.core.schema import EngineResult, SynthesisOutput

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
คุณคือหัวหน้าทีมนักพยากรณ์มืออาชีพ เชี่ยวชาญทั้งโหราศาสตร์ยูเรเนียน ไพ่ทาโรต์ และไพ่ออราเคิล
กฎที่ต้องปฏิบัติตามอย่างเคร่งครัด:
1. ห้ามใส่ความเห็นส่วนตัวหรือความเชื่อของคุณเอง ตีความจากข้อมูลดิบที่ได้รับเท่านั้น
2. ห้ามอ้างอิงข้อมูลใดๆ นอกเหนือจากที่ส่งมาในข้อความนี้ (ไม่มีประวัติผู้ใช้)
3. วิเคราะห์ตามลำดับ 3 ขั้นตอนเสมอ:
   ก) หาจุดร่วม (convergence) — ประเด็นที่ทั้ง 3 ศาสตร์ชี้ไปทางเดียวกัน
   ข) จัดการความขัดแย้ง (divergence) — อธิบายอย่างสมเหตุสมผล ไม่เลือกทิ้งศาสตร์ใดศาสตร์หนึ่ง
   ค) เติมเต็มมุมที่ขาด (complementary) — แต่ละศาสตร์เสริมมุมที่อีกศาสตร์ไม่ครอบคลุมอย่างไร

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


async def synthesize(
    uranian: EngineResult, tarot: EngineResult, oracle: EngineResult
) -> SynthesisOutput:
    client = AsyncAnthropic()  # reads ANTHROPIC_API_KEY from env
    model = os.environ.get("SYNTHESIS_MODEL", "claude-sonnet-5")

    payload = {
        "uranian": uranian.model_dump(),
        "tarot": tarot.model_dump(),
        "oracle": oracle.model_dump(),
    }

    try:
        response = await client.messages.create(
            model=model,
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
            timeout=SYNTHESIS_TIMEOUT_SECONDS,
        )
        text_block = next(b for b in response.content if b.type == "text")
        parsed = json.loads(text_block.text)

        return SynthesisOutput(
            final_reading=parsed["final_reading"],
            convergent_themes=parsed["convergent_themes"],
            divergent_notes=parsed["divergent_notes"],
            per_engine_breakdown={"uranian": uranian, "tarot": tarot, "oracle": oracle},
        )
    except (APIError, TypeError, KeyError, ValueError, StopIteration) as exc:
        # TypeError covers the anthropic SDK's own "missing/invalid API key"
        # failure, which it raises before ever making a request rather than
        # as an APIError. KeyError/ValueError/StopIteration cover a malformed
        # or non-JSON model response.
        logger.warning("Synthesis via Claude failed, falling back to raw engine summary: %s", exc)
        return _fallback_synthesis(uranian, tarot, oracle)


def _fallback_synthesis(
    uranian: EngineResult, tarot: EngineResult, oracle: EngineResult
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

    return SynthesisOutput(
        final_reading=final_reading,
        convergent_themes=convergent_themes,
        divergent_notes=divergent_notes,
        per_engine_breakdown=engines,
    )
