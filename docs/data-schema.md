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

## Forecast (Solar Arc / Transit / Lunar Return / Relocation — ไม่บังคับ, ต่อกับ Uranian engine)

4 เทคนิคเสริมจาก `backend/app/modules/uranian/{solar_arc,transit}.py` แต่ละตัวเลือกเปิดแยกกันได้
(checkbox ที่ฟอร์ม `/reading`) — ทั้ง `POST /api/reading` และ `POST /api/forecast` รับ sub-request
ชุดเดียวกันนี้ (ดูหัวข้อถัดไป)

```python
class SolarArcRequest(BaseModel):
    target_date: date

class TransitRequest(BaseModel):
    target_date: date

class LunarReturnRequest(BaseModel):
    search_start: date

class RelocationRequest(BaseModel):
    place: str
    latitude: float
    longitude: float

class PictureResult(BaseModel):
    type: Literal["type1", "type2"]
    label: str            # เช่น "r:SUN / d:VENUS = t:JUPITER"
    factors: list[str]
    orb: float

class SolarArcResult(BaseModel):
    arc_degrees: float
    pictures: list[PictureResult]

class TransitResult(BaseModel):
    pictures: list[PictureResult]   # รวม Daily M/A (t:A, t:M) และ Transit Axes ถ้ามีเงื่อนไขครบ

class LunarReturnResult(BaseModel):
    return_at: datetime

class RelocationResult(BaseModel):
    ascendant: float
    midheaven: float

class ForecastResponse(BaseModel):
    solar_arc: SolarArcResult | None = None
    transit: TransitResult | None = None
    lunar_return: LunarReturnResult | None = None
    relocation: RelocationResult | None = None
```

## ReadingRequest (body ของ `POST /api/reading`) / ForecastRequest (body ของ `POST /api/forecast`)

รูปร่างเดียวกันทุกประการ — `birth_data` บังคับ ส่วน forecast sub-request ทั้ง 4 ไม่บังคับและเลือก
ได้อิสระต่อกัน (ไม่เลือกเลยก็ได้) `/api/reading` คำนวณ forecast ที่เลือกแล้วส่งเข้า `synthesize()`
ด้วย (ดูหัวข้อถัดไป) ส่วน `/api/forecast` คืนแค่ตารางดิบ ไม่สังเคราะห์ ไม่บันทึกประวัติ — ใช้เมื่อ
อยากได้ผลลัพธ์แบบตารางอย่างเดียวโดยไม่ต้องจั่วไพ่/เรียก Gemini

```python
class ReadingRequest(BaseModel):
    birth_data: BirthData
    solar_arc: SolarArcRequest | None = None
    transit: TransitRequest | None = None
    lunar_return: LunarReturnRequest | None = None
    relocation: RelocationRequest | None = None

class ForecastRequest(BaseModel):
    birth_data: BirthData
    solar_arc: SolarArcRequest | None = None
    transit: TransitRequest | None = None
    lunar_return: LunarReturnRequest | None = None
    relocation: RelocationRequest | None = None
```

## SynthesisOutput (output สุดท้ายจาก Master Interpreter)

```python
class SynthesisOutput(BaseModel):
    final_reading: str                  # คำทำนายฉบับสมบูรณ์ — ถ้ามี forecast จะทอเนื้อหาเข้าไปด้วย
    convergent_themes: list[str]        # จุดที่ 3 ศาสตร์เห็นตรงกัน
    divergent_notes: list[str]          # จุดที่ขัดแย้งกัน พร้อมคำอธิบาย
    per_engine_breakdown: dict[str, EngineResult]  # ผลดิบของแต่ละศาสตร์ ให้ผู้ใช้ตรวจสอบที่มาได้
    forecast: ForecastResponse | None = None  # ผลดิบของ forecast ที่เลือก (ถ้ามี) — เก็บไว้ให้
                                               # frontend แสดงตารางต่อ แม้จะสังเคราะห์เข้า
                                               # final_reading ไปแล้วก็ตาม
```

**หมายเหตุ (แก้ไข 2026-08-13)**: เดิม (Phase 12) ตั้งใจให้ forecast เป็นตารางดิบล้วนๆ ไม่ผ่าน
Gemini synthesis — ผู้ใช้กลับคำตัดสินใจนี้ใน Phase 13 ให้ `synthesize()` รับ `forecast` เป็น
argument ที่ 4 (optional) แล้วนำไปพิจารณาร่วมกับ 3 engine หลักด้วย ดู `master_interpreter.py`
`SYSTEM_PROMPT` ข้อ 4

## User / Reading (persistence — Postgres/Neon prod, SQLite dev, ดู `backend/app/db/models.py`)

ตารางเหล่านี้เป็น SQLAlchemy model ไม่ใช่ Pydantic — ใช้เก็บประวัติคำทำนายผูกกับ user ที่ล็อกอิน
ด้วย Google เท่านั้น ไม่เคยถูกส่งเข้า prompt ของ Gemini (ดูกฎ "ห้ามใช้ประวัติผู้ใช้" ใน CLAUDE.md ข้อ 1)
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
