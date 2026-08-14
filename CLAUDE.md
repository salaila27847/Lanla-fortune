# CLAUDE.md — คู่มือสำหรับ Claude Code ในโปรเจกต์นี้

โปรเจกต์นี้คือเว็บแอปดูดวงที่ผสาน 3 ศาสตร์เข้าด้วยกันแบบสมบูรณ์: **โหราศาสตร์ยูเรเนียน**, **ไพ่ทาโรต์**, และ **ไพ่ออราเคิล** อ่านเอกสารนี้ก่อนเริ่มงานทุกครั้ง

## 1. ภาพรวมสถาปัตยกรรม

ระบบจำลองโครงสร้างทีมงานเป็นสถาปัตยกรรมซอฟต์แวร์ 4 ชั้น:

```
ผู้ใช้ป้อนข้อมูล (วันเกิด / คำถาม / ไพ่ที่จั่ว)
        │
        ▼
 ┌──────────────┬──────────────┬──────────────┐
 │  Uranian     │   Tarot      │   Oracle     │   ← 3 โมดูลอิสระ ทำงานคู่ขนาน
 │  Engine      │   Engine     │   Engine     │
 └──────────────┴──────────────┴──────────────┘
        │              │              │
        └──────────────┼──────────────┘
                        ▼
              Master Interpreter
        (Synthesis Layer — เรียก Gemini API)
                        │
                        ▼
              คำทำนายฉบับสมบูรณ์ (output)
```

**หลักการที่ห้ามละเมิด:**
- **ห้ามใส่ personal bias** — Master Interpreter ต้องตีความจากผลลัพธ์ดิบของ 3 engine เท่านั้น ห้าม hardcode น้ำเสียงส่วนตัวหรือความเชื่อของผู้พัฒนา
- **ห้ามใช้ประวัติการค้นคว้า/ใช้งานของผู้ใช้** — ห้ามดึง browsing/search history หรือ session ก่อนหน้ามาปรุงแต่งคำทำนาย ใช้เฉพาะข้อมูลที่ผู้ใช้ป้อนในเซสชันปัจจุบัน (privacy-by-design)
- **แต่ละ engine ต้องทำงานได้อิสระ** — ทดสอบ/เรียกใช้แยกจากกันได้ ก่อนจะเข้าสู่ชั้นสังเคราะห์

## 2. Tech stack (ตัดสินใจแล้ว)

