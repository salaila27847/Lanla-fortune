# Fortune App — Uranian × Tarot × Oracle

โครงโปรเจกต์เว็บแอปดูดวงที่ผสาน 3 ศาสตร์เข้าด้วยกัน พร้อมให้ Claude Code ทำงานต่อ

## เริ่มต้นใช้งานกับ Claude Code

1. เปิดโฟลเดอร์นี้เป็น working directory
2. สั่ง Claude Code ว่า **"อ่าน CLAUDE.md แล้วเริ่ม Phase 0-1 ตาม docs/task-breakdown.md"**
3. Claude Code จะอ่าน `CLAUDE.md` (กติกาโปรเจกต์), `docs/PRD.md` (ข้อกำหนด),
   `docs/data-schema.md` (schema กลาง) และ `docs/task-breakdown.md` (task list) โดยอัตโนมัติ

## โครงสร้างโฟลเดอร์

```
fortune-app/
├── CLAUDE.md              ← อ่านก่อนเสมอ
├── docs/
│   ├── PRD.md
│   ├── data-schema.md
│   └── task-breakdown.md
├── backend/                ← FastAPI + Python
│   ├── requirements.txt
│   ├── .env.example
│   ├── app/
│   │   ├── main.py
│   │   ├── core/schema.py         ← EngineResult contract กลาง
│   │   ├── modules/{uranian,tarot,oracle}/engine.py   ← 3 engine (ตอนนี้เป็น mock)
│   │   ├── synthesis/master_interpreter.py            ← เรียก Claude API สังเคราะห์ผล
│   │   └── knowledge_base/{uranian,tarot,oracle}/     ← ข้อมูลอ้างอิงแต่ละศาสตร์
│   └── tests/
└── frontend/                ← Next.js (ยังไม่ scaffold — ดู frontend/README.md)
```

## สถานะปัจจุบัน

- [x] โครงสร้าง repo + เอกสาร (CLAUDE.md, PRD, data schema, task breakdown)
- [x] Backend: schema กลาง, 3 engine stub (mock data), synthesis layer, FastAPI endpoint, venv + tests ผ่าน
- [x] Frontend: scaffold ด้วย `create-next-app` (TS, Tailwind, App Router) + framer-motion + `src/lib/api.ts`
- [x] CI: GitHub Actions รัน lint + test ทั้ง backend/frontend บน push/PR ไปที่ `main`
- [ ] Knowledge base จริง (ยูเรเนียน/ทาโรต์/ออราเคิล) — ยังเป็น mock ทั้งหมด
- [ ] ชุดไพ่ออราเคิลหลัก — ยังไม่ตัดสินใจ (ต้องถามผู้ใช้)
- [ ] หน้า frontend จริง (birth-data, tarot-draw, oracle-draw, reading) — ยังไม่สร้าง

## รันทดสอบ backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # แล้วใส่ ANTHROPIC_API_KEY จริง
pytest
uvicorn app.main:app --reload
```
