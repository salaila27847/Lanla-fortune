# Uranian knowledge base

## โครงสร้าง

```
points.yaml              ← 8 ดาวเสริม (Cupido, Hades, Zeus, Kronos, Apollon, Admetos,
                            Vulkanus, Poseidon) — id (ตัวพิมพ์เล็ก), swe_id (40-47),
                            name_th, keywords, meaning_core
signs.yaml                ← 12 ราศี — id, name_th, start_degree, modifier (วลีปรับสีสัน
                            การแสดงออกของปัจจัยเมื่ออยู่ในราศีนั้น)
factors.yaml               ← อีก 14 ปัจจัย (6 จุดส่วนตัวอ้างอิง: ARIES, M, A, SUN, MOON,
                            NODE + ดาวเคราะห์คลาสสิก 8 ดวง: MERCURY-PLUTO) — id (ตัวพิมพ์ใหญ่
                            ให้ตรงกับ planetary_pictures.yaml/axis_meanings.yaml), name_th,
                            category (personal_point/planet), keywords, meaning_core
planetary_pictures.yaml   ← glossary คู่ปัจจัย (factor pair) ที่มีความหมายเฉพาะตัว 50 คู่
                            (ถอดความจาก "Glossary of Selected Combinations")
axis_meanings.yaml         ← ความหมายเมื่อปัจจัยหนึ่งจับคู่กับแกน M/A/SUN/MOON/NODE (ระดับ "ธีมของ
                            คู่" ไม่แยกตามปัจจัยที่ 3) — M/A/MOON/NODE ครบ 21 คู่ (ทุกปัจจัยอื่น),
                            SUN มี 19 คู่ (ต้นฉบับไม่ได้ระบุ Sun+Apollon/Sun+Admetos)
witte_pictures.yaml        ← glossary ละเอียดกว่า axis_meanings.yaml อีกชั้น — คู่ปัจจัย + ปัจจัย
                            ที่ 3 ที่ตกกลาง = ความหมายเฉพาะ (เช่น M+SUN=ARIES ต่างจาก M+SUN=SATURN)
                            ถอดความจากตำรา "Rules for Planetary Pictures" ของ Witte ฉบับเต็มที่
                            ผู้ใช้ส่งมาให้ (OCR คุณภาพต่ำ ต้องอ่านสร้างใหม่ทุกรายการ) — **ทำครบทั้ง
                            22 หมวดของหนังสือแล้ว** (Meridian → Aries → Sun → Ascendant → Moon →
                            Node → Mercury → Venus → Mars → Jupiter → Saturn → Uranus → Neptune →
                            Pluto → Cupido → Hades → Zeus → Kronos → Apollon → Admetos → Vulkanus
                            → Poseidon ตามลำดับที่หนังสือกำหนด) รวม **226 base pairs, 4,400
                            รายการ** จาก 231 คู่ที่เป็นไปได้ทางทฤษฎี — 5 คู่ที่ขาดไปทั้งคู่
                            (A+NODE, A+CUPIDO, A+ADMETOS, CUPIDO+SUN, APOLLON+SUN) ข้ามไปตั้งใจ
                            เพราะ OCR เสียจนระบุตัวบ่งชี้ปัจจัยที่ 3 ไม่ได้เลย ดูรายละเอียดที่หัวข้อ
                            "ยังไม่ได้ทำ" ด้านล่าง
research/                  ← เอกสารวิจัยต้นทาง (ภาษาไทย, ถอดความจากตำรา ไม่ใช่คำแปลตรงตัว)
                            เก็บไว้เป็นแหล่งอ้างอิงสำหรับขยาย KB ต่อ (เช่น house_meanings,
                            factors principle/function/expression/manifestation) — รวมถึง
                            `uranian-niggemann-primary-source.md` ที่ถอดความจากตำราปฐมภูมิ
                            "The Principles of the Uranian System of Astrology" ของ Hans
                            Niggemann (ลูกศิษย์ตรงของ Witte/Sieggrün) มี antiscia formula
                            (implement แล้วใน engine.py — ดูข้อ 5 ด้านล่าง), orb reference
                            เพิ่มเติม, และประวัติศาสตร์ที่มาของดาวสมมติ
```

