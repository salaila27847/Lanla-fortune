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
- [x] Tarot: ตรวจสอบแล้ว ไม่พบไฟล์จากโปรเจกต์ Destiny Matrix ในบัญชี GitHub — เขียนความหมายทั้ง 78 ใบ
      ขึ้นใหม่ (ตั้งตรง+กลับหัว) อิงฐานสากล Rider-Waite-Smith สร้าง knowledge base จริงและสลับ engine
      จาก mock แล้ว (ดู `backend/app/knowledge_base/tarot/`)
- [x] Uranian: สร้างฐานความหมาย configuration พื้นฐาน (8 ดาวเสริม + midpoint หลัก) แล้ว —
      คำนวณจริงด้วย `pyswisseph` (Moshier ephemeris ในตัว) สลับ engine จาก mock แล้ว
      (ดู `backend/app/knowledge_base/uranian/`)
- [x] Oracle: ตัดสินใจแล้ว — deck หลัก `lanla_original` (เทวดา/นางฟ้า + สัตว์นำทางไทย + ดอกไม้ 60 ใบ)
      สร้าง knowledge base จริงและสลับ engine จาก mock แล้ว (ดู `backend/app/knowledge_base/oracle/`)

## Phase 4 — Frontend (คู่ขนานกับ Phase 1-2 โดยเรียก mock API)
- [x] หน้ากรอกข้อมูลเกิด (`/reading`, `BirthDataForm.tsx`) — ยังไม่มี "เลือกคำถาม" เพราะ `BirthData`
      schema (`docs/data-schema.md`) ไม่มี field คำถามอยู่ตอนนี้ ต้องตัดสินใจ/เพิ่ม schema ก่อนถ้าต้องการ
- [x] หน้าจั่วไพ่ทาโรต์แบบ interactive (animation) — `CardDrawStep.tsx` (Framer Motion flip)
- [x] หน้าจั่วไพ่ออราเคิล — ใช้ component เดียวกับทาโรต์ (`cardCount={1}`)
- [x] หน้าแสดงผลคำทำนายฉบับสมบูรณ์ + tab ดูรายละเอียดแยกศาสตร์ — `ReadingResult.tsx`
- [x] แก้บั๊ก: ช่อง "สถานที่เกิด" เดิมพิมพ์ชื่อสถานที่แล้วไม่กระทบพิกัด (ค้างที่ค่า preset เริ่มต้น)
      — เพิ่มการค้นหาพิกัดจริงผ่าน OpenStreetMap Nominatim (`frontend/src/lib/geocode.ts`, debounce
      600ms) แสดง dropdown ผลลัพธ์ให้เลือก แล้ว auto-fill ละติจูด/ลองจิจูด (และเขตเวลาถ้าเป็นสถานที่
      ในประเทศไทย) ยังคงแก้ไขพิกัดด้วยตนเองได้เหมือนเดิมเป็น fallback

หมายเหตุ: เรียก `/api/reading` ของจริงแล้ว (ไม่ใช่ mock endpoint) ทดสอบ end-to-end ผ่าน browser
(Playwright) แล้วว่า flow ทำงานถูกต้องจนถึงจุดเรียก Claude API — ผลจริงยังทดสอบไม่ได้เพราะ sandbox
นี้ไม่มี `ANTHROPIC_API_KEY`

## Phase 5 — ต่อของจริงแทน mock ทีละ engine
- [x] สลับ Tarot engine เป็นของจริงแล้ว — ทดสอบ unit + ทดสอบเรียกพร้อมกับอีก 2 engine ผ่าน
      `asyncio.gather` แบบเดียวกับที่ `/api/reading` ทำจริงแล้ว (ยังไม่ได้ทดสอบผ่าน HTTP จริงที่มี
      `ANTHROPIC_API_KEY` เพราะ sandbox นี้ไม่มี key)
- [x] สลับ Uranian engine เป็นของจริงแล้ว (คำนวณด้วย `pyswisseph`) — ทดสอบแบบเดียวกับ Tarot ข้างต้น
- [x] สลับ Oracle engine เป็นของจริงแล้ว — ทดสอบแบบเดียวกับ Tarot ข้างต้น

