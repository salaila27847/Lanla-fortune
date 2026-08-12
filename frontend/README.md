# Frontend — Fortune App

Next.js 14+ (App Router), TypeScript, TailwindCSS. Scaffolded with:

```bash
npx create-next-app@latest . --typescript --tailwind --app --eslint --src-dir --import-alias "@/*"
npm install framer-motion   # สำหรับ animation จั่วไพ่ / 90° dial
```

## หน้าที่ต้องมี (ดู docs/PRD.md ส่วน user flow)

- `src/app/birth-data/page.tsx` — ฟอร์มกรอกข้อมูลเกิด + เลือกคำถาม
- `src/app/tarot-draw/page.tsx` — จั่วไพ่ทาโรต์แบบ interactive
- `src/app/oracle-draw/page.tsx` — จั่วไพ่ออราเคิล
- `src/app/reading/page.tsx` — แสดงคำทำนายฉบับสมบูรณ์ + tab แยกศาสตร์
- `src/lib/api.ts` — client เรียก `POST /api/reading` ของ backend (ดู backend/app/main.py)

ในช่วงที่ backend engine ยังเป็น mock (Phase 1-2) หน้าเหล่านี้พัฒนาคู่ขนานได้เลย เพราะ endpoint
`/api/reading` คืนค่าตาม schema จริงอยู่แล้ว แค่เนื้อหาข้างในเป็น mock data

## Dev server

```bash
npm run dev
```
