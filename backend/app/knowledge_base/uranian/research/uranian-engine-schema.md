# ออกแบบ Database Schema และ Engine — โมดูลยูเรเนียน (Lanla-fortune)

> อ้างอิงจาก 5 เอกสารวิจัยที่ทำไว้ก่อนหน้า (Glossary, ตรรกะการคำนวณ, Delineation, พื้นฐาน, Solar Arc/Transit)
> เอกสารนี้คือ schema + pseudocode พร้อมใช้พัฒนาต่อเป็นโค้ดจริง

---

## 1. ภาพรวมสถาปัตยกรรม

```
[Ephemeris Engine] → [Position Calculator] → [Midpoint/Picture Matcher]
                                                        ↓
                                          [Interpretation Database]
                                                        ↓
                                          [Synthesis Layer (Claude API)]
                                                        ↓
                                                  [คำทำนายสุดท้าย]
```

แบ่งฐานข้อมูลเป็น 2 กลุ่ม:
- **Reference tables** (ข้อมูลตายตัว ไม่เปลี่ยนตามผู้ใช้) — มาจาก 5 เอกสารวิจัย
- **User/chart tables** (ข้อมูลเฉพาะดวงชะตาของผู้ใช้แต่ละคน)

---

## 2. Reference Tables (ฐานความรู้ยูเรเนียน)

### 2.1 `factors` — 22 ปัจจัยหลัก (6 personal points + 16 planets)

```sql
CREATE TABLE factors (
    factor_id       VARCHAR(20) PRIMARY KEY,   -- 'M', 'A', 'SUN', 'MOON', 'NODE', 'ARIES',
                                                 -- 'MERCURY', 'VENUS', ... 'CUPIDO', 'HADES', ...
    factor_type     ENUM('personal_point', 'planet', 'transneptunian') NOT NULL,
    name_th         VARCHAR(50) NOT NULL,       -- ชื่อภาษาไทย
    name_en         VARCHAR(50) NOT NULL,
    symbol          VARCHAR(10),                -- unicode/glyph สำหรับ UI
    principle_th    TEXT,                       -- จากเอกสาร Phase 4 (บทที่ II)
    function_th     TEXT,
    expression_th   TEXT,
    manifestation_th TEXT,
    sort_order      INT                         -- ลำดับมาตรฐานสำหรับ UI (M, A, Sun, Moon, Node, Aries, ...)
);
```

### 2.2 `planetary_pictures` — ฐานข้อมูลคู่/ชุดดาว (จากเอกสาร Phase 1)

```sql
CREATE TABLE planetary_pictures (
    picture_id      SERIAL PRIMARY KEY,
    picture_type    ENUM('type1', 'type2') NOT NULL,  -- Type I = A=B/C, Type II = A+B=C+D
    factor_a        VARCHAR(20) REFERENCES factors(factor_id),
    factor_b        VARCHAR(20) REFERENCES factors(factor_id),
    factor_c        VARCHAR(20) REFERENCES factors(factor_id),   -- NULL ถ้าเป็นรูปแบบเปิด (sensitive point)
    factor_d        VARCHAR(20) REFERENCES factors(factor_id),   -- ใช้เฉพาะ type2
    meaning_th      TEXT NOT NULL,              -- ถอดความจาก Glossary / Delineation
    axis_context    VARCHAR(20),                -- 'M','A','SUN','MOON','NODE', หรือ NULL = ทั่วไป
    source_ref      VARCHAR(100),               -- อ้างอิงแหล่งที่มา (เช่น "Jacobson, Glossary p.179")
    confidence      ENUM('core','extended') DEFAULT 'core'  -- core = จากคัดสรรของ Jacobson,
                                                              -- extended = เพิ่มจากแหล่งอื่นภายหลัง
);

-- Index สำคัญสำหรับ matching เร็ว: ค้นหาคู่ดาวแบบไม่สนลำดับ (A+B เท่ากับ B+A)
CREATE INDEX idx_pic_pair ON planetary_pictures (
    LEAST(factor_a, factor_b), GREATEST(factor_a, factor_b)
);
```

### 2.3 `axis_meanings` — ความหมายคู่ดาวแยกตามแกน M/A/Sun/Moon/Node (จากเอกสาร Phase 3)

