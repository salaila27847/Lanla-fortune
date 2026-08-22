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
    voice: str | None    # คำพูดของ finding ในมุมมองบุคคลที่หนึ่ง ("ฉันคือ...") — ปัจจุบันมาจาก
                          # voice_th ในไพ่ออราเคิลเท่านั้น (uranian/tarot ยังไม่มีข้อมูลนี้ จึงเป็น
                          # None) Master Interpreter ใช้เป็นแรงบันดาลใจโทนเสียง ไม่ใช่คัดลอกทั้งประโยค
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

## Draw-before-reveal (`POST /api/oracle/draw`, `POST /api/tarot/draw`)

**แก้ไข 2026-08-16**: ผู้ใช้ตัดสินใจให้การจั่วไพ่เป็นการเลือกจริงของผู้ใช้ ไม่ใช่แค่ animation
cosmetic ที่สุ่มไพ่หลังบ้านทีหลังโดยไม่สนตำแหน่งที่แตะ — client ต้องเรียก endpoint นี้ก่อนแสดงตาราง
ไพ่ (`CardDrawStep`) เพื่อรับ**สำรับทั้งชุดที่สับแล้ว**พร้อมเนื้อหาไพ่จริงทุกใบ ตำแหน่งที่ผู้ใช้แตะจึง
แม็ปกับไพ่จริงที่ตัดสินไว้ล่วงหน้าแล้ว ไม่ใช่ไพ่ที่กำหนดทีหลัง — สำหรับทาโรต์ orientation
(กลับหัว/ตั้งตรง) ก็ตัดสินไว้พร้อมกับการสับด้วยเหตุผลเดียวกัน

```python
class OracleDrawRequest(BaseModel):
    deck: str | None = None      # ไม่ระบุ = ใช้ deck default (lanla_original)

class OracleCardPreview(BaseModel):
    card_id: str
    name_th: str
    category_th: str
    meaning: str
    keywords: list[str]

class OracleDeckResponse(BaseModel):
    cards: list[OracleCardPreview]   # สำรับทั้ง 88 ใบ สับแล้ว

class TarotDrawRequest(BaseModel):
    spread: str = "three_card"

class TarotCardPreview(BaseModel):
    card_id: str
    name_th: str
    reversed: bool                    # ตัดสินไว้ตอนสับแล้ว ไม่ใช่ตอนตีความ
    meaning: str
    keywords: list[str]

class TarotDeckResponse(BaseModel):
    positions: list[str]              # label ตามเลย์เอาท์ที่เลือก เช่น ["อดีต","ปัจจุบัน","อนาคต"]
    cards: list[TarotCardPreview]     # สำรับทั้ง 78 ใบ สับแล้ว
```

ผู้ใช้เลือก "trust client" สำหรับขั้นถัดไป (ส่งไพ่ที่จั่วไปกลับให้ `/api/reading`) — **ไม่มี**
token/session ฝั่ง server คอยกันการปลอมแปลงว่าจั่วอะไรมาจริง (เหตุผล: ไม่มีคู่แข่ง/เดิมพันในระบบนี้
ผู้ใช้ปลอมไพ่ของตัวเองก็แค่หลอกตัวเอง) **แต่**เนื้อหา (meaning/keywords) ยังคง authoritative จาก
knowledge base เสมอ — client ส่งกลับแค่ `card_id` (+ `reversed` สำหรับทาโรต์) ในลำดับที่แตะ
backend จะ lookup ความหมายจริงเองทุกครั้ง ไม่เคยเชื่อ meaning ที่ client ส่งมา (ดู
`build_result_from_picks()` ใน `app/modules/{oracle,tarot}/engine.py`)

```python
class TarotPick(BaseModel):
    card_id: str
    reversed: bool
```

`CardDraw` (ของเดิม) ถูกลบออกแล้ว — ไม่เคยถูกใช้งานจริงอยู่ก่อนแล้ว และตอนนี้แทนที่ด้วย `TarotPick`
(สำหรับ tarot) กับ `picks: list[str]` (สำหรับ oracle) ที่ผูกกับ flow ใหม่นี้โดยตรง

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

