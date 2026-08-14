# Tarot knowledge base

ตรวจสอบแล้ว (2026-08-12): ไม่พบไฟล์อ้างอิงความหมายไพ่ทาโรต์ภาษาไทยจากโปรเจกต์ Destiny Matrix
ในบัญชี GitHub ที่ใช้งานอยู่ (`salaila27847`) — ตรวจครบทุก repo ที่มีอยู่ในบัญชีแล้วไม่พบ
ผู้ใช้ยืนยันให้เขียนความหมายทั้งสำรับขึ้นใหม่ทั้งหมด โดยอิงฐานความหมายที่เป็นสากล
(ธรรมเนียม Rider-Waite-Smith) แปลและเรียบเรียงเป็นภาษาไทยเอง — รวมทั้งใบตั้งตรงและกลับหัว

## โครงสร้าง

```
major_arcana.yaml   ← 22 ใบ (0-21) — id, number, name_th, name_en,
                       keywords_upright, keywords_reversed,
                       meaning_upright, meaning_reversed
minor_arcana.yaml   ← 56 ใบ (4 ชุด x 14 อันดับ: ไม้เท้า/ถ้วย/ดาบ/เหรียญ,
                       เอซ-10, เพจ, อัศวิน, ควีน, คิง) — schema เดียวกับ major
                       เพิ่ม suit, suit_th, rank
spreads.yaml        ← นิยามหน้าไพ่ 5 แบบให้ผู้ใช้เลือกที่หน้า /reading (แก้ไข 2026-08-14):
                       single_card (1 ใบ), three_card (อดีต-ปัจจุบัน-อนาคต —
                       ใช้เป็น default ของ engine), situation_advice
                       (สถานการณ์-อุปสรรค-คำแนะนำ, 3 ใบ), relationship_five
                       (ความสัมพันธ์ 5 ใบ), celtic_cross (กากบาทเซลติก, 10 ใบ)
```

`app/modules/tarot/engine.py` โหลดทั้งสำรับ (78 ใบ) สุ่มจั่วตามจำนวนตำแหน่งใน spread ที่เลือก
สุ่มว่าใบไหนตั้งตรง/กลับหัว แล้วเลือกความหมายให้ตรงกับทิศทางที่จั่วได้ ไม่มี hardcode เนื้อหาการ์ดในโค้ด