```sql
CREATE TABLE axis_meanings (
    id              SERIAL PRIMARY KEY,
    axis_factor     VARCHAR(20) REFERENCES factors(factor_id),  -- 'M','A','SUN','MOON','NODE'
    paired_factor   VARCHAR(20) REFERENCES factors(factor_id),
    meaning_th      TEXT NOT NULL,
    meaning_layer   VARCHAR(30) DEFAULT 'general'
        -- สำหรับ Moon โดยเฉพาะ: 'woman','people','emotion','thought','hour','month'
        -- (ตามหลักการ "many faces of the Moon" ในเอกสาร Phase 3)
);
```

### 2.4 `house_meanings` — ความหมายดาวในเรือน (ทั่วไป, จากเอกสาร Phase 3 ข้อ 7)

```sql
CREATE TABLE house_meanings (
    factor_id       VARCHAR(20) PRIMARY KEY REFERENCES factors(factor_id),
    meaning_th      TEXT NOT NULL   -- "เรือนที่ดาวนี้สถิต จะมีธรรมชาติแบบใด"
);
```

### 2.5 `keywords_extended` — คำหลัก 4 มิติของแต่ละดาว (จากเอกสาร Phase 4)
รวมอยู่ใน `factors` แล้ว (principle/function/expression/manifestation) — ไม่ต้องแยกตาราง เว้นแต่ต้องการ versioning หลายชุดคำหลัก (เช่น จากหลายตำรา) ในอนาคต ค่อยแยกเป็น `keyword_sources` table

---

## 3. User / Chart Tables

### 3.1 `natal_charts`

```sql
CREATE TABLE natal_charts (
    chart_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(user_id),
    birth_datetime_utc TIMESTAMP NOT NULL,
    birth_lat       DECIMAL(9,6) NOT NULL,
    birth_lon       DECIMAL(9,6) NOT NULL,
    house_system    VARCHAR(20) DEFAULT 'uranian_equal_m',  -- ระบบเรือนยูเรเนียน (จาก Phase 4)
    node_type       ENUM('mean','true') DEFAULT 'mean',      -- ต้องเลือกและ fix ไว้ (Phase 5)
    created_at      TIMESTAMP DEFAULT now()
);
```

### 3.2 `chart_positions` — ตำแหน่งดาวจริง ณ เวลา/สถานที่หนึ่งๆ (ใช้ได้ทั้ง natal, directed, transit)

```sql
CREATE TABLE chart_positions (
    id              SERIAL PRIMARY KEY,
    chart_id        UUID REFERENCES natal_charts(chart_id),
    position_type   ENUM('natal','directed','transit') NOT NULL,
    reference_date  DATE,                        -- ใช้กับ directed/transit เท่านั้น (NULL สำหรับ natal)
    factor_id       VARCHAR(20) REFERENCES factors(factor_id),
    longitude_wc    DECIMAL(8,4) NOT NULL,        -- whole-circle 0-360°
    house_number    SMALLINT,                     -- 1-12 ตามระบบเรือนยูเรเนียน
    UNIQUE (chart_id, position_type, reference_date, factor_id)
);

CREATE INDEX idx_positions_lookup ON chart_positions (chart_id, position_type, reference_date);
```

### 3.3 `detected_pictures` — ผลลัพธ์ configuration ที่ engine หาเจอในดวงของผู้ใช้แต่ละคน

```sql
CREATE TABLE detected_pictures (
    id              SERIAL PRIMARY KEY,
    chart_id        UUID REFERENCES natal_charts(chart_id),
    picture_type    ENUM('type1','type2') NOT NULL,
    axis_factors    VARCHAR(20)[] NOT NULL,       -- array ของปัจจัยที่ประกอบ picture นี้
    picture_source  ENUM('natal','directed','transit') NOT NULL,
    orb_actual      DECIMAL(5,3) NOT NULL,        -- orb จริงที่วัดได้ (องศา)
    dial_type       ENUM('360','90') NOT NULL,    -- ตรวจพบจากหน้าปัดไหน
    has_personal_point BOOLEAN NOT NULL,          -- ใช้คัดกรองความสำคัญ (Phase 2 ข้อ 6.5)
    matched_meaning_id INT REFERENCES planetary_pictures(picture_id),  -- NULL ถ้ายังไม่มีความหมายในฐานข้อมูล
    computed_at     TIMESTAMP DEFAULT now()
);
```

### 3.4 `sensitive_points` — จุดที่รอปัจจัยมาเติม (สำหรับ transit forecast, จาก Phase 2 ข้อ 4)

