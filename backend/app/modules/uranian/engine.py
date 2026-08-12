"""Uranian astrology engine.

TODO (Phase 5): replace the mock body with real calculations using
pyswisseph — 8 trans-Neptunian points (Cupido, Hades, Zeus, Kronos,
Apollon, Admetos, Vulcanus, Poseidon), midpoints, and 90° dial
placement, matched against backend/app/knowledge_base/uranian/*.yaml.

The function signature and return type (EngineResult) must not change —
the synthesis layer depends on this contract.
"""

from __future__ import annotations

from app.core.schema import BirthData, EngineResult, Finding


async def calculate(birth_data: BirthData) -> EngineResult:
    # --- MOCK DATA — replace in Phase 5 ---
    return EngineResult(
        engine="uranian",
        summary="ช่วงนี้มีสัญญาณการเปลี่ยนแปลงด้านอาชีพ (mock data)",
        themes=["การงาน", "การเปลี่ยนแปลง"],
        raw_findings=[
            Finding(
                label="Cupido/MC = 45° (mock)",
                meaning="โอกาสความร่วมมือใหม่ในหน้าที่การงาน (mock)",
                weight=0.7,
            )
        ],
        confidence=0.5,
    )
