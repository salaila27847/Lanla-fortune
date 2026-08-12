"""Tarot engine.

TODO (Phase 3/5): replace the mock body with fair-random card drawing
+ real meaning lookups. Check backend/app/knowledge_base/tarot/ for a
reusable Thai-language Major Arcana reference file carried over from
the Destiny Matrix project before writing new meanings from scratch.

The function signature and return type (EngineResult) must not change —
the synthesis layer depends on this contract.
"""

from __future__ import annotations

from app.core.schema import EngineResult, Finding


async def draw(spread_type: str = "three_card") -> EngineResult:
    # --- MOCK DATA — replace in Phase 5 ---
    return EngineResult(
        engine="tarot",
        summary="ไพ่ชี้ไปที่การเริ่มต้นใหม่หลังช่วงลังเล (mock data)",
        themes=["การเปลี่ยนแปลง", "จุดเริ่มต้นใหม่"],
        raw_findings=[
            Finding(
                label="The Fool (upright) — position: present (mock)",
                meaning="ความกล้าที่จะเริ่มต้นสิ่งใหม่ (mock)",
                weight=0.6,
            )
        ],
        confidence=0.5,
    )
