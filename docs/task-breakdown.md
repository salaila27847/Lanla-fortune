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

## Phase 10 — สลับ synthesis layer จาก Claude API เป็น Gemini API
- [x] ตัดสินใจแล้ว (2026-08-12): ผู้ใช้ขอเปลี่ยนจาก Anthropic Claude เป็น Google Gemini เพราะ Gemini
      มี free tier จริง (ไม่ต้องผูกบัตรเครดิต) — ตรวจสอบ SDK ปัจจุบันจริงจากแหล่งต้นทาง
      (`github.com/googleapis/python-genai` README + ติดตั้งแพ็กเกจจริงในนี้เพื่อตรวจ field name
      ของ `types.HttpOptions`/`GenerateContentConfig` แทนการเดา) แทนที่ `anthropic` SDK ด้วย
      `google-genai` ใน `backend/app/synthesis/master_interpreter.py` — interface ของ
      `synthesize()` ไม่เปลี่ยน (รับ 3 `EngineResult` คืน `SynthesisOutput` เหมือนเดิม),
      `_fallback_synthesis()` (Phase 6 QA) เป็น provider-agnostic อยู่แล้วไม่ต้องแก้
- [x] Env var: `ANTHROPIC_API_KEY` → `GEMINI_API_KEY` (จาก aistudio.google.com ฟรี), default
      `SYNTHESIS_MODEL` เปลี่ยนจาก `claude-sonnet-5` เป็น `gemini-3.5-flash` (flash tier ที่ยัง
      อยู่ใน free tier ตอนตรวจสอบ ไม่ใช่ preview/lite)
- [x] อัปเดต `render.yaml`, `docs/deployment.md` (ขั้นตอนขอ key จาก Google AI Studio แทน Anthropic
      Console), `CLAUDE.md` (architecture diagram + tech stack table + decided-items note),
      `docs/PRD.md` §4.4, root `README.md` — ไม่แก้ entry เก่าใน task-breakdown.md นี้ที่พูดถึง
      Claude API เพราะเป็น log ประวัติศาสตร์ว่าตอนนั้นสร้างด้วยอะไรจริง (เหมือนตอนแก้ Railway→Render
      ที่เพิ่ม correction note แทนการเขียนประวัติทับ)
- [x] อัปเดต test double ใน `test_master_interpreter_fallback.py` (`_FakeAsyncAnthropic` →
      `_FakeGenAIClient`), `conftest.py` env var, comment ใน `test_reading_history.py`,
      docstring ใน `backend/scripts/qa_conflict_reading.py` — ทดสอบแล้ว: 36 tests ผ่าน,
      `ruff check`/`ruff format --check` สะอาด
- [ ] **ข้อจำกัดที่ทดสอบในนี้ไม่ได้**: ไม่มี `GEMINI_API_KEY` จริงใน sandbox นี้ — ทดสอบได้แค่ path
      fallback (key ปลอม/ไม่มี → `_fallback_synthesis()` ทำงานถูกต้อง ไม่ crash) ต้องทดสอบคุณภาพ
      การตีความจริงด้วย key จริงบนเครื่องผู้ใช้ (`backend/scripts/qa_conflict_reading.py` ใช้ทดสอบได้)

## Phase 11 — Uranian engine: planetary pictures (Type I/II) + combinations glossary

ผู้ใช้ส่ง handoff package (`lanla-fortune-uranian-package.zip`) ที่มีโค้ดต้นแบบ
(`uranian_math.py`, `ephemeris.py`, `picture_finder.py`, `seed_data.py`, `schema.sql`,
`test_engine.py`) และเอกสารวิจัยภาษาไทย 6 ไฟล์ (ถอดความจาก *The Language of Uranian Astrology*
โดย Roger A. Jacobson) — เชื่อมเข้ากับ engine ที่ใช้งานจริงแล้วดังนี้:

- [x] ขยาย `engine.py` ให้คำนวณครบ 22 ปัจจัย (เดิมมีแค่ TNP 8 ดวง + Sun/Moon/Asc/MC) — เพิ่ม
      ดาวเคราะห์คลาสสิก 8 ดวง (Mercury-Pluto), Node (mean), และจุดอาริส (คงที่ 0°)