## Phase 6 — QA
- [ ] ทดสอบกรณี 3 ศาสตร์ขัดแย้งกัน ว่า Master Interpreter อธิบายได้สมเหตุสมผล — เตรียม script ไว้แล้ว
      ที่ `backend/scripts/qa_conflict_reading.py` (สร้างสถานการณ์ที่ยูเรเนียนสนับสนุนการเปลี่ยนงาน
      แต่ทาโรต์เตือนความเสี่ยง ส่วนออราเคิลชี้ไปมุมความพร้อมภายใน) ยังรันไม่ได้ในนี้เพราะไม่มี
      `ANTHROPIC_API_KEY` จริง — ผู้ใช้ต้องรันเองที่เครื่อง (ใส่ key ใน `backend/.env` แล้ว
      `python scripts/qa_conflict_reading.py`) แล้วเช็ค checklist ที่ script พิมพ์ออกมา
- [x] ทดสอบ edge case แล้ว:
  - ไม่ทราบเวลาเกิด — `uranian/engine.py` ใช้เที่ยงวันเป็นค่าประมาณ ลด confidence และแจ้งข้อจำกัด
  - จั่วไพ่ซ้ำ — ป้องกันโดยโครงสร้าง (`random.sample` ไม่คืนใบซ้ำ) ทั้ง tarot และ oracle engine
  - Claude API timeout/fail — `master_interpreter.py` มี fallback แล้ว (ตัดกลับไปสรุปผลดิบจาก
    3 engine ตรงๆ แทนการ error 500) ทดสอบจริงผ่าน HTTP แล้วว่าไม่ crash แม้ไม่มี API key
  - Timezone/พิกัดไม่ถูกต้อง — `BirthData` validate ที่ schema (422 แทนที่จะ crash 500)

## Phase 7 — ระบบสมาชิก (Google Sign-In)
- [x] ติดตั้ง `next-auth@5` (Auth.js) พร้อม Google provider — `frontend/src/auth.ts`,
      `frontend/src/app/api/auth/[...nextauth]/route.ts`
- [x] UI ล็อกอิน/ล็อกเอาต์ — `AuthButton.tsx` (Server Component + Server Action) แสดงใน
      `Header.tsx` ทุกหน้า ไม่ได้บังคับล็อกอินก่อนใช้หน้า `/reading` (ยังเป็น guest-friendly เหมือนเดิม)
- [x] ทดสอบโครงสร้างแล้ว: `GET /api/auth/providers` คืนค่า provider ถูกต้อง, กด "เข้าสู่ระบบด้วย
      Google" ได้ Server Action ที่สร้าง Google OAuth authorization URL ถูกต้องครบ (client_id,
      redirect_uri, PKCE, scope) — ยังทดสอบ live ไม่ได้เพราะไม่มี Google OAuth credentials จริง
- [x] ผู้ใช้สร้าง Google OAuth Client ID/Secret จริงแล้วและใส่ใน `frontend/.env.local` — ทดสอบ
      ล็อกอินจริงบนเครื่องผู้ใช้แล้ว เข้าสู่ระบบด้วย Google สำเร็จ (ยืนยันด้วย screenshot)
- [x] ตัดสินใจแล้ว (2026-08-12): บังคับล็อกอินก่อนใช้ `/reading` และ `/history` + เก็บประวัติคำทำนาย
      ผูกกับ user จริง — ดู Phase 9 ด้านล่างสำหรับรายละเอียด implementation

## Phase 8 — Deployment (Vercel + Render + Neon)
- [x] `render.yaml` (Blueprint) สำหรับ backend — เชื่อม repo แล้ว Render สร้าง web service ให้อัตโนมัติ
- [x] `docs/deployment.md` — ขั้นตอนละเอียดทีละ dashboard (Render, Vercel, Neon, Google OAuth
      redirect URI สำหรับ production)
- [ ] ผู้ใช้ต้อง deploy จริงผ่านบัญชีของตัวเอง (Claude ไม่มีสิทธิ์เข้าถึงบัญชี Render/Vercel/Neon) —
      ทำตาม `docs/deployment.md` ข้อ 1-5 ทั้งหมด **รวมข้อ 3 (เชื่อม Neon) ด้วย** — ไม่ใช่ตัวเลือกอีก
      ต่อไปแล้ว เพราะ Phase 9 ทำให้ login/history ต้องมี DB จริงถึงจะใช้งานได้
