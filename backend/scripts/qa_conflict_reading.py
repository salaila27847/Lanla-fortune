"""Phase 6 QA — manual check: do 3 conflicting engine results synthesize sensibly?

Not a pytest — it makes a real Gemini API call and needs a human to read the
output, so it isn't meant to run in CI. Requires a real GEMINI_API_KEY in
backend/.env (this script loads it itself, same as app/main.py does).

Usage:
    cd backend && source .venv/bin/activate
    PYTHONPATH=. python scripts/qa_conflict_reading.py

Builds a scenario where the 3 engines deliberately disagree about a career
move, then prints the synthesized reading so you can check by eye that
master_interpreter.py's convergence -> divergence -> complementary structure
(see CLAUDE.md section 1, PRD.md section 4.4) holds up instead of just
picking a winner or blending everything into mush.
"""

from __future__ import annotations

import asyncio
import json

from dotenv import load_dotenv

from app.core.schema import EngineResult, Finding
from app.synthesis.master_interpreter import synthesize

load_dotenv()

# Uranian: favors the move (expansion, opportunity)
URANIAN = EngineResult(
    engine="uranian",
    summary="ช่วงนี้ดาว Jupiter สร้างมุมเสริมกับ Midheaven บ่งชี้โอกาสขยายงาน/เปลี่ยนสายอาชีพที่ดี",
    themes=["โอกาสขยายตัว", "จังหวะเปลี่ยนงานที่เอื้ออำนวย"],
    raw_findings=[
        Finding(label="Jupiter-MC", meaning="โอกาสเติบโตในหน้าที่การงาน", weight=0.85),
        Finding(label="Sun-Uranus", meaning="ความต้องการเปลี่ยนแปลงครั้งใหญ่", weight=0.7),
    ],
    confidence=0.8,
)

# Tarot: warns against it (caution, hidden risk)
TAROT = EngineResult(
    engine="tarot",
    summary="ไพ่ที่จั่วได้ชี้ให้ระวังการตัดสินใจเรื่องการงาน/การเงินในช่วงนี้ มีความเสี่ยงที่ยังมองไม่เห็น",
    themes=["ความเสี่ยงซ่อนอยู่", "ควรทบทวนก่อนตัดสินใจ"],
    raw_findings=[
        Finding(label="Five of Pentacles (upright)", meaning="ความไม่มั่นคงทางการเงิน", weight=0.75),
        Finding(label="The Tower (reversed)", meaning="เลี่ยงการเปลี่ยนแปลงที่หุนหันพลันแล่น", weight=0.65),
    ],
    confidence=0.7,
)

# Oracle: neither confirms nor denies — shifts to a different axis (inner readiness)
ORACLE = EngineResult(
    engine="oracle",
    summary="ไพ่ออราเคิลชี้ไปที่ความพร้อมภายในมากกว่าจังหวะภายนอก แนะนำให้ฟังสัญชาตญาณตัวเองเป็นหลัก",
    themes=["ความพร้อมภายใน", "เชื่อสัญชาตญาณตัวเอง"],
    raw_findings=[
        Finding(label="นกฮูกแห่งปัญญา (guardian)", meaning="ใคร่ครวญให้รอบคอบก่อนลงมือ", weight=0.6),
        Finding(label="ดอกบัว (flower)", meaning="การเติบโตทางจิตใจต้องใช้เวลา", weight=0.55),
    ],
    confidence=0.65,
)


async def main() -> None:
    result = await synthesize(URANIAN, TAROT, ORACLE)
    print(
        json.dumps(
            result.model_dump(exclude={"per_engine_breakdown"}), ensure_ascii=False, indent=2
        )
    )
    print("\n--- checklist ---")
    print("[ ] convergent_themes สมเหตุสมผลจริง ไม่ใช่แค่รวมทุกอย่างเข้าด้วยกัน")
    print("[ ] divergent_notes อธิบายความขัดแย้ง Uranian (สนับสนุน) vs Tarot (เตือน) โดยไม่ทิ้งฝั่งใดฝั่งหนึ่ง")
    print("[ ] final_reading ใช้ Oracle เป็นมุมเติมเต็ม (complementary) ไม่ใช่ตัวชี้ขาด")
    print("[ ] ไม่มีน้ำเสียง/ความเห็นที่ไม่ได้มาจาก 3 engine ข้างต้น (no personal bias)")


if __name__ == "__main__":
    asyncio.run(main())