- [x] เพิ่มการหา **planetary picture** บน 90° dial ทั่วทั้ง 22 ปัจจัย — Type I (`_find_pictures`
      ใน `engine.py`, orb 1.5°) และ Type II (orb 3.0°) กรองเฉพาะภาพที่มีจุดส่วนตัวอย่างน้อยหนึ่งจุด
      แทนที่ hit-finding แบบเดิมที่เช็คเฉพาะ TNP-vs-personal-point-pair (ซึ่งเป็นกรณีย่อยของอันใหม่)
- [x] KB ใหม่ 3 ไฟล์ (YAML ตามแพทเทิร์นเดิมของโปรเจกต์ ไม่ใช้ตาราง DB ตามที่ `schema.sql` ของ
      package เสนอ เพราะขัดกับหลักการ "knowledge base เป็นไฟล์ YAML/JSON" ใน CLAUDE.md §2):
      `factors.yaml` (14 ปัจจัยที่ไม่มีใน `points.yaml`), `planetary_pictures.yaml` (glossary
      คู่ปัจจัย 50 คู่ จาก `seed_data.py`), `axis_meanings.yaml` (แกน M 21 คู่ จาก `seed_data.py`)
- [x] เก็บเอกสารวิจัยต้นฉบับทั้ง 6 ไฟล์ไว้ที่ `backend/app/knowledge_base/uranian/research/`
      เป็นแหล่งอ้างอิงสำหรับขยาย KB ต่อ (ดู "ยังไม่ได้ทำ" ใน `knowledge_base/uranian/README.md`)
- [x] เพิ่ม unit test 15 เคสใน `test_uranian_knowledge_base.py` (พอร์ตจาก `test_engine.py` ของ
      package + เทสต์ KB loading ใหม่) — รวม 51 tests ผ่านทั้งหมด, `ruff check`/`ruff format --check`
      สะอาด — ยืนยันด้วย manual run จริงว่า picture-finder เจอ Type I/II จริงและ match glossary
      ถูกต้อง (เช่น `Mars/Sun=Hades/Neptune` → "น้ำ การจมน้ำ การขาดอากาศหายใจ")
- [x] **แก้ไข 2026-08-13 (Phase 14)**: `axis_meanings.yaml` ครบทั้ง 5 แกนแล้ว (M/A/Sun/Moon/Node)
      — ดู Phase 14 ด้านล่าง — ยังไม่มี house_meanings (ยังไม่คำนวณเรือน) และยังไม่มี solar arc /
      transit forecast ตอนที่เขียนบรรทัดนี้ครั้งแรก — ปัจจุบัน solar arc/transit ทำแล้วใน Phase 11-13
- [x] **แก้ไข 2026-08-13**: ผู้ใช้เทียบผลลัพธ์ engine กับเว็บอ้างอิง 2 เว็บโดยใช้วันเกิดจริง —
      ดาวเคราะห์คลาสสิก, Ascendant/MC, และดาวเสริมทั้ง 8 ดวงตรงกับทั้ง 2 เว็บในระดับ <1 ลิปดา
      (ยืนยันว่า ephemeris/house/midpoint math ถูกต้อง) จุดเดียวที่ต่าง ~0.5° คือ Node เพราะ
      engine ใช้ Mean Node แต่เว็บอ้างอิงใช้ True Node — ผู้ใช้ตัดสินใจแล้วให้เปลี่ยนเป็น
      **True Node** (`swe.TRUE_NODE` แทน `swe.MEAN_NODE` ใน `_compute_positions()`) ทดสอบแล้วว่า
      ตรงกับเว็บอ้างอิงในระดับ <1 ลิปดาเช่นกัน, 51 tests ยังผ่านหมด (ไม่มี test ใดอิง Node
      longitude ตายตัว)
