# Fortune App — Uranian × Tarot × Oracle

เว็บแอปดูดวงที่ผสาน **โหราศาสตร์ยูเรเนียน**, **ไพ่ทาโรต์**, และ **ไพ่ออราเคิล** เข้าด้วยกันแบบสมบูรณ์
ผ่านชั้นตีความกลาง (Master Interpreter, เรียก Gemini API) — ดู `CLAUDE.md` สำหรับสถาปัตยกรรมเต็ม

## เริ่มต้นใช้งานกับ Claude Code

1. เปิดโฟลเดอร์นี้เป็น working directory
2. อ่าน `CLAUDE.md` (กติกาโปรเจกต์ + สถานะการตัดสินใจล่าสุด), `docs/PRD.md` (ข้อกำหนด),
   `docs/data-schema.md` (schema กลาง) และ `docs/task-breakdown.md` (task list ทุก phase)

## โครงสร้างโฟลเดอร์

```
Lanla-fortune/
├── CLAUDE.md                          ← อ่านก่อนเสมอ
├── docs/
│   ├── PRD.md
│   ├── data-schema.md
│   ├── task-breakdown.md
│   └── deployment.md                  ← ขั้นตอน deploy Vercel + Render + Neon
├── backend/                           ← FastAPI + Python 3.11+
│   ├── requirements.txt
│   ├── .env.example
│   ├── render.yaml                    ← Render Blueprint
│   ├── app/
│   │   ├── main.py                    ← /api/reading, /api/forecast, /api/readings
│   │   ├── core/schema.py             ← EngineResult/BirthData/ReadingRequest/... contract กลาง
│   │   ├── core/auth.py               ← BFF shared-secret auth (get_current_user)
│   │   ├── db/                        ← SQLAlchemy 2.0 async (User, Reading)
│   │   ├── modules/uranian/           ← engine.py (natal) + solar_arc.py + transit.py (forecast)
│   │   ├── modules/{tarot,oracle}/engine.py
│   │   ├── synthesis/master_interpreter.py   ← เรียก Gemini API สังเคราะห์ผล
│   │   └── knowledge_base/{uranian,tarot,oracle}/     ← ข้อมูลอ้างอิงแต่ละศาสตร์ (YAML)
│   ├── scripts/qa_conflict_reading.py ← manual QA script (ต้องมี GEMINI_API_KEY จริง)
│   └── tests/
└── frontend/                          ← Next.js 16 (App Router) + TypeScript + Tailwind
    ├── src/auth.ts                    ← NextAuth.js v5 (Auth.js), Google provider
    ├── src/proxy.ts                   ← บังคับล็อกอินก่อนเข้า /reading, /history
    ├── src/app/reading/page.tsx       ← wizard: birth data → forecast checkboxes → tarot/oracle draw → result
    ├── src/app/history/               ← ประวัติคำทำนายของ user ที่ล็อกอิน
    ├── src/app/api/{reading,forecast}/route.ts   ← BFF proxy ไป backend พร้อม shared secret
    ├── src/components/{BirthDataForm,CardDrawStep,ReadingResult}.tsx
    └── src/lib/{api,geocode,usePlaceSearch}.ts
```

## สถานะปัจจุบัน

- [x] 3 engine ของจริงครบ: Uranian (`pyswisseph`, 22 ปัจจัย, planetary pictures Type I/II),
      Tarot (RWS 78 ใบ), Oracle (deck กำหนดเอง "ลานลาออราเคิล" 88 ใบ)
- [x] Uranian forecast (ไม่บังคับ, เลือกเปิดที่ฟอร์ม): Solar Arc Directions, Transit (รวม Station
      Points, Lunar Return, Relocation, Daily M/A, Transit Axes)
- [x] Master Interpreter สังเคราะห์ผลผ่าน Gemini API (`gemini-2.5-flash-lite`) — รวม forecast เข้าไป
      ด้วยถ้าผู้ใช้เลือกเปิด ไม่ใช่แค่ 3 engine หลัก (มี fallback ถ้า Gemini ใช้งานไม่ได้)
- [x] ระบบสมาชิก: Google Sign-In (NextAuth.js v5) บังคับล็อกอินก่อนใช้ `/reading`/`/history`,
      บันทึกประวัติคำทำนายผูกกับ user ทุกครั้งอัตโนมัติ (Postgres/Neon prod, SQLite dev)
- [x] Frontend เต็มรูปแบบ: ฟอร์มกรอกข้อมูลเกิด (พร้อม autocomplete สถานที่ทั้งจุดเกิดและ relocation),
      checkbox เปิด/ปิด forecast แต่ละแบบ, การ์ดจั่วไพ่ทาโรต์/ออราเคิลแบบ animation, หน้าผลลัพธ์แบบ
      tab (ภาพรวม/แยกศาสตร์/พยากรณ์ล่วงหน้า พร้อมปุ่มข้ามดูทีละแบบ)
- [x] CI: GitHub Actions รัน lint + test ทั้ง backend/frontend บน push/PR ไปที่ `main`
- [x] Deployment: Vercel (frontend) + Render (backend) + Neon (Postgres) — ดู `docs/deployment.md`
- [ ] `house_meanings` ของ Uranian KB ยังไม่ทำ (ต้องคำนวณ house cusp แบบ equal-house จาก M ก่อน,
      ยังไม่มีในโค้ด) — ดู `backend/app/knowledge_base/uranian/README.md`
- [ ] Rate limit / cache สำหรับ forecast endpoint ยังไม่ทำ

รายละเอียดทุก phase ดูที่ `docs/task-breakdown.md`

## รันทดสอบ backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # แล้วใส่ GEMINI_API_KEY จริง (ฟรีจาก aistudio.google.com)
pytest
uvicorn app.main:app --reload
```

## รันทดสอบ frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # ใส่ Google OAuth client id/secret + AUTH_SECRET + INTERNAL_API_SECRET
npm run lint
npm run build
npm run dev
```