class HousePlacementResult(BaseModel):
    factor: str            # เช่น "MARS" (ไม่มี prefix r:/d:/t: — บริบทมาจากว่าอยู่ใน field ไหน)
    house_number: int      # 1-12, ระบบเรือนเมริเดียน (uranian.engine.HOUSE_SYSTEM_MERIDIAN)
    label: str             # เช่น "อังคาร (directed) อยู่เรือนที่ 5"

class SolarArcResult(BaseModel):
    arc_degrees: float
    pictures: list[PictureResult]
    house_placements: list[HousePlacementResult]  # ตำแหน่ง directed ของ 18 ปัจจัย (10 ดาวเคราะห์
        # คลาสสิก + 8 ดาวเสริม) เทียบกับเรือน "เกิด" (radix) เดิม — ว่างถ้าไม่ทราบเวลาเกิด

class TransitResult(BaseModel):
    pictures: list[PictureResult]   # รวม Daily M/A (t:A, t:M) และ Transit Axes ถ้ามีเงื่อนไขครบ
    house_placements: list[HousePlacementResult]  # ตำแหน่ง transit จริงของ 18 ปัจจัย เทียบกับเรือน
        # "เกิด" (radix) เดิม (หลักการเดียวกับ solar_arc — เรือนเกิดเป็น "เวที" คงที่ ไม่คำนวณเรือนใหม่
        # ทุกครั้งที่ดาวเคลื่อนที่) — ว่างถ้าไม่ทราบเวลาเกิด

class LunarReturnResult(BaseModel):
    return_at: datetime

class RelocationResult(BaseModel):
    ascendant: float
    midheaven: float
    house_placements: list[HousePlacementResult]  # ตำแหน่งดาว radix เดิม (ไม่เปลี่ยน) เทียบกับเรือน
        # *ใหม่* ที่คำนวณจากพิกัดปลายทาง — ต่างจาก solar_arc/transit ตรงที่ relocation คำนวณเรือนใหม่
        # จริงๆ เพราะเป้าหมายคือ "เรือนที่สถานที่ใหม่หมายถึงอะไร" ไม่ใช่ "ดาวที่เคลื่อนที่ตกเรือนเดิมไหน"

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

**แก้ไข 2026-08-16**: `tarot.picks`/`oracle.picks` แทนที่ `card_count`/`spread`-only เดิม — client
ต้องจั่วไพ่จริงก่อนผ่าน `POST /api/oracle|tarot/draw` (ดูหัวข้อ "Draw-before-reveal" ด้านบน) แล้วส่ง
ไพ่ที่แตะเปิดจริงกลับมาที่นี่ตามลำดับที่แตะ backend ไม่ได้สุ่มไพ่เองในขั้นตอนนี้อีกต่อไป แค่ lookup
ความหมายจากไพ่ที่ client ระบุ id มา (`build_result_from_picks()`)

```python
class TarotPick(BaseModel):
    card_id: str
    reversed: bool

class TarotRequest(BaseModel):
    spread: str = "three_card"   # id จาก backend/app/knowledge_base/tarot/spreads.yaml
    picks: list[TarotPick]       # ต้องมีจำนวนเท่ากับ positions ของ spread นี้ (validate ที่ endpoint)

class OracleRequest(BaseModel):
    picks: list[str]             # card id ตามลำดับที่แตะ — ge=3, le=9 (สุ่มจำนวนจากระบบเสมอ ไม่ใช่ผู้ใช้เลือก)
    question: str | None = None  # บังคับก็ต่อเมื่อ oracle เป็นศาสตร์เดียวที่เลือก (ไม่มี birth_data/tarot)
    deck: str | None = None

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

## FollowUpRequest (body ของ `POST /api/reading/follow-up`) — แก้ไข 2026-08-14, 2026-08-16

Flow "ถามเพิ่ม" ที่หน้าแสดงผล: ผู้ใช้พิมพ์คำถามต่อ จั่วไพ่ออราเคิลชุดใหม่จริง (ผ่าน
`POST /api/oracle/draw` เหมือน reading รอบแรก — ดูหัวข้อ "Draw-before-reveal") แล้วสังเคราะห์
ต่อเนื่องจากคำทำนายเดิม โดยให้น้ำหนักกับไพ่ชุดใหม่เป็นหลัก — client ส่ง `SynthesisOutput` ที่ตัวเอง
มีอยู่แล้วกลับมาตรงๆ (ข้อมูลในเซสชันนี้ ไม่ใช่ดึงจาก `/history` — ยังคงกฎ "ห้ามใช้ประวัติผู้ใช้"
ในข้อ 1)

```python
class FollowUpRequest(BaseModel):
    previous: SynthesisOutput    # ผลลัพธ์ล่าสุดที่ client มีอยู่แล้วในเซสชันนี้
    question: str                # min_length=1
    oracle_picks: list[str]      # card id ตามลำดับที่แตะ — ge=3, le=9 (สุ่มจำนวนจากระบบเสมอ)
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
    # แก้ไข 2026-08-22 — ความจำ birth data (ดูหัวข้อ "ความจำ birth data" ด้านล่าง):
    birth_date: date | None
    birth_time: time | None
    birth_place: str | None
    birth_latitude: float | None
    birth_longitude: float | None
    birth_timezone: str | None

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