- [x] **แก้ไข 2026-08-13**: เริ่มทำ Solar Arc Directions (บทที่ 10 ใน `research/`) — ผู้ใช้ตัดสินใจ
      แล้วว่าตอนนี้เอาแค่ฟังก์ชันคำนวณก่อน **ยังไม่ต่อ endpoint/UI** (ต้องเพิ่ม target-date input ที่
      `BirthData` ยังไม่มี ไว้ตัดสินใจ scope การเชื่อมกับแอปทีหลัง) — สร้าง
      `backend/app/modules/uranian/solar_arc.py`: `progressed_sun_longitude()`, `solar_arc_degrees()`,
      `directed_positions()` (ขับเคลื่อนทุกปัจจัยด้วยส่วนโค้งเท่ากัน ตามกฎ Solar Arc), และ
      `find_directed_pictures()` (หา Type I/II ข้ามชุด radix+directed โดยตัดคู่ปัจจัยตัวเดียวกัน
      ข้ามชุด radix/directed ออกจากการจับคู่ midpoint เพราะเป็นฟังก์ชันคงที่ของ arc ไม่ใช่
      configuration จริง, ตัดภาพที่เป็น radix ล้วนออกเพราะ natal engine ครอบคลุมแล้ว, ตัด Type II
      ที่ทั้งสองคู่เป็นดาวชุดเดียวกันข้าม radix/directed ออกเพราะเกือบจะเป็นฟังก์ชันคงที่ของ arc
      เช่นกัน — คงไว้เฉพาะภาพที่พึ่งพาตำแหน่งจริงของดวงชะตา) เพิ่ม unit test 11 เคสใน
      `test_uranian_solar_arc.py` (คำนวณ arc, directed positions, และภาพสังเคราะห์ครบทุก
      edge case ข้างต้น) — รวม 62 tests ผ่านหมด, ruff clean
- [x] **แก้ไข 2026-08-13 (Phase 12)**: ตัดสินใจแล้วและเชื่อมเข้าแอปจริงแล้ว — ดู Phase 12 ด้านล่าง
- [x] **แก้ไข 2026-08-13**: ทำต่อ Transit + Station Points + Lunar Return + Relocation (บทที่ 11-12
      ใน `research/`) ตามที่ผู้ใช้ขอให้ครอบคลุมทุกหัวข้อในตาราง "ฟีเจอร์ที่ควรมีในระบบ" — ยังคง
      calculation-only เหมือน solar_arc.py (ยังไม่ต่อ endpoint/UI) สร้าง
      `backend/app/modules/uranian/transit.py`:
      - `transit_positions()` — ตำแหน่งจริง ณ วันที่ต้องการ (19 ปัจจัย: ดาวเคราะห์คลาสสิก 10 +
        ดาวเสริม 8 + Node จริง ไม่รวม M/A เพราะเป็นคนละเทคนิค "Daily M/A")
      - `find_transit_pictures()` — หา Type I/II ข้าม radix+transit (และ directed ถ้ามี) ที่ orb
        แคบ 1° ตามที่เอกสารกำหนด, บังคับต้องมีปัจจัยที่ "กำลังเคลื่อนไหว" (transit/directed) อย่างน้อย
        1 ตัว และมี personal point แบบ radix/directed อย่างน้อย 1 ตัว (transit ของ Sun/Moon/Node เอง
        ไม่นับเป็น personal point เพราะเป็นดาวที่กำลังโคจรผ่าน ไม่ใช่จุดอ้างอิงคงที่)
      - `_is_arc_locked_pair()` — ระหว่างพัฒนาพบบั๊กจริงที่ตัวเองเขียน: กฎตัดคู่ปัจจัยเดียวกันข้าม
        radix/directed (ลอกมาจาก solar_arc.py) ตรวจจับแค่กรณีตรงไปตรงมา (radix Sun/Venus vs directed
        Sun/Venus) แต่พลาดกรณี "cross pairing" (radix Sun/directed Venus vs directed Sun/radix Venus)
        ซึ่งเป็น identity ทางคณิตศาสตร์เดียวกันทุกประการ (`midpoint(x,y+k) == midpoint(x+k,y)`) แก้แล้ว
        ด้วยกฎที่ตรวจทุกวิธีแบ่งกลุ่มพร้อมกัน — ยืนยันด้วย unit test ทั้ง 2 กรณี และยืนยันว่า
        radix/transit (ไม่ใช่ radix/directed) ไม่ถูกตัดออกเพราะ transit ไม่ได้ขยับด้วย arc คงที่แบบ
        directed
      - `daily_speed()` / `find_stations_in_range()` — หา station point จากการเปลี่ยนเครื่องหมาย
        ความเร็วรายวัน ทดสอบกับคาบ Mercury retrograde จริงเดือนก.พ.-มี.ค. 2026 (เจอ 2 สถานีตรงตาม
        คาบจริง คาบอื่นในปี 2026 ก็นับได้ 6 สถานีรวม ตรงกับที่ Mercury retrograde ปีละ ~3 รอบ)
      - `find_lunar_return()` — bisection search หาวันที่ดวงจันทร์ transit กลับตำแหน่งเกิดพอดี
        (แม่นถึงระดับ <0.01° เพราะดวงจันทร์ไม่มีทางถอยหลัง เดินหน้าทางเดียวเสมอ scan ทุก 6 ชม.
        ไม่มีทางพลาดจุดตัด)
      - `relocated_angles()` — คำนวณ A/M ใหม่จากพิกัดปลายทาง ใช้เวลาเกิด UTC เดิม
      - เพิ่ม unit test 16 เคสใน `test_uranian_transit.py` — รวม 78 tests ผ่านหมด, ruff clean
