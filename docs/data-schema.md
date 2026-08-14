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

**แก้ไข 2026-08-14**: `ReadingRequest` ไม่บังคับ `birth_data` อีกต่อไป — ผู้ใช้กดข้ามได้ทีละศาสตร์
(ปุ่มข้ามที่หน้า `/reading`) ตอนนี้ `birth_data`/`tarot`/`oracle` เป็น optional อิสระต่อกันทั้ง 3
ตัว การมี/ไม่มีแต่ละ field คือสิ่งที่บอก backend ว่าจะรันเอนจินไหนบ้าง — ต้องมีอย่างน้อย 1 ใน 3
เสมอ (validate ด้วย `model_validator`) `ForecastRequest` (ของ `/api/forecast` เดี่ยวๆ) ยังคงบังคับ
`birth_data` เหมือนเดิมเพราะเป็น Uranian-only endpoint

```python
class TarotRequest(BaseModel):
    spread: str = "three_card"   # id จาก backend/app/knowledge_base/tarot/spreads.yaml

class OracleRequest(BaseModel):
    card_count: int              # ge=3, le=9 — สุ่มจากระบบเสมอ (ไม่ใช่ผู้ใช้เลือก)
    question: str | None = None  # บังคับก็ต่อเมื่อ oracle เป็นศาสตร์เดียวที่เลือก (ไม่มี birth_data/tarot)

class ReadingRequest(BaseModel):
    birth_data: BirthData | None = None
    tarot: TarotRequest | None = None
    oracle: OracleRequest | None = None
    solar_arc: SolarArcRequest | None = None
    transit: TransitRequest | None = None
    lunar_return: LunarReturnRequest | None = None
    relocation: RelocationRequest | None = None
    # model_validator บังคับ: (1) มีอย่างน้อย 1 ใน birth_data/tarot/oracle
    # (2) forecast sub-request ต้องมาคู่กับ birth_data เสมอ
    # (3) oracle-only (ไม่มี birth_data และ tarot) ต้องมี oracle.question

class ForecastRequest(BaseModel):
    birth_data: BirthData
    solar_arc: SolarArcRequest | None = None
    transit: TransitRequest | None = None
    lunar_return: LunarReturnRequest | None = None
    relocation: RelocationRequest | None = None
```

## FollowUpRequest (body ของ `POST /api/reading/follow-up`) — แก้ไข 2026-08-14

