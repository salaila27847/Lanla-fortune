# Deployment guide — Vercel + Render + Neon

สแต็กที่ตัดสินใจแล้ว (ดู `CLAUDE.md` หัวข้อ 2 และ 6): **Vercel** (frontend) + **Render**
(backend) + **Neon** (Postgres) — ทั้ง 3 ไม่ต้องผูกบัตรเครดิต

ขั้นตอนด้านล่างต้องทำผ่านบัญชีของคุณเองในแต่ละ dashboard (ล็อกอิน, เชื่อม GitHub, ตั้งค่า
environment variables) — Claude ไม่มีสิทธิ์เข้าถึงบัญชีเหล่านี้ให้คุณได้ ไฟล์ `render.yaml` ที่มีอยู่แล้ว
ในโปรเจกต์ช่วยให้ขั้นตอน Render เป็นแบบคลิกเดียว (Blueprint)

**หมายเหตุเรื่อง Neon/Postgres:** backend ปัจจุบัน**ยังไม่มี** DB layer เลย (ไม่มีตาราง ไม่มี
SQLAlchemy model) เพราะฟีเจอร์ที่ต้องใช้ DB จริง (เก็บประวัติคำทำนายผูกกับ user) ยังไม่ตัดสินใจ
(ดู `docs/task-breakdown.md` Phase 7) — ขั้นตอน Neon ด้านล่างจึงยังไม่จำเป็นสำหรับตอนนี้ ข้ามไปก่อนได้
แอปทำงานได้ครบ (3 engine + synthesis + login) โดยไม่มี DB เลย จะกลับมาทำตอนตัดสินใจเรื่อง history แล้ว

## 1. Backend → Render

1. ไปที่ [dashboard.render.com](https://dashboard.render.com) → New → **Blueprint**
2. เชื่อม GitHub repo `salaila27847/Lanla-fortune`, branch `main`
3. Render จะเจอ `render.yaml` อัตโนมัติแล้วสร้าง web service `lanla-fortune-backend` ให้
4. ตั้งค่า environment variables ที่ทำเครื่องหมาย `sync: false` ใน `render.yaml` (ต้องกรอกเองใน
   dashboard เพราะเป็นความลับ ไม่เก็บใน git):
   - `ANTHROPIC_API_KEY` — จาก [console.anthropic.com](https://console.anthropic.com)
   - `FRONTEND_ORIGIN` — ใส่ URL ของ Vercel หลังจาก deploy frontend เสร็จ (ขั้นตอน 2) เช่น
     `https://lanla-fortune.vercel.app` — ถ้ามีหลาย origin (เช่น preview deploy) คั่นด้วย `,`
5. Deploy แล้วจด URL backend ไว้ (รูปแบบ `https://lanla-fortune-backend.onrender.com`) — ใช้ในขั้นตอน 2
6. ทดสอบว่า backend ขึ้นจริง: `curl https://<backend-url>/health` ควรได้ `{"status":"ok"}`

**ข้อจำกัด free plan:** service จะ sleep หลังไม่มีคนใช้ 15 นาที คำขอแรกหลัง sleep จะช้า
(cold start ~30-60 วินาที) — ปกติสำหรับ demo/personal project

## 2. Frontend → Vercel

1. ไปที่ [vercel.com/new](https://vercel.com/new) → import repo `salaila27847/Lanla-fortune`
2. **Root Directory** ตั้งเป็น `frontend` (สำคัญ — repo เป็น monorepo)
3. Vercel จะ detect Next.js อัตโนมัติ ไม่ต้องแก้ build command
4. ตั้งค่า environment variables (Project Settings → Environment Variables) — อิง
   `frontend/.env.example`:
   - `AUTH_SECRET` — สร้างด้วย `npx auth secret` (ค่าใหม่สำหรับ production ไม่ใช้ค่าเดียวกับ dev)
   - `AUTH_GOOGLE_ID`, `AUTH_GOOGLE_SECRET` — จาก Google Cloud Console (ดูขั้นตอน 4)
   - `NEXT_PUBLIC_API_BASE_URL` — URL backend จาก Render ในขั้นตอน 1
5. Deploy แล้วจด URL frontend ไว้ (เช่น `https://lanla-fortune.vercel.app`) — เอาไปใส่
   `FRONTEND_ORIGIN` ใน Render (ขั้นตอน 1.4) แล้ว redeploy backend อีกครั้งให้ CORS ถูกต้อง

## 3. เชื่อม Neon (ข้ามได้ตอนนี้ — ดูหมายเหตุด้านบน)

เมื่อถึงเวลาที่ต้องใช้จริง:
1. [console.neon.tech](https://console.neon.tech) → New Project → คัดลอก connection string
   (`postgresql://...`)
2. ใส่เป็น `DATABASE_URL` ใน Render environment variables
3. เพิ่ม `asyncpg` หรือ `psycopg[binary]` ใน `backend/requirements.txt` และเขียน SQLAlchemy
   models/migrations ตามฟีเจอร์ history ที่จะตัดสินใจ

## 4. อัปเดต Google OAuth Console สำหรับ production

`frontend/README.md` มีขั้นตอนตั้งค่า Google Sign-In สำหรับ dev อยู่แล้ว สำหรับ production
ต้องกลับไปที่ Google Cloud Console → APIs & Services → Credentials → OAuth client เดิม แล้ว
เพิ่ม **Authorized redirect URI** ใหม่:

```
https://<your-vercel-domain>/api/auth/callback/google
```

(เก็บ URI เดิมของ `localhost:3000` ไว้ด้วย เผื่อยัง dev ต่อ)

## 5. ทดสอบ end-to-end บน production

- เปิด URL Vercel → login ด้วย Google → กรอกข้อมูลเกิด (ลองพิมพ์ค้นหาสถานที่ด้วย เพื่อเช็ค
  Nominatim ใช้งานได้จากโดเมนจริง) → จั่วไพ่ → ดูผลคำทำนายฉบับสมบูรณ์จนจบ
- เช็ค Render logs ว่า `/api/reading` ตอบ 200 ไม่มี error เรื่อง `ANTHROPIC_API_KEY`