- [x] **แก้ไข 2026-08-13 (Phase 13)**: เพิ่ม "Daily Meridian and Ascendant" (M/A ณ ปัจจุบัน — คนละ
      เทคนิคกับ relocation ที่เป็น M/A ณ สถานที่อื่น) และ "Transit Axes" — ดู Phase 13 ด้านล่าง
- [ ] **ข้อจำกัดที่ทดสอบในนี้ไม่ได้**: ทดสอบผ่าน unit test + manual script เท่านั้น ยังไม่ได้ทดสอบ
      end-to-end ผ่าน `/api/reading` จริงที่มี `GEMINI_API_KEY` จริง (ข้อจำกัดเดิมจาก Phase 6/10)

## Phase 12 — เชื่อม Solar Arc/Transit/Lunar Return/Relocation เข้ากับแอปจริง

ผู้ใช้ตัดสินใจแล้ว (2026-08-13): เพิ่ม checkbox 4 ตัวในฟอร์มกรอกข้อมูลเกิด `/reading` เดิม
(ไม่แยกหน้าใหม่) แต่ละตัวเปิด/ปิดฟิลด์ข้อมูลของตัวเอง และผลลัพธ์แสดงเป็น**ตารางดิบ** ไม่ผ่าน
Gemini synthesis (ต่างจาก `/api/reading` ที่สังเคราะห์เป็นคำทำนายภาษา) — **กลับคำตัดสินใจนี้แล้ว
ใน Phase 13**: ผู้ใช้ขอให้การสังเคราะห์ผลต้องเอา Transit/Solar Arc/Relocation ไปด้วย ไม่ใช่แค่
ตารางดิบแยกออกมา — ตารางดิบยังคงแสดงอยู่ (เป็น tab "การพยากรณ์ล่วงหน้า" ที่ `ReadingResult.tsx`)
แต่ตอนนี้ Gemini เห็นข้อมูลชุดเดียวกันด้วยและทอเข้าไปใน `final_reading`

- [x] Backend: เพิ่ม schema (`ForecastRequest`/`ForecastResponse` + sub-request/result ต่อเทคนิค)
      ใน `app/core/schema.py`, เพิ่ม `POST /api/forecast` ใน `main.py` — auth-gated แบบเดียวกับ
      `/api/reading` (`get_current_user`) แต่**ไม่บันทึกลง reading history** เพราะเป็นตารางดิบ
      ไม่ใช่คำทำนาย รับ birth_data + sub-request ที่เลือก (solar_arc/transit/lunar_return/relocation)
      แต่ละตัว optional คำนวณเฉพาะที่ส่งมา จำกัดผลลัพธ์ 30 picture ต่อเทคนิค (`FORECAST_PICTURE_LIMIT`)
      แปลง factor id ภายใน (`r:SUN`, `d:MOON`, `t:JUPITER` ฯลฯ) เป็น label ภาษาไทยอ่านง่ายผ่าน
      `_factor_display_name()` เดิมจาก `engine.py`