```sql
CREATE TABLE sensitive_points (
    id              SERIAL PRIMARY KEY,
    chart_id        UUID REFERENCES natal_charts(chart_id),
    known_factors   VARCHAR(20)[] NOT NULL,   -- เช่น ['D','E','C'] จาก B = D+E-C
    target_longitude DECIMAL(8,4) NOT NULL,   -- ตำแหน่งที่ต้องการให้ดาว transit มาตกพอดี
    picture_id_ref  INT REFERENCES planetary_pictures(picture_id)
);
```

---

## 4. Pseudocode: Core Engine Pipeline

### 4.1 คำนวณตำแหน่งดาว (ใช้ Swiss Ephemeris + ephemeris เสริมของ transneptunian)

```python
def compute_positions(chart_id, dt_utc, lat, lon, position_type="natal", ref_date=None):
    positions = {}
    # ดาวเคราะห์จริง + Sun/Moon จาก Swiss Ephemeris
    for factor in STANDARD_FACTORS:  # Sun..Pluto
        positions[factor] = swisseph.get_longitude(factor, dt_utc)

    # M และ A จากสูตร RAMC (เอกสาร Phase 4 บทที่ III)
    positions["M"] = compute_midheaven(dt_utc, lon)
    positions["A"] = compute_ascendant(dt_utc, lat, lon)
    positions["NODE"] = swisseph.get_node(dt_utc, mode=chart.node_type)
    positions["ARIES"] = 0.0  # cardinal point คงที่

    # ดาวสมมติ (transneptunian) จาก ephemeris เฉพาะ (เอกสาร Phase 4)
    for factor in TRANSNEPTUNIAN_FACTORS:
        positions[factor] = uranian_ephemeris.get_longitude(factor, dt_utc)

    save_chart_positions(chart_id, position_type, ref_date, positions)
    return positions
```

### 4.2 สร้าง Midpoint Matrix

```python
def build_midpoint_matrix(positions: dict) -> dict:
    midpoints = {}
    factors = list(positions.keys())
    for i, a in enumerate(factors):
        for b in factors[i + 1 :]:
            mp = whole_circle_midpoint(positions[a], positions[b])
            midpoints[frozenset([a, b])] = mp
    return midpoints
```

### 4.3 ตรวจหา Planetary Picture บน 90°-Dial (ตามเอกสาร Phase 2 ข้อ 6)

```python
def find_pictures_90dial(positions, midpoints, orb_off_center=1.5, orb_off_side=3.0):
    found_pictures = []
    dial90_positions = {f: to_90dial(lon) for f, lon in positions.items()}

    # Type I: ปัจจัยเดี่ยวตกที่ midpoint
    for pair, mp in midpoints.items():
        mp90 = to_90dial(mp)
        for factor, pos90 in dial90_positions.items():
            if factor in pair:
                continue
            diff = angular_diff(pos90, mp90)
            if diff <= orb_off_center:
                found_pictures.append(
                    {
                        "type": "type1",
                        "factors": list(pair) + [factor],
                        "orb": diff,
                        "has_personal_point": any(
                            f in PERSONAL_POINTS for f in list(pair) + [factor]
                        ),
                    }
                )

    # Type II: midpoint คู่หนึ่งตรงกับ midpoint อีกคู่หนึ่งบน 90-dial
    midpoint_items = list(midpoints.items())
    for i, (pair1, mp1) in enumerate(midpoint_items):
        for pair2, mp2 in midpoint_items[i + 1 :]:
            if pair1 & pair2:  # มีปัจจัยซ้ำกัน ข้าม
                continue
            diff = angular_diff(to_90dial(mp1), to_90dial(mp2))
            if diff <= orb_off_side:
                combined = list(pair1) + list(pair2)
                found_pictures.append(
                    {
                        "type": "type2",
                        "factors": combined,
                        "orb": diff,
                        "has_personal_point": any(f in PERSONAL_POINTS for f in combined),
                    }
                )

    return found_pictures
```

### 4.4 คัดกรองและจับคู่กับฐานข้อมูลความหมาย

```python
def filter_and_match(found_pictures, db):
    significant = [p for p in found_pictures if p["has_personal_point"]]
    for pic in significant:
        pic["meaning"] = db.lookup_planetary_picture(pic["factors"], pic["type"])
        if pic["meaning"] is None:
            pic["meaning"] = db.lookup_axis_meaning_fallback(
                pic["factors"]
            )  # ใช้ axis_meanings แทนถ้าไม่เจอสูตรตรง
    return significant
```

