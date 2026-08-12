# Task breakdown

ผู้ใช้ยืนยันแล้วว่าต้องการ **วางโครงทั้ง 3 ศาสตร์พร้อมกันตั้งแต่แรก** — ลำดับด้านล่างจึงเน้นวางโครง (scaffolding) ทั้งหมดก่อน แล้วค่อยลงรายละเอียดทีละส่วน

## Phase 0 — Setup
- [x] `backend`: สร้าง virtualenv, ติดตั้ง FastAPI, Pydantic, SQLAlchemy, `pyswisseph`, `anthropic` SDK, `pytest`, `ruff`
- [x] `frontend`: `npx create-next-app@latest` (TypeScript, Tailwind, App Router)
- [x] ตั้งค่า `.env` จาก `.env.example` (ต้องมี `ANTHROPIC_API_KEY`)
- [x] ตั้ง CI ขั้นต่ำ: lint + test บน push (ถ้าใช้ GitHub)

## Phase 1 — วางโครง 3 engine พร้อมกัน (ตามที่ผู้ใช้ตัดสินใจ)
- [x] สร้าง `EngineResult` / `Finding` เป็น Pydantic model กลาง (ใช้ร่วมกันทั้ง 3 module)
- [x] `modules/uranian/`: stub function `calculate(birth_data) -> EngineResult` ที่ return mock data ก่อน
- [x] `modules/tarot/`: stub function `draw(spread_type) -> EngineResult` ที่ return mock data ก่อน
- [x] `modules/oracle/`: stub function `draw(deck) -> EngineResult` ที่ return mock data ก่อน (แทนที่ด้วยของจริงแล้วใน Phase 3)
- [x] เขียน unit test สำหรับ interface ทั้ง 3 (ตรวจว่า return ตรง schema)

## Phase 2 — Synthesis layer (คู่ขนานกับ Phase 1)
- [x] `synthesis/master_interpreter.py`: รับ mock `EngineResult` ทั้ง 3 มาประกอบ prompt เรียก Claude API
- [x] เขียน prompt template ที่ล็อกกฎ: ไม่ bias, ไม่ใช้ user history, ทำ convergence → divergence → complementary
- [x] Endpoint `/api/reading` ที่ orchestrate เรียก 3 engine แบบ concurrent (`asyncio.gather`) แล้วส่งต่อให้ synthesis

## Phase 3 — Knowledge base ของจริง (ทีละศาสตร์ แทนที่ mock)
- [ ] Tarot: ตรวจสอบและ reuse ไฟล์ความหมายจากโปรเจกต์ Destiny Matrix ก่อนสร้างใหม่
- [ ] Uranian: สร้างฐานความหมาย configuration พื้นฐาน (8 ดาวเสริม + midpoint หลัก)
- [x] Oracle: ตัดสินใจแล้ว — deck หลัก `lanla_original` (เทวดา/นางฟ้า + สัตว์นำทางไทย + ดอกไม้ 60 ใบ)
      สร้าง knowledge base จริงและสลับ engine จาก mock แล้ว (ดู `backend/app/knowledge_base/oracle/`)

## Phase 4 — Frontend (คู่ขนานกับ Phase 1-2 โดยเรียก mock API)
- [ ] หน้ากรอกข้อมูลเกิด + เลือกคำถาม
- [ ] หน้าจั่วไพ่ทาโรต์แบบ interactive (animation)
- [ ] หน้าจั่วไพ่ออราเคิล
- [ ] หน้าแสดงผลคำทำนายฉบับสมบูรณ์ + tab ดูรายละเอียดแยกศาสตร์

## Phase 5 — ต่อของจริงแทน mock ทีละ engine
- [ ] สลับ Tarot engine เป็นของจริง → ทดสอบ end-to-end
- [ ] สลับ Uranian engine เป็นของจริง → ทดสอบ end-to-end
- [ ] สลับ Oracle engine เป็นของจริง → ทดสอบ end-to-end

## Phase 6 — QA
- [ ] ทดสอบกรณี 3 ศาสตร์ขัดแย้งกัน ว่า Master Interpreter อธิบายได้สมเหตุสมผล
- [ ] ทดสอบ edge case: ไม่ทราบเวลาเกิด, จั่วไพ่ซ้ำ, Claude API timeout/fail (ต้องมี fallback)