- [x] Backend: เพิ่ม unit test 8 เคสใน `test_forecast_endpoint.py` (ครอบคลุมทุก sub-request,
      auth, no-time-for-relocation error, ยิงทุกตัวพร้อมกัน)
- [x] **เจอบั๊ก race condition จริงระหว่างทดสอบ end-to-end ในเบราว์เซอร์**: frontend ยิง
      `/api/reading` และ `/api/forecast` พร้อมกัน (`Promise.all`) — สำหรับ user คนใหม่ที่ไม่เคย
      login มาก่อน ทั้ง 2 request's `get_current_user()` แข่งกัน INSERT `google_sub` เดียวกัน
      ตัวที่แพ้ชน UNIQUE constraint แล้ว 500 ทั้ง endpoint แก้ที่ `app/core/auth.py`: ดัก
      `IntegrityError` ตอน flush แล้ว rollback + select ใหม่ (ได้ row ที่อีก request เพิ่ง commit
      ไป) เพิ่ม regression test `test_auth_race.py` (ใช้ temp-file SQLite ไม่ใช่ `:memory:` เพราะ
      `:memory:` + StaticPool ใช้ connection เดียวจริง ไม่สามารถจำลอง 2 transaction ที่เป็นอิสระ
      จากกันจริงได้) ยืนยันแล้วว่า test นี้ fail จริงถ้าไม่มี fix (ลอง revert แล้วรัน) และผ่านหลัง fix
- [x] Frontend: `BirthDataForm.tsx` เพิ่ม section "การพยากรณ์ล่วงหน้า (ไม่บังคับ)" — checkbox 4 ตัว
      (Solar Arc/Transit/Lunar Return/Relocation) แต่ละตัวเปิดฟิลด์ของตัวเองเมื่อติ๊ก ปิดเมื่อไม่ติ๊ก
      ตามที่ผู้ใช้ขอ, `onSubmit` ส่ง `ForecastOptions` เพิ่มจาก `BirthData` เดิม
- [x] Frontend: `app/api/forecast/route.ts` (BFF proxy ใหม่ เหมือน `app/api/reading/route.ts`),
      `lib/api.ts` เพิ่ม type + `getForecast()`, `reading/page.tsx` ยิง `getReading()` +
      `getForecast()` พร้อมกันด้วย `Promise.all` (forecast เป็น best-effort — ถ้าพังไม่บังการอ่าน
      หลักด้วย `.catch(() => null)`), `ReadingResult.tsx` เพิ่ม tab "การพยากรณ์ล่วงหน้า" (โชว์เฉพาะ
      เมื่อมีผลลัพธ์) แสดงตาราง picture ต่อเทคนิค
- [x] ทดสอบผ่านเบราว์เซอร์จริงแล้ว (Playwright): คลิก checkbox ครบ 4 ตัว ยืนยันฟิลด์เปิด/ปิดถูกต้อง,
      submit ผ่าน tarot/oracle draw จนถึงหน้าผลลัพธ์, เห็น forecast tab พร้อมตาราง Solar
      Arc/Transit/Lunar Return จริงจาก backend local (bypass login ชั่วคราวเพราะ sandbox นี้ทำ
      Google OAuth จริงไม่ได้ — revert กลับหมดแล้วก่อนจบงาน ยืนยันด้วย `git diff` ว่าไฟล์ auth
      กลับสู่สภาพเดิม), `npm run build`/`npm run lint` ผ่าน, backend 87 tests ผ่าน, ruff clean
- [x] **แก้ไข 2026-08-13 (Phase 13)**: relocation มี autocomplete ค้นหาสถานที่แล้วเหมือนช่อง
      สถานที่เกิด — ดู Phase 13 ด้านล่าง
- [ ] **ยังไม่ทำ**: การจำกัด (rate limit) หรือแคชผลลัพธ์ forecast

## Phase 13 — Daily M/A + Transit Axes, สังเคราะห์ forecast เข้า Gemini, relocation autocomplete, ปุ่มข้าม

