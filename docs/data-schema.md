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

## User / Reading (persistence — Postgres/Neon prod, SQLite dev, ดู `backend/app/db/models.py`)

ตารางเหล่านี้เป็น SQLAlchemy model ไม่ใช่ Pydantic — ใช้เก็บประวัติคำทำนายผูกกับ user ที่ล็อกอิน
ด้วย Google เท่านั้น ไม่เคยถูกส่งเข้า prompt ของ Claude (ดูกฎ "ห้ามใช้ประวัติผู้ใช้" ใน CLAUDE.md ข้อ 1)
— เป็นแค่ที่เก็บสำหรับให้ผู้ใช้ย้อนดูของตัวเองที่หน้า `/history`

```python
class User(Base):
    id: int                  # primary key
    google_sub: str          # unique — Google account id ที่เสถียร (จาก session.user.id)
    email: str
    name: str | None
    created_at: datetime

class Reading(Base):
    id: int                  # primary key
    user_id: int             # FK -> users.id
    birth_data: dict          # BirthData.model_dump(mode="json") ทั้งก้อน
    synthesis_output: dict    # SynthesisOutput.model_dump(mode="json") ทั้งก้อน
    created_at: datetime
```

## ReadingRecord (response ของ `GET /api/readings` — Pydantic)

```python
class ReadingRecord(BaseModel):
    id: int
    created_at: datetime
    birth_data: BirthData
    synthesis: SynthesisOutput
```

## หมายเหตุสำคัญ

- **ไพ่ทาโรต์ (แก้ไข 2026-08-12)**: ตรวจสอบทุก repo ในบัญชี GitHub ที่ใช้งานแล้ว ไม่พบไฟล์อ้างอิงจากโปรเจกต์
  Destiny Matrix ตามที่ระบุไว้เดิม ผู้ใช้ยืนยันให้เขียนความหมายทั้ง 78 ใบขึ้นใหม่ทั้งหมดโดยอิงฐานความหมาย
  สากล (Rider-Waite-Smith) แทน — ดู `backend/app/knowledge_base/tarot/README.md`
- Knowledge base ทุกไฟล์เก็บเป็น YAML ใน `backend/app/knowledge_base/{uranian,tarot,oracle}/` แยกโฟลเดอร์ตามศาสตร์
