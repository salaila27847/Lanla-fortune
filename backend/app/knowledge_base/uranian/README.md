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
axis_meanings.yaml         ← ความหมายเมื่อปัจจัยหนึ่งจับคู่กับแกน M (21 คู่ — ครบทุกปัจจัยอื่น)
                            แกน A/Sun/Moon/Node ยังไม่ได้ถอดความ (ดู research/ ด้านล่าง)
research/                  ← เอกสารวิจัยต้นทาง (ภาษาไทย, ถอดความจากตำรา ไม่ใช่คำแปลตรงตัว)
                            เก็บไว้เป็นแหล่งอ้างอิงสำหรับขยาย KB ต่อ (เช่น axis_meanings แกนอื่น,
                            house_meanings, factors principle/function/expression/manifestation)
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

   เก็บเฉพาะภาพที่มีจุดส่วนตัว (Sun, Moon, M, A, Node, จุดอาริส) อย่างน้อยหนึ่งจุด แล้วจับคู่กับ
   `planetary_pictures.yaml` — ถ้าเจอคู่ตรง ใช้ความหมายจาก glossary (weight สูงกว่า) ถ้าไม่เจอ
   ประกอบความหมายทั่วไปจาก keywords ของแต่ละปัจจัยแทน (weight ต่ำกว่า) ถ้าภาพมี M ร่วมอยู่ด้วย
   จะเติมหมายเหตุจาก `axis_meanings.yaml` ต่อท้ายด้วย

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

- `axis_meanings.yaml` มีแค่แกน M — แกน A, Sun, Moon, Node ยังไม่ได้ถอดความเป็น YAML
  (เนื้อหามีอยู่แล้วใน `research/uranian-delineation-axes.md`)
- ไม่มี `house_meanings` — engine นี้ยังไม่คำนวณว่าดาวแต่ละดวงตกเรือนที่เท่าไหร่
  (เนื้อหามีอยู่แล้วใน `research/uranian-delineation-axes.md` หัวข้อ 7)
- `planetary_pictures.yaml` เป็นการคัดสรร 50 คู่ ไม่ใช่ชุดสมบูรณ์ตามต้นฉบับ
- forecast (`solar_arc.py`/`transit.py`) ไม่มี rate limit หรือแคชผลลัพธ์