ผู้ใช้ขอ 4 อย่างพร้อมกัน (2026-08-13): (1) คำนวณ Daily M/A + Transit Axes ให้ครบตามที่ Phase 11
เหลือไว้ (2) แก้ช่อง relocation ให้มี autocomplete เหมือนช่อง "สถานที่เกิด" (3) เพิ่มปุ่มข้ามให้ดูผล
พยากรณ์ล่วงหน้าทีละแบบได้ (4) **กลับคำตัดสินใจ Phase 12**: การสังเคราะห์ผลของ Gemini ต้องเอา
Transit/Solar Arc/Lunar Return/Relocation ไปพิจารณาด้วย ไม่ใช่แค่แสดงตารางดิบแยกจากคำทำนาย

- [x] Backend: `transit_positions()` รับ `birth_data` เพิ่ม (optional) — ถ้าส่งมา คำนวณ Ascendant/
      Midheaven ณ วันเวลาที่ระบุ (สถานที่เกิดเดิม) เพิ่มเป็นปัจจัย `A`/`M` ในชุดตำแหน่ง transit
      นี่คือ "Daily M/A" (ตรงข้ามกับ relocation ที่ตรึงเวลาเกิดแต่เปลี่ยนสถานที่ — Daily M/A ตรึง
      สถานที่เกิดแต่เปลี่ยนเวลาเป็นวันปัจจุบัน) เพิ่ม `DAILY_ANGLE_BASES = {"A", "M"}` ใน
      `transit.py` ให้ `_has_reference_personal_point()` นับ `t:A`/`t:M` เป็นจุดอ้างอิงส่วนตัวได้
      ด้วย (ปกติปัจจัยที่กำลัง transit ไม่นับเป็น personal point เพราะเป็นดาวที่กำลังเคลื่อนที่ แต่ Daily
      M/A เป็นข้อยกเว้น เพราะเป็นมุมอ้างอิงคงที่ของวันนั้น ไม่ใช่ดาวเคราะห์) — เมื่อมี Daily M/A แล้ว
      **Transit Axes** (ภาพที่สร้างจากท้องฟ้าวันนี้ล้วนๆ รวม Daily M/A โดยไม่ต้องมีปัจจัย radix/directed
      เลย) เกิดขึ้นได้เองผ่าน `find_transit_pictures()` เดิมโดยไม่ต้องเขียนฟังก์ชันแยก — เพิ่ม unit
      test 3 เคสยืนยัน (มี/ไม่มี Daily M/A, Transit Axes ล้วนๆ หา picture เจอจริง) — รวม 81 tests
- [x] Backend: **กลับคำตัดสินใจ Phase 12** — รวม `/api/reading` กับความสามารถของ `/api/forecast`
      เข้าด้วยกัน: เพิ่ม `ReadingRequest` (`birth_data` + `solar_arc`/`transit`/`lunar_return`/
      `relocation` optional เหมือน `ForecastRequest`) เป็น body ใหม่ของ `POST /api/reading`
      (เดิมรับ `BirthData` ตรงๆ) — endpoint คำนวณ forecast (ถ้ามีการเลือก) ผ่าน `_compute_forecast()`
      ที่ดึงมาเป็นฟังก์ชันร่วมให้ `/api/reading`/`/api/forecast` ใช้ร่วมกัน (กันโค้ดสองจุดเพี้ยนออก
      จากกัน) แล้วส่ง `ForecastResponse` เข้า `synthesize()` เป็น argument ที่ 4 (optional) —
      `SynthesisOutput` เพิ่ม field `forecast: ForecastResponse | None` เก็บผลไว้ให้ frontend แสดง
      ตารางดิบต่อได้เหมือนเดิม แม้จะสังเคราะห์เป็นคำทำนายไปแล้วก็ตาม — `/api/forecast` (standalone,
      ไม่ synthesize, ไม่บันทึกประวัติ) ยังอยู่เหมือนเดิมสำหรับกรณีอยากได้ตารางดิบอย่างเดียว
- [x] Backend: `master_interpreter.py` — `synthesize()` รับ `forecast` เป็น argument ที่ 4
      (optional) ใส่เข้า payload ที่ส่งให้ Gemini เป็น key `"forecast"` เพิ่มกฎข้อ 4 ใน
      `SYSTEM_PROMPT` บอกให้พิจารณา forecast เป็น "ชั้นจังหวะเวลา" เสริม ด้วยหลัก 3 ขั้นตอนเดียวกัน
      (จุดร่วม/ความขัดแย้ง/เติมเต็ม) — `_fallback_synthesis()` เพิ่ม `_forecast_summary_lines()`
      สรุปผล forecast แบบข้อความสั้นต่อท้าย `final_reading` เวลา Gemini ใช้งานไม่ได้
