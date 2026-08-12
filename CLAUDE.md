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
        (Synthesis Layer — เรียก Claude API)
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
| Backend | Python 3.11+, FastAPI, Pydantic v2 | เหมาะกับ ephemeris library (`pyswisseph`) สำหรับคำนวณยูเรเนียน และ async I/O เวลาเรียก Claude API |
| Database | PostgreSQL (dev: SQLite ผ่าน SQLAlchemy) | โครงสร้างข้อมูลชัดเจน รองรับการขยาย |
| Knowledge base | ไฟล์ YAML/JSON versioned ใน `backend/app/knowledge_base/` | ให้ "เจ้าหน้าที่ค้นคว้า" (คนจริง) แก้ไขได้โดยไม่แตะโค้ด, track ผ่าน git |
| Frontend | Next.js 14+ (App Router), TypeScript, TailwindCSS | SSR ดี, ทำ 90° dial แบบ interactive และ animation จั่วไพ่ได้ลื่นด้วย Framer Motion |
| Synthesis layer | Anthropic Python SDK เรียก `claude-sonnet-5` | ตามที่ผู้ใช้ตัดสินใจ — ใช้ LLM ช่วยตีความไขว้ 3 ศาสตร์ |
| Auth/session | Google Sign-In (OAuth) ผ่าน NextAuth.js (Auth.js) ฝั่ง frontend | ผู้ใช้ตัดสินใจแล้ว (2026-08-12) — สมัคร/ล็อกอินง่าย ไม่ต้องจัดการรหัสผ่านเอง |
| Deployment | Vercel (frontend) + Railway (backend + managed Postgres) | ผู้ใช้ตัดสินใจแล้ว (2026-08-12) ตามคำแนะนำ — ต้นทุนต่ำ, DevOps น้อย, เหมาะกับ MVP |

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
- **ชุดไพ่ออราเคิลหลัก**: สร้างขึ้นเอง (ไม่ใช้สำนักสำเร็จรูป) ผสาน 3 ธีม — เทวดา & นางฟ้าผู้พิทักษ์,
  สัตว์นำทางแบบไทย, ดอกไม้แห่งจิตวิญญาณ — รวม 60 ใบ ชื่อ deck: "ลานลาออราเคิล" (`lanla_original`)
  ผู้ใช้เลือกสลับไปใช้ deck อื่นได้ในแอป — ดู `backend/app/knowledge_base/oracle/README.md`
- **Deployment target**: Vercel (frontend, Next.js) + Railway (backend FastAPI + managed Postgres)
  ตามคำแนะนำ — เหตุผลและ checklist ดูข้อความในเซสชันนี้/README การ deploy (ยังไม่ได้สร้างไฟล์
  แยกต่างหาก)
- **ระบบสมาชิก**: ใช้ Google Sign-In (OAuth) เป็นวิธีสมัคร/ล็อกอินหลัก — ยกเลิกโมเดล guest-only
  ตาม MVP เดิม, จะ implement ด้วย NextAuth.js (Auth.js) ฝั่ง frontend