| ส่วน | เทคโนโลยี | เหตุผล |
|---|---|---|
| Backend | Python 3.11+, FastAPI, Pydantic v2 | เหมาะกับ ephemeris library (`pyswisseph`) สำหรับคำนวณยูเรเนียน และ async I/O เวลาเรียก Gemini API |
| Database | PostgreSQL (dev: SQLite ผ่าน SQLAlchemy, prod: Neon) | โครงสร้างข้อมูลชัดเจน รองรับการขยาย — Neon เพราะ free tier ไม่ต้องผูกบัตรเครดิต |
| Knowledge base | ไฟล์ YAML/JSON versioned ใน `backend/app/knowledge_base/` | ให้ "เจ้าหน้าที่ค้นคว้า" (คนจริง) แก้ไขได้โดยไม่แตะโค้ด, track ผ่าน git |
| Frontend | Next.js 14+ (App Router), TypeScript, TailwindCSS | SSR ดี, ทำ 90° dial แบบ interactive และ animation จั่วไพ่ได้ลื่นด้วย Framer Motion |
| Synthesis layer | `google-genai` Python SDK เรียก `gemini-3.1-flash-lite` | **แก้ไข 2026-08-12**: เปลี่ยนจาก Anthropic Claude API เป็น Gemini API ตามที่ผู้ใช้ตัดสินใจ — Gemini มี free tier จริง (rate-limited แต่ไม่ต้องผูกบัตรเครดิต) สอดคล้องกับ Render/Vercel/Neon ที่เลือกไว้แล้วเพราะเหตุผลเดียวกัน — **แก้ไข 2026-08-14**: เปลี่ยนโมเดลจาก `gemini-3.5-flash` เป็น `gemini-2.5-flash-lite` เพราะ `gemini-3.5-flash` เจอ free-tier quota ต่ำผิดปกติ (`generate_content_free_tier_requests` แค่ 20 request/วัน) ทำให้ทุกคำทำนายจริงตกไป fallback เกือบตลอด — `gemini-2.5-flash-lite` มี quota หลวมกว่ามาก (รายงานว่า ~1,500 req/วันสำหรับกลุ่ม Flash/Flash-Lite ตามเอกสาร Google ล่าสุด) — **แก้ไข 2026-08-14 (ต่อมา)**: `gemini-2.5-flash-lite` ใช้งานไม่ได้จริง — Gemini ตอบ `404 NOT_FOUND` ("This model models/gemini-2.5-flash-lite is no longer available to new users") เปลี่ยนเป็น `gemini-3.1-flash-lite` แทนตามที่ผู้ใช้ระบุ |
| Auth/session | Google Sign-In (OAuth) ผ่าน NextAuth.js (Auth.js) ฝั่ง frontend | ผู้ใช้ตัดสินใจแล้ว (2026-08-12) — สมัคร/ล็อกอินง่าย ไม่ต้องจัดการรหัสผ่านเอง |
| Deployment | Vercel (frontend) + Render (backend) + Neon (Postgres) | ผู้ใช้ตัดสินใจแล้ว (2026-08-12) — ทั้ง 3 บริการไม่ต้องผูกบัตรเครดิตเลย (ตรวจสอบราคาจริงแล้ว, ดูหัวข้อ 6) |

**อย่าเปลี่ยน stack นี้โดยไม่ถามผู้ใช้ก่อน** — เป็นการตัดสินใจที่ยืนยันแล้ว

## 3. ลำดับการพัฒนา (ผู้ใช้ยืนยันแล้ว: วางโครงทั้ง 3 ศาสตร์พร้อมกัน)

อ่าน `docs/task-breakdown.md` สำหรับรายละเอียด แต่หลักการคือ:
1. วางโครง backend module ทั้ง 3 (`modules/uranian`, `modules/tarot`, `modules/oracle`) พร้อมกันแบบมี interface เดียวกัน (shared base class/protocol)
2. แต่ละ module ต้องมี stub ที่ return mock data ได้ก่อน เพื่อให้ synthesis layer และ frontend ต่อไปพัฒนาคู่ขนานได้
3. Master Interpreter (synthesis layer) พัฒนาคู่ขนานโดยรับ mock data จากทั้ง 3 module ไปก่อน แล้วค่อยสลับเป็นของจริงทีละตัว
4. Frontend พัฒนาคู่ขนานโดยเรียก mock API endpoints

## 4. Coding conventions

- Python: ใช้ type hints ทุกฟังก์ชัน, format ด้วย `ruff format`, lint ด้วย `ruff check`
- แต่ละ engine module ต้อง implement interface เดียวกัน (ดู `docs/data-schema.md` → `EngineResult`) เพื่อให้ Master Interpreter เรียกใช้แบบเดียวกันได้ทั้ง 3 ศาสตร์
- ห้าม commit API key ใดๆ — ใช้ `.env` (มี `.env.example` เป็นแม่แบบ)
- Frontend: ใช้ TypeScript strict mode, component ละ 1 ไฟล์, ใช้ Tailwind utility classes ไม่เขียน CSS แยก
- Commit message ภาษาอังกฤษ, รูปแบบ conventional commits (`feat:`, `fix:`, `docs:`)

## 5. เอกสารที่ต้องอ่านก่อนเริ่ม