- [x] Backend: อัปเดต test suite ทั้งหมดให้ตรงกับ request shape ใหม่ (`json={"birth_data": ...}`
      แทน `json=BIRTH_DATA` ตรงๆ), เพิ่ม test ยืนยันว่า `/api/reading` พร้อม forecast option คืน
      `forecast` ใน response และบันทึกลง history ถูกต้อง, เพิ่ม test จับ payload ที่ส่งให้ Gemini
      client จริง (fake) ว่ามี/ไม่มี key `"forecast"` ตรงตามที่ควร — รวม **96 tests ผ่านหมด**, ruff
      clean
- [x] Frontend: สร้าง `frontend/src/lib/usePlaceSearch.ts` (custom hook) ดึง logic ค้นหาสถานที่
      แบบ debounce 600ms ที่เดิมอยู่เฉพาะช่อง "สถานที่เกิด" ออกมาใช้ร่วมกันได้ — `BirthDataForm.tsx`
      เปลี่ยนทั้งช่อง "สถานที่เกิด" และช่อง relocation ให้ใช้ hook เดียวกัน ทำให้ relocation ได้
      dropdown ผลค้นหาจริง + auto-fill ละติจูด/ลองจิจูด เหมือนช่องสถานที่เกิดทุกประการ (เดิม
      relocation กรอกพิกัดเองล้วนๆ)
- [x] Frontend: `lib/api.ts` ลบ `getForecast()`/`hasForecastOptions()` ออก (ไม่ต้องยิง 2 endpoint
      แยกกันอีกต่อไป) — `getReading(birthData, forecastOptions)` ยิง `/api/reading` ครั้งเดียว
      ส่ง `{ birth_data, ...forecastOptions }` ตรงกับ `ReadingRequest` ใหม่ `SynthesisOutput` type
      เพิ่ม `forecast: ForecastResponse | null` — `reading/page.tsx` ตัด state/การเรียกแยกของ
      forecast ออก เหลือ `getReading()` เรียกเดียว
      `ReadingResult.tsx` เพิ่ม `ForecastTab` component: ถ้ามี forecast มากกว่า 1 หมวด (เช่น Solar
      Arc + Transit) จะโชว์แถบปุ่ม "ข้ามไปดู: Solar Arc / Transit / Lunar Return / Relocation" ให้
      คลิกสลับดูทีละหมวดแทนการเลื่อนดูทั้งหมด (ถ้ามีแค่หมวดเดียวไม่โชว์แถบปุ่ม เพราะไม่มีอะไรให้ข้าม)
- [x] ทดสอบแล้ว: backend 96 tests ผ่าน, `ruff check`/`ruff format --check` สะอาด, frontend
      `npm run build`/`npm run lint` ผ่าน, ยืนยันผ่านเบราว์เซอร์ (Playwright, bypass login ชั่วคราว
      เหมือน Phase 12 แล้ว revert กลับหมดก่อนจบงาน) ว่า flow ทั้งหมดทำงานถูกต้องจนถึงหน้าผลลัพธ์
      พร้อม forecast tab — การค้นหาสถานที่ของช่อง relocation ยืนยันด้วยโค้ดว่าใช้ mechanism เดียวกัน
      กับช่องสถานที่เกิดที่ยืนยันแล้วว่าใช้งานได้จริง (ทดสอบ live network call ผ่าน dropdown จริงใน
      sandbox นี้ไม่ได้ เพราะ browser ที่ควบคุมด้วย Playwright ไม่ผ่าน proxy ของ sandbox ไปยัง
      Nominatim ได้ — เป็นข้อจำกัดของสภาพแวดล้อมทดสอบ ไม่ใช่บั๊กของโค้ด)