Flow "ถามเพิ่ม" ที่หน้าแสดงผล: ผู้ใช้พิมพ์คำถามต่อ ระบบสุ่มไพ่ออราเคิลชุดใหม่ 3-9 ใบให้เปิด แล้ว
สังเคราะห์ต่อเนื่องจากคำทำนายเดิม โดยให้น้ำหนักกับไพ่ชุดใหม่เป็นหลัก — client ส่ง `SynthesisOutput`
ที่ตัวเองมีอยู่แล้วกลับมาตรงๆ (ข้อมูลในเซสชันนี้ ไม่ใช่ดึงจาก `/history` — ยังคงกฎ "ห้ามใช้ประวัติ
ผู้ใช้" ในข้อ 1)

```python
class FollowUpRequest(BaseModel):
    previous: SynthesisOutput    # ผลลัพธ์ล่าสุดที่ client มีอยู่แล้วในเซสชันนี้
    question: str                # min_length=1
    oracle_count: int            # ge=3, le=9 — สุ่มจากระบบเสมอ
```

## SynthesisOutput (output สุดท้ายจาก Master Interpreter)

```python
class SynthesisOutput(BaseModel):
    final_reading: str                  # คำทำนายฉบับสมบูรณ์ — ถ้ามี forecast จะทอเนื้อหาเข้าไปด้วย
    convergent_themes: list[str]        # จุดที่แต่ละศาสตร์ที่เลือกใช้เห็นตรงกัน (ว่างได้ถ้าใช้ศาสตร์เดียว)
    divergent_notes: list[str]          # จุดที่ขัดแย้งกัน พร้อมคำอธิบาย
    per_engine_breakdown: dict[str, EngineResult]  # เฉพาะศาสตร์ที่ผู้ใช้เลือกใช้จริง (1-3 key)
    forecast: ForecastResponse | None = None  # ผลดิบของ forecast ที่เลือก (ถ้ามี) — เก็บไว้ให้
                                               # frontend แสดงตารางต่อ แม้จะสังเคราะห์เข้า
                                               # final_reading ไปแล้วก็ตาม
    oracle_question: str | None = None  # คำถามที่ขับเคลื่อนการอ่านไพ่ออราเคิลรอบนี้ (ตอนเลือก
                                         # oracle ศาสตร์เดียว หรือจาก /api/reading/follow-up)
```

**หมายเหตุ (แก้ไข 2026-08-13)**: เดิม (Phase 12) ตั้งใจให้ forecast เป็นตารางดิบล้วนๆ ไม่ผ่าน
Gemini synthesis — ผู้ใช้กลับคำตัดสินใจนี้ใน Phase 13 ให้ `synthesize()` รับ `forecast` เป็น
argument ที่ 4 (optional) แล้วนำไปพิจารณาร่วมกับ 3 engine หลักด้วย ดู `master_interpreter.py`
`SYSTEM_PROMPT` ข้อ 4

**หมายเหตุ (แก้ไข 2026-08-14)**: `synthesize()` รับ `uranian`/`tarot`/`oracle` เป็น `EngineResult |
None` ทั้ง 3 ตัวแล้ว (เดิมบังคับทั้ง 3) — เฉพาะตัวที่ไม่ใช่ `None` เท่านั้นที่เข้า payload ที่ส่งให้
Gemini และปรากฏใน `per_engine_breakdown` ผลลัพธ์ ถ้าเหลือศาสตร์เดียวหลังข้าม `SYSTEM_PROMPT` จะสั่ง
ให้ตีความเจาะลึกศาสตร์นั้นแทนขั้นตอน convergence/divergence ปกติ — ดู `master_interpreter.py` ข้อ 3

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
    id: int                       # primary key
    user_id: int                  # FK -> users.id
    birth_data: dict | None       # BirthData.model_dump(mode="json") — None ถ้าข้ามยูเรเนียน
                                   # (oracle-only, tarot+oracle, หรือมาจาก /api/reading/follow-up
                                   # ซึ่งไม่มี birth data เลย) — แก้ไข 2026-08-14
    synthesis_output: dict         # SynthesisOutput.model_dump(mode="json") ทั้งก้อน
    created_at: datetime
```

## ReadingRecord (response ของ `GET /api/readings` — Pydantic)

```python
class ReadingRecord(BaseModel):
    id: int
    created_at: datetime
    birth_data: BirthData | None = None  # แก้ไข 2026-08-14 — ดูหมายเหตุที่ Reading ด้านบน
    synthesis: SynthesisOutput
```

## หมายเหตุสำคัญ

- **ไพ่ทาโรต์ (แก้ไข 2026-08-12)**: ตรวจสอบทุก repo ในบัญชี GitHub ที่ใช้งานแล้ว ไม่พบไฟล์อ้างอิงจากโปรเจกต์
  Destiny Matrix ตามที่ระบุไว้เดิม ผู้ใช้ยืนยันให้เขียนความหมายทั้ง 78 ใบขึ้นใหม่ทั้งหมดโดยอิงฐานความหมาย
  สากล (Rider-Waite-Smith) แทน — ดู `backend/app/knowledge_base/tarot/README.md`
- **เลย์เอาท์ไพ่ทาโรต์ (แก้ไข 2026-08-14)**: `spreads.yaml` มี 5 แบบให้ผู้ใช้เลือกที่หน้า `/reading`
  แล้ว (เดิมมีแค่ single_card/three_card) — เพิ่ม situation_advice (3 ใบ), relationship_five
  (5 ใบ), celtic_cross (10 ใบ) ตาม PRD ข้อ 4.2 ที่ระบุไว้ตั้งแต่แรกว่าต้องรองรับหลาย spread
  frontend เก็บ id/ตำแหน่ง/จำนวนใบชุดเดียวกันไว้ที่ `frontend/src/lib/tarotSpreads.ts` (ต้อง sync
  มือกับ YAML นี้เพราะ backend ตัดไพ่ตามลำดับ position ที่ zip กับ card ที่สุ่มได้)
- Knowledge base ทุกไฟล์เก็บเป็น YAML ใน `backend/app/knowledge_base/{uranian,tarot,oracle}/` แยกโฟลเดอร์ตามศาสตร์