- `docs/PRD.md` — ข้อกำหนดผลิตภัณฑ์ฉบับเต็ม
- `docs/data-schema.md` — schema ของทุก entity (birth data, tarot card, oracle card, engine result, synthesis output)
- `docs/task-breakdown.md` — task ที่แบ่งเป็นเฟส พร้อม checklist

## 6. คำถามที่ยังไม่ตัดสินใจ (ให้ถามผู้ใช้ก่อนลงมือ ถ้าเจอ)

(ไม่มีในตอนนี้ — คำถามที่เคยค้างไว้ทั้งหมดตัดสินใจแล้ว ดูหัวข้อด้านล่าง)

### ตัดสินใจแล้ว
- **ชุดไพ่ออราเคิลหลัก**: สร้างขึ้นเอง (ไม่ใช้สำนักสำเร็จรูป) ผสาน 4 ธีม — เทวดา & นางฟ้าผู้พิทักษ์,
  สัตว์นำทางแบบไทย, ดอกไม้แห่งจิตวิญญาณ, เงาแห่งบทเรียน — รวม 88 ใบ (22 ใบ/ธีม) ชื่อ deck:
  "ลานลาออราเคิล" (`lanla_original`) ผู้ใช้เลือกสลับไปใช้ deck อื่นได้ในแอป — ดู
  `backend/app/knowledge_base/oracle/README.md` — **แก้ไข 2026-08-12 (ต่อมา)**: เดิมมี 3 ธีม/60 ใบ
  ทั้งหมดเป็น Light Work ผู้ใช้ทักท้วงว่าขาดใบเตือนภัย/สัจธรรมด้านที่ไม่สบายใจ จึงเพิ่มหมวด
  "เงาแห่งบทเรียน" (สัญลักษณ์ธรรมชาติ เช่น พายุ/หมอก/ไฟป่า แทนวัตถุ) และเติมอีก 2 ใบ/หมวดเดิม
  ให้ครบ 22 เท่ากันทุกหมวด **ตัดสินใจไม่เพิ่มหมวดธาตุ/วัตถุ/กาลเวลาตามที่มีคนเสนอ** เพราะไพ่ทาโรต์
  ในแอปนี้เป็นชุด RWS มาตรฐานครบ 78 ใบอยู่แล้ว (4 suits ครอบธาตุ/วัตถุ-อารมณ์-ความคิดอยู่แล้ว
  ทุกใบมีความหมายกลับหัวเป็น shadow ในตัว) เพิ่มหมวดแบบนั้นในออราเคิลจะซ้ำหน้าที่เอนจินทาโรต์
- **Deployment target**: Vercel (frontend, Next.js) + Render (backend FastAPI) + Neon (Postgres) —
  แก้ไข 2026-08-12: ตอนแรกแนะนำ Railway แต่ผู้ใช้ทักท้วงว่าไม่ฟรีจริง (ตรวจสอบแล้วพบว่า Railway
  ให้ trial credit $5 ครั้งเดียว 30 วัน ต้องผูกบัตรเครดิตตั้งแต่สมัคร) จึงเปลี่ยนเป็น Render + Neon
  ซึ่งทั้งคู่ไม่ต้องผูกบัตรเครดิตเลย (Render free web service sleep หลังไม่มีคนใช้ 15 นาที,
  Neon Postgres free tier ไม่หมดอายุ) — มี `render.yaml` (Blueprint) แล้ว และขั้นตอน deploy
  ทั้งหมดอยู่ใน `docs/deployment.md` (ต้องทำผ่านบัญชีผู้ใช้เองในแต่ละ dashboard เนื่องจากต้องใช้
  ข้อมูลลับ/บัญชีส่วนตัว) — **แก้ไข**: เชื่อม Neon แล้ว (บังคับ ไม่ใช่ตัวเลือก) เพราะ backend มี DB
  layer จริงแล้ว (`backend/app/db/`) รองรับฟีเจอร์เก็บประวัติคำทำนายด้านล่าง