### 4.5 Solar Arc Forecast (จากเอกสาร Phase 5)

```python
def solar_arc_forecast(chart_id, target_date):
    natal = load_positions(chart_id, "natal")
    progressed_sun = compute_progressed_sun(natal, target_date)
    solar_arc = angular_diff(progressed_sun, natal["SUN"])

    directed_positions = {f: (lon + solar_arc) % 360 for f, lon in natal.items()}
    save_chart_positions(chart_id, "directed", target_date, directed_positions)

    midpoints_directed = build_midpoint_matrix(
        {**natal, **{f"d.{k}": v for k, v in directed_positions.items()}}
    )
    pictures = find_pictures_90dial({**natal, **directed_positions}, midpoints_directed)
    return filter_and_match(pictures, db)
```

### 4.6 Transit Check (orb แคบ ≤1°, เน้นดาวช้า — Phase 5)

```python
def transit_forecast(chart_id, check_date):
    natal = load_positions(chart_id, "natal")
    directed = load_positions(chart_id, "directed", latest_before(check_date))
    transit = compute_positions_ephemeris_only(check_date)

    combined = merge_with_prefix(natal, directed, transit)  # ติด prefix 'tr.' / 'v.' ตามชื่อในหนังสือ
    midpoints = build_midpoint_matrix(combined)

    pictures = find_pictures_90dial(combined, midpoints, orb_off_center=0.5, orb_off_side=1.0)
    # เน้นเฉพาะ picture ที่มีดาว transit ช้า (Jupiter–Poseidon) เกี่ยวข้อง
    pictures = [
        p
        for p in pictures
        if any(f.startswith("tr.") and base(f) in SLOW_FACTORS for f in p["factors"])
    ]
    return filter_and_match(pictures, db)
```

### 4.7 ส่งต่อให้ Synthesis Layer

```python
def synthesize(pictures: list, question_context: str) -> str:
    prompt = build_prompt(pictures, question_context)
    # prompt รวม: รายการ picture ที่เจอ + ความหมายจาก DB + axis_meanings ที่เกี่ยวข้อง
    # + house_meanings ของแต่ละปัจจัยในดวง
    return call_claude_api(prompt)
```

---

## 5. ข้อควรระวังเชิง Data Integrity

- **`planetary_pictures` ยังไม่ครบ** — มีแค่ ~48 คู่จากส่วน "Glossary of Selected Combinations" (คัดสรรเท่านั้น) ระบบต้องรองรับกรณี `matched_meaning_id IS NULL` โดย fallback ไปที่ `axis_meanings` หรือ synthesis จากคำหลัก 4 มิติใน `factors` แทน
- **`node_type`** ต้อง fix ต่อ chart ตั้งแต่สร้างดวง ห้ามสลับไปมาระหว่าง mean/true ในดวงเดียวกัน เพราะจะทำให้ Node-axis picture คลาดเคลื่อน
- **Orb ต้องแยกตามบริบท** — natal (90°-dial: off-center 1.5°/off-side 3°) vs transit (≤1°) ตามที่ระบุในเอกสาร Phase 2 และ 5 ห้ามใช้ orb เดียวกันทุกกรณี
- **`has_personal_point` ต้องคำนวณก่อนบันทึกเสมอ** — picture ที่ไม่มี personal point เกี่ยวข้องเลยไม่ถือว่ามีนัยสำคัญ (ตามหลักในเอกสาร Phase 2) ไม่ควรส่งเข้า synthesis layer เพื่อประหยัด token และลดสัญญาณรบกวน

---

## 6. ขั้นตอนถัดไปที่แนะนำ

1. Implement `compute_positions()` จริงด้วย Swiss Ephemeris + จัดหา/ตรวจสอบ ephemeris ของดาวสมมติ 8 ดวง
2. เขียน migration สร้างตารางทั้งหมดข้างต้น แล้ว seed ข้อมูลจาก 5 ไฟล์ .md ที่มีอยู่ (แปลงตารางใน .md เป็น INSERT statements)
3. เขียน unit test เทียบกับตัวอย่างในหนังสือ (เช่น Judy Garland's M/Kronos = Jupiter) เพื่อตรวจสอบความถูกต้องของ midpoint/dial calculation
4. ค่อยขยาย `planetary_pictures` ให้ครบมากกว่า 48 คู่ (จากแหล่งอื่นในอนาคต ตามที่ระบุใน Phase 1 ข้อ 5)