- [ ] ทดสอบ end-to-end บน production จริง

## Phase 9 — บังคับล็อกอิน + เก็บประวัติคำทำนายผูกกับ user
- [x] Backend: DB layer จริงด้วย SQLAlchemy 2.0 async (`backend/app/db/session.py`,
      `backend/app/db/models.py`) — `User` (google_sub, email, name), `Reading` (birth_data +
      synthesis_output เป็น JSON column ผูกกับ user_id) สร้างตารางอัตโนมัติตอน startup
      (`Base.metadata.create_all`, ยังไม่ใช้ Alembic เพราะไม่มี migration มาก่อน)
- [x] Backend: ยืนยันตัวตนแบบ BFF proxy + shared secret (`backend/app/core/auth.py`) — Next.js
      server เป็นคนตรวจ session จริง (ผ่าน `auth()`) แล้วส่ง `X-Internal-Secret` +
      `X-User-Id`/`X-User-Email`/`X-User-Name` มาให้ backend ตรวจซ้ำด้วย `hmac.compare_digest`
      (เลือกทางนี้แทนการถอดรหัส JWE ของ NextAuth เองใน Python เพราะซับซ้อนและเปราะบางกว่ามาก)
- [x] Backend: `POST /api/reading` บันทึกทุกคำทำนายลง DB อัตโนมัติ (response shape เดิมไม่เปลี่ยน),
      `GET /api/readings` คืนประวัติของ user คนนั้นเท่านั้น (เรียงใหม่สุดก่อน) — มี unit test
      ครอบคลุม 401 กรณี secret ผิด/ขาด, การบันทึกถูก user, และ **cross-user isolation** โดยเฉพาะ
      (`backend/tests/test_reading_history.py`)
- [x] Frontend: `frontend/src/proxy.ts` กัน `/reading`, `/history` ไม่ให้เข้าถ้ายังไม่ล็อกอิน
      (Next.js 16 เปลี่ยนชื่อ convention จาก `middleware.ts` เป็น `proxy.ts` — ตรวจสอบกับ
      `node_modules/next/dist/docs/` แล้วยืนยันแล้ว) พร้อม `callbacks.authorized` ใน `auth.ts`
- [x] Frontend: แก้บั๊ก callbackUrl ไม่ไหลไปถึง `signIn()` ตอนใช้ custom sign-in page (ถ้าไม่แก้
      ผู้ใช้จะเด้งกลับหน้าแรกเสมอหลัง login แทนที่จะกลับไปหน้าที่ตั้งใจเข้า)
- [x] Frontend: `/history` หน้าใหม่ (Server Component) แสดงประวัติคำทำนาย, ลิงก์ "ดูประวัติคำทำนาย"
      ใน `AuthButton.tsx`
- [x] Frontend: `lib/backend.ts` (server-only helper แนบ header ยืนยันตัวตน) +
      `app/api/reading/route.ts` (proxy คำขอจาก wizard ที่เป็น Client Component ไปยัง backend)
- [x] ทดสอบแล้ว: backend 36 tests ผ่านทั้งหมด (`ruff check`/`ruff format --check` สะอาด), frontend
      `npm run build`/`npm run lint` ผ่าน, ยืนยันด้วย curl ว่า auth/persistence/cross-user
      isolation ทำงานถูกต้องจริงแบบ end-to-end, Playwright ยืนยัน redirect ตอนไม่ได้ล็อกอิน
- [ ] **ข้อจำกัดที่ทดสอบในนี้ไม่ได้**: sandbox นี้ทำ Google OAuth login จริงไม่ได้ (ไม่มี credentials
      จริง) — ต้องทดสอบ full flow (login → กรอกข้อมูล → จั่วไพ่ → เห็นคำทำนายใน `/history`) บนเครื่อง
      ผู้ใช้เอง เหมือนตอนทดสอบ Google Sign-In ครั้งแรก