## ความจำ birth data (`GET`/`DELETE /api/profile/birth-data`) — แก้ไข 2026-08-22

ผู้ใช้ขอให้ระบบจดจำ birth data ของแต่ละคน (วันเกิด/เวลาเกิด/สถานที่เกิด/เขตเวลา) เพราะทุกคนต้อง
ล็อกอินก่อนใช้งานอยู่แล้ว — ไม่ต้องให้พิมพ์ซ้ำทุกครั้ง **ไม่ขัดกับกฎ "ห้ามใช้ประวัติผู้ใช้" ใน CLAUDE.md
ข้อ 1**: กฎนั้นห้าม *เนื้อหาคำทำนายเก่า* ย้อนกลับไปปรุงแต่งคำทำนายใหม่ (เช่น ให้ Gemini เห็นว่าเคย
ทำนายอะไรไว้) ไม่ใช่การจดจำข้อเท็จจริงที่ไม่เปลี่ยนแปลง (วันเกิด) ที่ผู้ใช้พิมพ์เองซ้ำทุกครั้งอยู่แล้ว —
ข้อมูลนี้แค่ช่วยเติมฟอร์มให้ ผู้ใช้ยังเห็น/แก้ไข/ยืนยันก่อนกดส่งทุกครั้งเหมือนเดิม ไม่มีอะไรถูกส่งเข้า
Gemini โดยที่ผู้ใช้ไม่เห็น

- `POST /api/reading` ที่มี `birth_data` จะบันทึกทับ `User.birth_*` เดิมเสมอ (semantics "ใช้ล่าสุด" —
  ไม่มี checkbox แยกให้เลือก "จดจำไหม" ตามธรรมเนียมเดียวกับที่ reading history เองก็บันทึกอัตโนมัติ
  ไม่มี opt-in ตั้งแต่ Phase 9) — reading ที่ไม่มี birth_data (oracle-only, follow-up) ไม่แตะค่าที่
  จดจำไว้เลย
- `GET /api/profile/birth-data` → `BirthData | None` — ให้ frontend ดึงมาเติมฟอร์ม `/reading`
  ล่วงหน้า (`BirthDataForm.tsx`) คืน `None` ถ้าไม่เคยส่ง birth_data มาก่อน หรือเคยลบไปแล้ว
- `DELETE /api/profile/birth-data` → 204 — ล้างค่าที่จดจำไว้ (ไม่กระทบ reading history เดิมที่
  `/history` เลย เพราะเก็บคนละที่ — `Reading.birth_data` เป็น snapshot ต่อครั้ง)
- **Migration**: `Base.metadata.create_all()` สร้างเฉพาะตารางที่ยังไม่มี ไม่ alter ตารางเดิม — เพราะ
  `users` มีอยู่แล้วใน production (มี user จริง) ตั้งแต่ก่อนเพิ่มคอลัมน์ `birth_*` จึงต้องมี
  `ensure_user_birth_data_columns()` (`backend/app/db/session.py`) รันต่อจาก `create_all()` ทุกครั้ง
  ที่ startup เพื่อ backfill คอลัมน์ที่ขาดด้วย `ALTER TABLE ... ADD COLUMN` (portable ทั้ง
  SQLite/Postgres, idempotent — ทดสอบแล้วว่าไม่ลบข้อมูลแถวเดิม)

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
