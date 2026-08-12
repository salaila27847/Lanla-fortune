# Deployment guide — Vercel + Render + Neon

สแต็กที่ตัดสินใจแล้ว (ดู `CLAUDE.md` หัวข้อ 2 และ 6): **Vercel** (frontend) + **Render**
(backend) + **Neon** (Postgres) — ทั้ง 3 ไม่ต้องผูกบัตรเครดิต

ขั้นตอนด้านล่างต้องทำผ่านบัญชีของคุณเองในแต่ละ dashboard (ล็อกอิน, เชื่อม GitHub, ตั้งค่า
environment variables) — Claude ไม่มีสิทธิ์เข้าถึงบัญชีเหล่านี้ให้คุณได้ ไฟล์ `render.yaml` ที่มีอยู่แล้ว
ในโปรเจกต์ช่วยให้ขั้นตอน Render เป็นแบบคลิกเดียว (Blueprint)

**อัปเดต:** ตอนนี้ `/reading` และ `/history` บังคับล็อกอินแล้ว และทุกคำทำนายถูกเก็บลง Postgres
ผูกกับ user — ขั้นตอน Neon (ข้อ 3) จึงเป็นขั้นตอน**บังคับ**แล้ว ไม่ใช่ตัวเลือกอีกต่อไป

## 1. Backend → Render

1. ไปที่ [dashboard.render.com](https://dashboard.render.com) → New → **Blueprint**
2. เชื่อม GitHub repo `salaila27847/Lanla-fortune`, branch `main`
3. Render จะเจอ `render.yaml` อัตโนมัติแล้วสร้าง web service `lanla-fortune-backend` ให้
4. ตั้งค่า environment variables ที่ทำเครื่องหมาย `sync: false` ใน `render.yaml` (ต้องกรอกเองใน
   dashboard เพราะเป็นความลับ ไม่เก็บใน git):
   - `ANTHROPIC_API_KEY` — จาก [console.anthropic.com](https://console.anthropic.com)
   - `FRONTEND_ORIGIN` — ใส่ URL ของ Vercel หลังจาก deploy frontend เสร็จ (ขั้นตอน 2) เช่น
     `https://lanla-fortune.vercel.app` — ถ้ามีหลาย origin (เช่น preview deploy) คั่นด้วย `,`
     (ตอนนี้ browser ไม่ได้เรียก backend ตรงๆ แล้ว แต่เก็บไว้เผื่อเรียก `/health` เองจากที่อื่น)
   - `DATABASE_URL` — connection string จาก Neon (ดูขั้นตอน 3) วางตามที่ Neon ให้มาได้เลย ไม่ต้อง
     แก้ scheme เอง (โค้ดแปลง `postgresql://` → `postgresql+asyncpg://` ให้อัตโนมัติ)
   - `INTERNAL_API_SECRET` — สร้างด้วย `openssl rand -hex 32` แล้วเอาค่า**เดียวกันเป๊ะๆ**ไปใส่ที่
     Vercel ด้วย (ขั้นตอน 2) — ใช้ยืนยันว่าคำขอมาจาก frontend server ของเราจริง
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
   - `BACKEND_INTERNAL_URL` — URL backend จาก Render ในขั้นตอน 1 (server-only ไม่มี `NEXT_PUBLIC_`
     prefix — browser ไม่เห็นค่านี้เลย)
   - `INTERNAL_API_SECRET` — ต้องตรงกับค่าที่ตั้งใน Render ขั้นตอน 1.4 เป๊ะๆ
5. Deploy แล้วจด URL frontend ไว้ (เช่น `https://lanla-fortune.vercel.app`) — เอาไปใส่
   `FRONTEND_ORIGIN` ใน Render (ขั้นตอน 1.4) แล้ว redeploy backend อีกครั้ง

## 3. เชื่อม Neon (บังคับ — ไม่มี DB แล้วล็อกอินไม่ได้ผลจริง เพราะเก็บประวัติไม่ได้)

1. [console.neon.tech](https://console.neon.tech) → New Project → คัดลอก connection string
   (`postgresql://...`) มาวางใน `DATABASE_URL` ที่ Render ตรงๆ ได้เลย ไม่ต้องแก้อะไร
2. Deploy backend ใหม่อีกครั้ง — ตอน startup แอปจะสร้างตาราง `users`/`readings` อัตโนมัติ
   (`Base.metadata.create_all`, ไม่ใช้ Alembic เพราะยังไม่มี migration ในโปรเจกต์)
3. ทดสอบว่าตารางถูกสร้างจริง: เข้า Neon dashboard → SQL Editor → `\dt` หรือ
   `select * from users limit 1;` ควรรันได้ไม่ error (แม้ว่าจะยังไม่มีแถวข้อมูล)

## 4. อัปเดต Google OAuth Console สำหรับ production

`frontend/README.md` มีขั้นตอนตั้งค่า Google Sign-In สำหรับ dev อยู่แล้ว สำหรับ production
ต้องกลับไปที่ Google Cloud Console → APIs & Services → Credentials → OAuth client เดิม แล้ว
เพิ่ม **Authorized redirect URI** ใหม่:

```
https://<your-vercel-domain>/api/auth/callback/google
```

(เก็บ URI เดิมของ `localhost:3000` ไว้ด้วย เผื่อยัง dev ต่อ)

## 5. ทดสอบ end-to-end บน production

- เปิด URL Vercel → เข้า `/reading` ตรงๆ ก่อน (ยังไม่ล็อกอิน) ควรเด้งกลับหน้าแรกพร้อม `callbackUrl`
- login ด้วย Google → ควรเด้งกลับ `/reading` อัตโนมัติ → กรอกข้อมูลเกิด (ลองพิมพ์ค้นหาสถานที่ด้วย
  เพื่อเช็ค Nominatim ใช้งานได้จากโดเมนจริง) → จั่วไพ่ → ดูผลคำทำนายฉบับสมบูรณ์จนจบ
- เข้า `/history` เช็คว่าคำทำนายที่เพิ่งดูปรากฏอยู่ในประวัติ
- เช็ค Render logs ว่า `/api/reading` และ `/api/readings` ตอบ 200 ไม่มี error เรื่อง
  `ANTHROPIC_API_KEY`/`INTERNAL_API_SECRET`/`DATABASE_URL`