`points.yaml` ใช้ id ตัวพิมพ์เล็ก (เช่น `cupido`) ส่วน `factors.yaml`/`planetary_pictures.yaml`/
`axis_meanings.yaml` ใช้ id ตัวพิมพ์ใหญ่ (เช่น `CUPIDO`, `MERCURY`, `M`) — engine จะ uppercase
id จาก `points.yaml` เองตอนค้นหา planetary picture (`_factor_display_name`/`_factor_keywords`
ใน `engine.py` handle ทั้งสองรูปแบบ)

## เนื้อหาจากแหล่งใด

เนื้อหาใน `points.yaml`, `planetary_pictures.yaml`, `axis_meanings.yaml`, และ `research/`
ถอดความ/สรุปโครงสร้างจาก *The Language of Uranian Astrology* โดย Roger A. Jacobson (มีลิขสิทธิ์)
— ใช้งานภายในโปรเจกต์เท่านั้น ไม่ใช่คำแปลตรงตัว ส่วน `signs.yaml`/`factors.yaml` เป็นความหมาย
ทั่วไปตามหลักโหราศาสตร์สากลที่ไม่ได้อิงตำราเล่มใดโดยเฉพาะ

## `app/modules/uranian/engine.py` ทำอะไรบ้าง

คำนวณตำแหน่งจริงด้วย `pyswisseph` (อีเฟเมอริส Moshier ในตัว ไม่ต้องใช้ไฟล์ข้อมูลเสริมหรือ
อินเทอร์เน็ต):

1. แปลงวัน/เวลา/เขตเวลาเกิดเป็น Julian Day (UT) ด้วย `zoneinfo` — ถ้าไม่ทราบเวลาเกิด
   ใช้เที่ยงวันเป็นค่าประมาณ และลดค่า `confidence` ลง พร้อมแจ้งข้อจำกัดใน findings
2. คำนวณตำแหน่งทั้ง 22 ปัจจัย (10 ดาวเคราะห์คลาสสิก + 8 ดาวเสริม + Node + จุดอาริส +
   Ascendant/Midheaven ถ้าทราบเวลาเกิด) — Node ใช้ **True Node** (`swe.TRUE_NODE`) ไม่ใช่ Mean
   Node — ผู้ใช้ตัดสินใจแล้ว (2026-08-13) หลังเทียบผลกับเว็บอ้างอิงอื่นแล้วพบว่าต่างกัน ~0.5°
   จาก Mean/True Node convention ที่ต่างกัน
3. **Placement findings** — ดาวเสริมทั้ง 8 ดวงจับคู่กับราศีและองศาที่อยู่ ประกอบความหมายจาก
   `points.yaml` + `signs.yaml` (เหมือนเดิม)
4. **Planetary-picture findings** — หา midpoint structure บน 90° dial ระหว่างปัจจัยทั้งหมด:
   - **Type I**: ปัจจัยเดี่ยวตกที่ midpoint ของอีกสองปัจจัย (เช่น `Mars/Saturn=Uranus`) orb 1.5°
   - **Type II**: midpoint ของคู่หนึ่งตรงกับ midpoint ของอีกคู่หนึ่ง (เช่น `M/Moon=Venus/Sun`)
     orb 3.0°

   เก็บเฉพาะภาพที่มีจุดส่วนตัว (Sun, Moon, M, A, Node, จุดอาริส) อย่างน้อยหนึ่งจุด แล้วหาความหมาย
   ตามลำดับความสำคัญนี้ (`_picture_finding` ใน `engine.py`):
   1. **Type I ที่ตรงกับ `witte_pictures.yaml` เป๊ะๆ** (คู่ปัจจัย + ปัจจัยที่ 3 ตรงกัน) — เจาะจงและ
      authoritative ที่สุด (weight 0.95) ครอบคลุมครบทั้ง 22 หมวดของหนังสือแล้ว (226/231 base pairs
      ที่เป็นไปได้ — ดูรายละเอียดหัวข้อ `witte_pictures.yaml` ด้านบนและ "ยังไม่ได้ทำ" ด้านล่าง)
   2. ถ้าไม่เจอ ลอง `planetary_pictures.yaml` (คู่ปัจจัยทั่วไป ไม่แยกปัจจัยที่ 3, weight 0.75-0.85)
   3. ถ้ายังไม่เจอ ประกอบความหมายทั่วไปจาก keywords ของแต่ละปัจจัยแทน (weight 0.45-0.55)

   จากนั้นถ้าภาพมีแกนใดแกนหนึ่งใน `axis_meanings.yaml` ร่วมอยู่ด้วย (M, A, SUN, MOON, NODE) จะเติม
   หมายเหตุจากแกนนั้นต่อท้ายเสมอ ไม่ว่าความหมายหลักจะมาจากขั้นตอนไหนก็ตาม — ถ้ามีมากกว่าหนึ่งแกนใน
   ภาพเดียวกัน (เช่น M/Mars=Sun/Saturn มีทั้ง M และ SUN) จะเติมหมายเหตุของทุกแกนที่พบ ไม่ใช่แค่แกนแรก
