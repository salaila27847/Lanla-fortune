# Frontend — ยังไม่ scaffold

ตั้งใจปล่อยว่างไว้ให้ Claude Code รัน scaffold tool โดยตรงในเครื่องจริง (มี network access เต็มที่)
แทนที่จะสร้างไฟล์ Next.js ปลอมไว้ล่วงหน้า

## คำสั่งที่ Claude Code ควรรัน (Phase 0)

```bash
cd frontend
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