- **ระบบสมาชิก**: ใช้ Google Sign-In (OAuth) implement แล้วด้วย `next-auth@5` (Auth.js) — ดู
  `frontend/README.md` หัวข้อ "ตั้งค่า Google Sign-In" ปุ่มล็อกอินอยู่ใน Header ทุกหน้า —
  **แก้ไข 2026-08-12**: ผู้ใช้ตัดสินใจแล้วทั้ง 2 ข้อที่เคยค้างไว้: (1) **บังคับล็อกอิน**ก่อนใช้
  `/reading` และ `/history` แล้ว (เปลี่ยนจาก guest-friendly เดิม) ผ่าน `frontend/src/proxy.ts`
  (Next.js 16 เปลี่ยนชื่อ `middleware.ts` เป็น `proxy.ts` — ระวังอย่าสร้าง `middleware.ts` ใหม่
  จะไม่ทำงาน) (2) **เก็บประวัติคำทำนายผูกกับ user** แล้ว — ทุกครั้งที่เรียก `/api/reading` สำเร็จ
  จะบันทึกลง Postgres/SQLite อัตโนมัติ ดูได้ที่ `/history` สถาปัตยกรรมยืนยันตัวตนใช้ BFF proxy
  pattern: browser ไม่เรียก FastAPI backend ตรงๆ อีกแล้ว แต่ผ่าน Next.js Route Handler
  (`frontend/src/app/api/reading/route.ts`) ที่ตรวจ session ฝั่ง server ก่อน แล้วส่งต่อไป backend
  พร้อม shared secret (`INTERNAL_API_SECRET`) — **กฎ "ห้ามใช้ประวัติผู้ใช้" ในข้อ 1 ยังคงอยู่**:
  ประวัติที่เก็บไว้ใช้แสดงผลให้ผู้ใช้ดูเองเท่านั้น ห้ามดึงกลับไปป้อนให้ Master Interpreter ทุกกรณี
- **LLM ของ synthesis layer**: **แก้ไข 2026-08-12** — เปลี่ยนจาก Anthropic Claude API เป็น
  Google Gemini API (`google-genai` SDK, ตอนนั้นใช้ `gemini-3.5-flash`) ตามที่ผู้ใช้ตัดสินใจ เพราะ
  Gemini มี free tier จริงที่ไม่ต้องผูกบัตรเครดิต (มี rate limit แต่พอสำหรับ demo/personal project)
  — **แก้ไข 2026-08-14**: production จริงเจอ `429 RESOURCE_EXHAUSTED` เกือบทุกครั้งเพราะ
  `gemini-3.5-flash` มี free-tier quota แค่ 20 request/วัน (`generate_content_free_tier_requests`)
  — เปลี่ยนเป็น `gemini-2.5-flash-lite` แทน (quota หลวมกว่ามาก) ผ่าน `SYNTHESIS_MODEL` env var
  (`render.yaml`/`backend/.env.example`) — **แก้ไข 2026-08-14 (ต่อมา)**: `gemini-2.5-flash-lite`
  ตอบ `404 NOT_FOUND` ("no longer available to new users") — เปลี่ยนเป็น `gemini-3.1-flash-lite`
  แทนตามที่ผู้ใช้ระบุ ยังใช้ `google-genai` SDK ตัวเดิม ไม่เปลี่ยน provider — ต้องใช้
  `GEMINI_API_KEY` แทน `ANTHROPIC_API_KEY` (จาก [aistudio.google.com](https://aistudio.google.com))
  interface ของ `synthesize()` ใน `backend/app/synthesis/master_interpreter.py` ไม่เปลี่ยน —
  รับ 3 `EngineResult` แล้วคืน `SynthesisOutput` เหมือนเดิม เปลี่ยนแค่ตัว client/provider ข้างใน
  `_fallback_synthesis()` (Phase 6 QA) เป็น provider-agnostic อยู่แล้ว ไม่ต้องแก้