5. **Antiscia-contact findings** — ปัจจัยหนึ่งตกที่จุดสะท้อน (antiscion) ของอีกปัจจัยหนึ่ง คือจุดที่มี
   declination เท่ากันข้ามแกนครีษมายัน Cancer/Capricorn (`_antiscion()`: `180° - longitude`) orb 1.5°
   เหมือน Type I เพราะอ่านเหมือนคอนจังชันตรงๆ — เป็นความสัมพันธ์คนละแบบจาก midpoint picture ด้านบน
   (ไม่ใช่ Type I/II) คำนวณแยกด้วย `_find_antiscia_contacts()` แล้วต่อท้าย picture findings **เสมอ**
   ไม่ว่า orb จะแคบแค่ไหนก็ไม่แซงหน้าภาพจริงขึ้นไปอยู่อันดับแรก เพราะต้นฉบับปฐมภูมิ (ดู
   `research/uranian-niggemann-primary-source.md` หัวข้อ 3) ระบุชัดว่า antiscia ให้ผลอ่อนกว่า
   picture ที่ครบสมบูรณ์เสมอ — หาความหมายจาก `planetary_pictures.yaml` ถ้ามีคู่ตรงกัน (weight 0.5)
   ไม่งั้น compose จาก keywords ของทั้งสองปัจจัย (weight 0.35) เก็บสูงสุด 5 รายการ
   (`MAX_ANTISCIA_FINDINGS`)

ไม่มี hardcode เนื้อหาความหมายในโค้ด engine ทั้งหมดโหลดจากไฟล์ YAML ข้างต้น

## `app/modules/uranian/{solar_arc,transit}.py` — forecast (ไม่บังคับ, ไม่มี KB ของตัวเอง)

ต่างจาก natal engine ข้างบน 2 โมดูลนี้**ไม่มีไฟล์ knowledge base แยก** — ใช้ label ของปัจจัย/คู่ปัจจัย
ตรงๆ (เช่น `r:SUN / d:VENUS = t:JUPITER`) ไม่ผ่าน `planetary_pictures.yaml`/`axis_meanings.yaml`
เพราะเนื้อหาที่มีอยู่อิงชุดปัจจัยเดี่ยว ไม่ได้ครอบคลุมทุก combination ข้าม 3 ชั้น (radix/directed/transit)
ที่เป็นไปได้ — ผลลัพธ์แสดงเป็นตารางดิบที่หน้า `/reading` (tab "การพยากรณ์ล่วงหน้า") และส่งเข้า Gemini
synthesis ให้ตีความรวมกับ 3 engine หลัก (ดู `docs/data-schema.md` หัวข้อ Forecast, `master_interpreter.py`):

- `solar_arc.py`: Solar Arc Directions — `progressed_sun_longitude()`, `solar_arc_degrees()`,
  `directed_positions()`, `find_directed_pictures()`
- `transit.py`: Transit จริง ณ วันที่เลือก (`transit_positions()`, `find_transit_pictures()`,
  orb แคบ 1°), Station Points (`daily_speed()`, `find_stations_in_range()`), Lunar Return
  (`find_lunar_return()`, bisection search), Relocation (`relocated_angles()`), Daily M/A
  (`transit_positions(birth_data=...)` เพิ่ม Ascendant/Midheaven ของวันนั้นที่สถานที่เกิดเดิม) และ
  Transit Axes (เกิดขึ้นเองจาก `find_transit_pictures()` เมื่อมี Daily M/A โดยไม่ต้องมีปัจจัย
  radix/directed เลย)

## ยังไม่ได้ทำ (สืบทอดจาก handoff package)

