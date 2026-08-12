# Frontend — Fortune App

Next.js 14+ (App Router), TypeScript, TailwindCSS. Scaffolded with:

```bash
npx create-next-app@latest . --typescript --tailwind --app --eslint --src-dir --import-alias "@/*"
npm install framer-motion   # สำหรับ animation จั่วไพ่ / 90° dial
npm install next-auth@beta  # Google Sign-In (Auth.js v5)
```

## โครงสร้างที่มีอยู่จริง

- `src/app/page.tsx` — หน้า landing
- `src/app/reading/page.tsx` — wizard เดียว: กรอกข้อมูลเกิด → จั่วไพ่ทาโรต์ → จั่วไพ่ออราเคิล →
  แสดงคำทำนายฉบับสมบูรณ์ (ใช้ step state ไม่ได้แยกเป็นหลาย route ตามที่วางแผนไว้ตอนแรก) —
  **ต้องล็อกอินก่อนถึงจะเข้าได้** (ดูหัวข้อ "ล็อกอินก่อนดูดวง" ด้านล่าง)
- `src/app/history/page.tsx` — ประวัติคำทำนายของผู้ใช้ที่ล็อกอินอยู่ (ต้องล็อกอินเช่นกัน)
- `src/components/BirthDataForm.tsx`, `CardDrawStep.tsx`, `ReadingResult.tsx` — component ของแต่ละ step
- `src/components/Header.tsx`, `AuthButton.tsx` — header ที่มีปุ่มล็อกอิน/ล็อกเอาต์ Google ทุกหน้า
  (มีลิงก์ "ดูประวัติคำทำนาย" เพิ่มเมื่อล็อกอินแล้ว)
- `src/lib/api.ts` — client เรียก `/api/reading` (route handler ของ Next.js เอง ไม่ใช่ backend ตรงๆ)
- `src/lib/backend.ts` — server-only helper แนบ `X-Internal-Secret`/`X-User-*` แล้วเรียก backend จริง
- `src/app/api/reading/route.ts` — proxy: ตรวจ session ฝั่ง server แล้วส่งต่อไป backend
- `src/proxy.ts` — กันไม่ให้เข้า `/reading`, `/history` ถ้ายังไม่ล็อกอิน (Next.js 16 เปลี่ยนชื่อจาก
  `middleware.ts` เป็น `proxy.ts` — อย่าสร้างไฟล์ `middleware.ts` ใหม่)
- `src/auth.ts`, `src/app/api/auth/[...nextauth]/route.ts` — ตั้งค่า Google Sign-In (Auth.js v5)

## ตั้งค่า Google Sign-In (ต้องทำก่อนล็อกอินได้จริง)

1. สร้าง `.env.local` จาก `.env.example`
2. รัน `npx auth secret` เพื่อสร้างค่า `AUTH_SECRET` แบบสุ่ม (หรือใช้ `python3 -c "import secrets; print(secrets.token_hex(32))"`)
3. ไปที่ [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials
   → Create Credentials → OAuth client ID → เลือก "Web application"
4. ใส่ Authorized redirect URI: `http://localhost:3000/api/auth/callback/google` (dev) และโดเมนจริงตอน deploy
5. คัดลอก Client ID / Client Secret ใส่ `AUTH_GOOGLE_ID` / `AUTH_GOOGLE_SECRET` ใน `.env.local`

ไม่มี `AUTH_GOOGLE_ID`/`AUTH_GOOGLE_SECRET` จริง ปุ่มล็อกอินจะพา redirect ไป Google แล้วเจอ error
จาก Google เอง เพราะ client ID ไม่มีตัวตนจริง

## ล็อกอินก่อนดูดวง (`/reading`, `/history`)

ตั้งแต่เพิ่มฟีเจอร์เก็บประวัติคำทำนาย ทั้งสองหน้านี้**บังคับล็อกอิน**แล้ว ต้องตั้งค่าเพิ่มอีก 2 ตัวใน
`.env.local` (ดู `.env.example`):

- `BACKEND_INTERNAL_URL` — URL ของ backend FastAPI, server-only ไม่ถูกส่งไปที่ browser
- `INTERNAL_API_SECRET` — ต้องตรงกับ `INTERNAL_API_SECRET` ใน `backend/.env` เป๊ะๆ (สร้างด้วย
  `openssl rand -hex 32`) ใช้ยืนยันว่าคำขอมาจาก frontend server ของเราจริง ไม่ใช่ browser ยิงตรง

## Dev server

```bash
npm run dev
```