- [ ] **ข้อจำกัดที่ทดสอบในนี้ไม่ได้**: คุณภาพจริงของการสังเคราะห์ forecast โดย Gemini (มี key จริง)
      ยังทดสอบไม่ได้ในนี้ เหมือนข้อจำกัดเดิมของ Phase 6/10 — ทดสอบได้แค่ path fallback กับ payload
      shape ที่ถูกต้อง

## Phase 14 — axis_meanings.yaml ครบ 5 แกน (M/A/Sun/Moon/Node)

ผู้ใช้ส่งไฟล์หนังสือ (`uranianchaptersth.zip`, 12 ไฟล์ต่อบท) ตามที่บอกไว้ใน Phase 13 ว่า "มีข้อมูล
แล้วเด่วส่งให้" — ตรวจสอบแล้วพบว่าเนื้อหาเหมือนกับ `research/uranian-delineation-axes.md` ที่มีอยู่
แล้วทุกประการ (จาก handoff package เดิม, Phase 11) เพียงแค่ถูกแบ่งเป็นไฟล์ต่อบทแทนไฟล์รวมตามหัวข้อ
— ไม่มีเนื้อหาใหม่ แต่ยืนยันว่าเนื้อหาที่มีอยู่แล้วถูกต้องครบถ้วนพอจะแปลงเป็น YAML ได้เลย

- [x] แปลงตาราง A-Axis/Sun-Axis/Moon-Axis/Node-Axis จาก `research/uranian-delineation-axes.md`
      หัวข้อ 3-6 เป็น `axis_meanings.yaml` เพิ่มจากที่มีแค่แกน M เดิม — backfill คู่ที่หนังสือเขียนไว้
      ฝั่งเดียว (เช่น "M + A" อยู่ใต้หัวข้อ M แต่ไม่มี "A + M" ซ้ำใต้หัวข้อ A) ด้วยข้อความเดียวกันข้าม
      แกน เพราะ midpoint สมมาตร ผลคือ M/A/MOON/NODE ครบ 21 คู่ (ทุกปัจจัยอื่น) ส่วน SUN ได้ 19 คู่
      (ต้นฉบับไม่เคยระบุความหมาย Sun+Apollon และ Sun+Admetos)
- [x] `engine.py`: `_picture_finding()` เดิม hardcode เช็คเฉพาะแกน M (`if "M" in factors`) — แก้เป็น
      loop ทุกแกนที่มีใน `axis_meanings.yaml` และอยู่ในภาพนั้นจริง เพื่อให้ภาพที่มีมากกว่าหนึ่งแกน
      (เช่น M/Mars=Sun/Saturn มีทั้ง M และ SUN) ได้หมายเหตุจากทุกแกน ไม่ใช่แค่แกนแรกที่เจอ
- [x] เพิ่ม unit test 8 เคสใน `test_uranian_knowledge_base.py` (ครอบคลุมทุกแกน + หลายแกนพร้อมกันใน
      ภาพเดียว) — รวม 102 tests ผ่านหมด, ruff clean — ยืนยันด้วย manual run จริงกับวันเกิด 22 กรกฎาคม
      1990 ว่าภาพที่มีมากกว่าหนึ่งแกนได้หมายเหตุครบทุกแกนจริง (เช่น A/Mars=Apollon/Neptune ได้ทั้ง 3
      หมายเหตุจากแกน A)
- [ ] **ยังไม่ได้ทำ**: `house_meanings` (เนื้อหา "ธรรมชาติของเรือนที่ดาวสถิต" ต่อดาว มีอยู่แล้วใน
      `research/uranian-delineation-axes.md` หัวข้อ 7 แต่การคำนวณจริงว่าดาวแต่ละดวงตกเรือนที่เท่าไหร่
      ยังไม่ implement — ต้องคำนวณ house cusp แบบ equal-house จาก M ก่อน ซึ่งเอกสารต้นทางที่มีอยู่
      (บทที่ 4) อธิบายแค่หลักการกว้างๆ ไม่ได้ให้สูตรคำนวณละเอียดพอจะ implement ได้ทันทีโดยไม่เดา —
      รอผู้ใช้ยืนยัน convention ที่แน่นอนก่อน), แกน ARIES ของ `axis_meanings.yaml` (ไม่มีเนื้อหา
      ต้นฉบับให้ถอดความ), Sun+Apollon/Sun+Admetos