- ไม่มี `house_meanings` — engine นี้ยังไม่คำนวณว่าดาวแต่ละดวงตกเรือนที่เท่าไหร่ (เนื้อหาความหมาย
  "ธรรมชาติของเรือนที่ดาวสถิต" ต่อดาว มีอยู่แล้วใน `research/uranian-delineation-axes.md` หัวข้อ 7
  — แต่การคำนวณจริงว่าดาวแต่ละดวงตกเรือนที่เท่าไหร่ยังไม่ implement เพราะระบบเรือนยูเรเนียนเป็น
  equal-house อ้างอิงจาก M ไม่ใช่ Placidus ที่ `swe.houses()` คืนมาตรงๆ — ต้องคำนวณ house cusp
  เองจาก M ก่อน (ดู `research/` เอกสารบทที่ 4 เรื่อง 360°-dial/reflex house)
- `planetary_pictures.yaml` เป็นการคัดสรร 50 คู่ ไม่ใช่ชุดสมบูรณ์ตามต้นฉบับ (แต่ `witte_pictures.yaml`
  ครอบคลุมได้ละเอียดกว่ามากแล้วสำหรับเกือบทั้งเล่ม — ดูด้านล่าง)
- `axis_meanings.yaml` แกน SUN ขาด Sun+Apollon และ Sun+Admetos (ต้นฉบับไม่ได้ระบุไว้), แกน ARIES
  ยังไม่มีเลย (ไม่มีเนื้อหาต้นฉบับให้ถอดความ)
- `witte_pictures.yaml` **ทำครบทั้ง 22 หมวดของหนังสือแล้ว** (Meridian → Aries → Sun → Ascendant →
  Moon → Node → Mercury → Venus → Mars → Jupiter → Saturn → Uranus → Neptune → Pluto → Cupido →
  Hades → Zeus → Kronos → Apollon → Admetos → Vulkanus → Poseidon ตามลำดับที่หนังสือกำหนด) รวม
  **226 base pairs / 4,400 รายการ** จาก 231 คู่ที่เป็นไปได้ทางทฤษฎี (C(22,2)) — บาง base pair เอง
  ก็ขาดบางรายการ third-factor เพราะ OCR กู้คืนไม่ได้ (ดู comment `# missing:` ต่อท้ายคู่นั้นในตัวไฟล์
  yaml) — คุณภาพ OCR แย่ลงเรื่อยๆ ตามหลังเล่ม (ตามที่หนังสือเองเตือนไว้) โดยเฉพาะหมวด Neptune เป็นต้นไป
  **5 คู่ที่ขาดไปทั้งคู่** (ไม่ใช่แค่บางรายการ) คือ A+NODE, A+CUPIDO, A+ADMETOS (หมวด Ascendant) และ
  CUPIDO+SUN, APOLLON+SUN (หมวด Sun) — ข้ามไปตั้งใจตั้งแต่ตอนทำหมวดนั้นๆ เพราะตัวบ่งชี้ปัจจัยที่ 3
  ("-XX" prefix) หายไปจาก OCR ทั้งหมดจนไม่มีทางระบุลำดับรายการได้อย่างน่าเชื่อถือ ยังไม่ได้ลองกลับไป
  อ่าน raw OCR อีกครั้งเพื่อกู้คืน 5 คู่นี้ — ต้นฉบับ scan+OCR ดิบทั้งเล่ม (~255 หน้า, 9,599 บรรทัด)
  เก็บไว้เฉพาะในเซสชันที่แปล ไม่ได้ก็อปปี้เข้า repo เพราะไฟล์ใหญ่มาก ต้องขอผู้ใช้ส่งซ้ำถ้าจะกลับไปแก้
- forecast (`solar_arc.py`/`transit.py`) ไม่มี rate limit หรือแคชผลลัพธ์
- Antiscia ยัง**ไม่ได้**เพิ่มเข้า `solar_arc.py`/`transit.py` — ที่ implement แล้วคือใน radix engine
  (`engine.py`, ดูข้อ 5 ด้านบน) เท่านั้น กติกาการเคลื่อนที่ตอน direction (antiscion เดินสวนทาง solar arc)
  มีอยู่แล้วใน `research/uranian-niggemann-primary-source.md` หัวข้อ 3 พร้อมใช้งานถ้าจะขยายไปที่
  forecast module ในอนาคต (ไม่ blocking สำหรับ MVP ปัจจุบัน)
