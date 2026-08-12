# Data schema

Schema เหล่านี้เป็น "สัญญา" (contract) ที่ทั้ง 3 engine ต้อง implement ให้ตรงกัน เพื่อให้ Master Interpreter เรียกใช้แบบเดียวกันได้ ใช้ Pydantic model ใน backend และ TypeScript type ที่ frontend ตรงกัน

## EngineResult (interface กลางที่ทั้ง 3 engine ต้อง return)

```python
class EngineResult(BaseModel):
    engine: Literal["uranian", "tarot", "oracle"]
    summary: str                     # สรุปสั้น 1-2 ประโยค
    themes: list[str]                # ธีมหลักที่พบ เช่น ["การงาน", "การเปลี่ยนแปลง"]
    raw_findings: list[Finding]      # รายละเอียดดิบของแต่ละองค์ประกอบ
    confidence: float                # 0-1 ความชัดเจนของสัญญาณจากศาสตร์นี้

class Finding(BaseModel):
    label: str          # เช่น "Cupido/Ascendant = 45°" หรือ "The Tower (reversed)"
    meaning: str         # ความหมายจากฐานข้อมูล
    weight: float         # น้ำหนักความสำคัญ 0-1
```

## BirthData (input สำหรับ Uranian Engine)

```python
class BirthData(BaseModel):
    date: date
    time: time | None        # ถ้าไม่ทราบเวลาเกิด ให้ระบบแจ้งข้อจำกัดความแม่นยำ
    place: str
    latitude: float
    longitude: float
    timezone: str
```

## TarotDraw / OracleDraw

```python
class CardDraw(BaseModel):
    deck: str                # ชื่อชุดไพ่
    card_id: str
    position_in_spread: str | None   # เช่น "past", "present", "future"
    reversed: bool
```

## SynthesisOutput (output สุดท้ายจาก Master Interpreter)

```python
class SynthesisOutput(BaseModel):
    final_reading: str                  # คำทำนายฉบับสมบูรณ์
    convergent_themes: list[str]        # จุดที่ 3 ศาสตร์เห็นตรงกัน
    divergent_notes: list[str]          # จุดที่ขัดแย้งกัน พร้อมคำอธิบาย
    per_engine_breakdown: dict[str, EngineResult]  # ผลดิบของแต่ละศาสตร์ ให้ผู้ใช้ตรวจสอบที่มาได้
```

## หมายเหตุสำคัญ

- **ตรวจสอบก่อนสร้างฐานความหมายไพ่ทาโรต์ใหม่**: มีไฟล์อ้างอิงภาษาไทยเรื่องความหมาย 22 เลข (Major Arcana correspondences) จากโปรเจกต์ Destiny Matrix ที่ทำไว้ก่อนหน้านี้แล้ว — ให้ตรวจสอบและนำมาใช้ซ้ำ (reuse) แทนการเขียนใหม่ทั้งหมด เพื่อความสอดคล้องของความหมายไพ่ระหว่างโปรเจกต์
- Knowledge base ทุกไฟล์เก็บเป็น YAML ใน `backend/app/knowledge_base/{uranian,tarot,oracle}/` แยกโฟลเดอร์ตามศาสตร์
