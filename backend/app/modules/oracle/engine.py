"""Oracle card engine.

TODO (Phase 3/5): deck choice is not yet decided (see CLAUDE.md open
questions) — ask the user which oracle deck to use as the primary set
before building the real knowledge base and draw logic.

The function signature and return type (EngineResult) must not change —
the synthesis layer depends on this contract.
"""

from __future__ import annotations

from app.core.schema import EngineResult, Finding


async def draw(deck: str = "tbd") -> EngineResult:
    # --- MOCK DATA — replace in Phase 5, deck TBD ---
    return EngineResult(
        engine="oracle",
        summary="ข้อความชี้ให้ไว้วางใจกระบวนการที่กำลังเกิดขึ้น (mock data)",
        themes=["ความไว้วางใจ", "จังหวะเวลา"],
        raw_findings=[
            Finding(
                label="Card: Trust the Process (mock)",
                meaning="ให้เวลาทำงานของมันโดยไม่เร่งรัด (mock)",
                weight=0.55,
            )
        ],
        confidence=0.5,
    )
