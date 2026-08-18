# ลำดับชั้นของจาน (Dial Hierarchy) — 360° / 90° / 45° / 22.5°

> สรุป/วิเคราะห์จากการค้นคว้าเพิ่มเติมนอกเหนือจากต้นฉบับ Niggemann (ดู
> `uranian-niggemann-primary-source.md`) — คราวนี้เป็นการยืนยันคำอธิบายที่ผู้ใช้เสนอมาเรื่องจาน 45°
> และ 22.5° ด้วยแหล่งข้อมูลภายนอก (WebSearch) แล้วนำไปเทียบกับพฤติกรรมจริงของโค้ด engine ในโปรเจกต์นี้
> ผลคือพบบั๊กจริงที่มีมาตั้งแต่ `_find_pictures()` เขียนครั้งแรก และนำไปสู่การแก้ไข + ฟีเจอร์ใหม่ 3 อย่าง
> ที่บันทึกไว้ในเอกสารนี้

**หมายเหตุแหล่งข้อมูล:** เว็บที่มีรายละเอียดลึกที่สุด (uranian-institute.org, astro.com,
kerykeion.net) ถูก block โดย network egress proxy ของ session — ใช้ได้แค่ snippet จาก WebSearch
เท่านั้น ไม่สามารถ WebFetch เนื้อหาเต็มได้ ข้อสรุปด้านล่างอิงจาก snippet ที่ดึงมาได้ + คำพูดตรงที่ปรากฏใน
snippet เหล่านั้น + เนื้อหาที่ยืนยันไขว้กับ `uranian-niggemann-primary-source.md` ที่มีอยู่แล้ว

---

## 1. ตารางฮาร์มอนิกของจานแต่ละขนาด (ยืนยันจากภายนอกแล้ว)

| จาน | Harmonic | มุมที่จับเป็น "hit" | จุดประสงค์หลัก |
|---|---|---|---|
| 360° | 1st | ตำแหน่งจริง, ราศี, เรือน | ภาพรวม/บริบท |
| 90° | 4th → **8th (หลังแก้บั๊ก)** | conjunction/semisquare/square/sesquiquadrate/opposition (0/45/90/135/180°) | โครงสร้างหลัก (Core Story) — Type I/II picture |
| 45° | 8th | เหมือนจาน 90° ที่แก้แล้วทุกประการ | **ไม่ใช่เครื่องมือใหม่** — ดูหัวข้อ 2 |
| 22.5° | 16th | เพิ่ม semi-octile (22.5/67.5/112.5/157.5°) | ระบุ "วันไหน" ของ event จร |

แหล่งอ้างอิงคำว่า "8th/16th harmonic": ผลค้นหายืนยันตรงกันหลายแหล่งว่า "Many Uranian astrologers also
work with 45-degree and 22.5-degree dials (the 8th and 16th harmonics)" และเรียกมุม 22.5° ว่า
"semi-octile" — ชุดมุมที่จาน 22.5° ดักจับคือทวีคูณคี่ของ 22.5 ทั้งหมด (22.5, 45, 67.5, 90, 112.5, 135,
157.5, 180)

---

## 2. จาน 45° ไม่ใช่เครื่องมือใหม่ — เป็นข้อมูลเดียวกับจาน 90° อ่านอีกด้าน

พบคำพูดตรงของ **Ludwig Rudolph** (หนึ่งใน 4 ผู้เขียนร่วมของ Niggemann ที่ถอดความไปแล้วในเซสชันนี้)
ที่อธิบายเรื่องนี้ชัดเจนที่สุด:

> Rudolph pointed out ... you "don't have to re-invent the wheel" and use a new 22.5 dial or chart,
> but simply take note of the midpoints on any given 90 axis, and then **turn the dial sideways** ...
> at a 90 angle.

ตรงกับสิ่งที่ต้นฉบับ Niggemann เขียนไว้แล้ว (หน้า 11, อ้างใน `uranian-niggemann-primary-source.md`
หัวข้อ 2):

> "All squares and oppositions show as conjunctions, while the semi- and sesqui-squares show
> **as oppositions**"

สรุป: จาน 90° เดิมอ่านได้ 2 แบบ — "จุดเดียวกัน" (conjunction/square/opposition family) กับ "จุดตรงข้าม"
(semisquare/sesquiquadrate family) — จาน 45° ก็คือข้อมูลชุดเดียวกันนี้ พับให้ทั้งสองแบบกลายเป็น "จุด
เดียวกัน" ไปเลย ไม่ใช่มุมใหม่ที่จาน 90° ไม่มี

---

## 3. บั๊กจริงที่พบใน `_dial90_orb()` — และการแก้ไข

ก่อนแก้ไข ฟังก์ชันนี้พับที่ mod 90 (`min(diff, 90-diff)` จาก `diff = (a-b) % 90`) ซึ่งจับได้แค่ตระกูล
conjunction/square/opposition (diff ใกล้ 0) เท่านั้น — กรณี semisquare/sesquiquadrate (ห่างกัน 45°)
กลับได้ค่าสูงสุดที่ฟังก์ชันเป็นไปได้ (45) ซึ่งไม่มีทางผ่าน orb threshold ได้เลย พิสูจน์ได้ตรงๆ จาก unit
test ที่มีอยู่ก่อนแล้ว: `_dial90_orb(0, 45) == 45` (แก้เป็น `== 0` แล้ว)

**ผลกระทบ:** `solar_arc.py` และ `transit.py` ทั้งคู่ `import _dial90_orb` ตรงจาก `engine.py` — ใช้ตัว
เดียวกันไม่มีสูตรพับจานของตัวเอง ดังนั้นบั๊กนี้กระทบครบทั้ง 3 ชั้น (natal/directed/transit) มาตั้งแต่แรก
ไม่ใช่แค่ natal chart engine

**การแก้ไข:** เพิ่มฟังก์ชันกลาง `_dial_fold_orb(a, b, fold_degrees)` แล้วให้ `_dial90_orb` เรียกมันด้วย
`fold_degrees=45.0` แทน — จับทั้ง 5 มุมแข็งของยูเรเนียนพร้อมกันในฟังก์ชันเดียว ตรงกับที่ Rudolph อธิบายว่า
"ไม่ต้องสร้างจานใหม่ แค่อ่านจาน 90° ให้ครบทั้งสองด้าน" ชื่อฟังก์ชัน `_dial90_orb` คงไว้เหมือนเดิม (90
หมายถึงขนาดจานจริง ไม่ใช่ modulus ที่ใช้พับภายใน) เพื่อไม่ต้องแก้ import ใน 3 ไฟล์

**ทดสอบแล้ว:** รันชุดทดสอบทั้งหมด (`solar_arc`/`transit`/`engine` — 149 เทสต์ก่อนแก้) พบว่ามีแค่ 1 เทสต์
ที่พังตรงๆ (คือ assertion ที่เขียนขึ้นเพื่อล็อกพฤติกรรมบั๊กไว้พอดี) เทสต์อื่นๆ ทั้งหมดผ่านต่อ ยืนยันว่า
fixture ที่มีอยู่ก่อนไม่ได้พึ่งพากรณีขอบ 45° นี้โดยบังเอิญ

---

## 4. Significance tier — orb แคบ = เรื่องใหญ่หลีกเลี่ยงไม่ได้

ผู้ใช้เสนอหลักการ: "สมการใดที่เห็นบนจาน 90° แล้ว วางบนจานละเอียดกว่าแล้วดาวทับกันสนิทพอดี (orb≈0) เรื่อง
นั้นจะเป็นเรื่องใหญ่หลีกเลี่ยงไม่ได้" — วิเคราะห์แล้วพบว่านี่**ไม่ใช่การพับจานใหม่** แต่เป็นการ**เช็ก orb
ของ finding ที่เจอแล้วซ้ำด้วย threshold ที่แคบกว่าเดิม** เพราะการซูมด้วยจานเล็กลงในทางกลไกจริงคือการขยาย
(magnify) ความละเอียดของการอ่าน ไม่ใช่มุมใหม่ — สอดคล้องกับที่ Niggemann เขียนไว้เรื่อง orb ที่ยิ่งแคบยิ่ง
มีนัยสำคัญ (`uranian-niggemann-primary-source.md` หัวข้อ 4)

**Implement แล้ว:** `SIGNIFICANT_ORB_DEGREES = 0.5` + `_significance_suffix(orb)` ใน `engine.py` — เติม
เครื่องหมาย "★ ตรงเป๊ะ (เรื่องใหญ่ที่หลีกเลี่ยงยาก)" ต่อท้าย label เมื่อ orb ≤ 0.5° ใช้ตัวเดียวกันทั้ง 3
จุด: `_picture_finding()`, `_antiscia_finding()` (natal engine), และ `_forecast_picture_label()` ใน
`main.py` (solar arc + transit) — ไม่ต้องมีฟังก์ชันพับจานแยก ใช้ orb ที่คำนวณอยู่แล้วซ้ำ

ตัวเลข 0.5° เป็นค่ากลางระหว่างข้อเสนอของผู้ใช้ (0.25-0.5°) กับ orb เดิมของระบบ (radix Type I 1.5°,
transit 1.0°) — ยังไม่มีแหล่งภายนอกยืนยันตัวเลขที่แน่นอน (เว็บที่มีรายละเอียดระดับนี้โดนบล็อก) ถือเป็นค่า
เริ่มต้นที่ปรับได้ภายหลังหากพบข้อมูลที่แม่นกว่านี้

---

## 5. จาน 22.5° (16th harmonic) — ฟีเจอร์ใหม่จริง สำหรับ "วันไหน"

ต่างจากข้อ 2-4 ตรงนี้เป็นมุมใหม่จริง (22.5°/67.5°/112.5°/157.5°) ที่จาน 90° (แม้แก้บั๊กแล้ว) ก็ยังจับไม่
ได้ — ตรงกับที่ผู้ใช้อธิบายวัตถุประสงค์: "กำหนดวันด้วยจาน 22.5° เมื่อดาวจรดวงเร็ว (อาทิตย์, อังคาร) ขยับ
มาทับจุดศูนย์รังสีเดิมพอดีเป๊ะ เหตุการณ์จะปะทุออกมารูปธรรมทันที"

**Implement แล้วใน `transit.py`:**
- `_dial225_orb()` ใน `engine.py` — พับที่ mod 22.5 (ครอบคลุมมุมของ `_dial90_orb` ด้วย เป็น superset)
- `find_fine_timing_hits()` ใน `transit.py` — เช็กเฉพาะดาวจรที่เคลื่อนที่เร็ว
  (`FAST_TRANSIT_FACTORS = {SUN, MOON, MERCURY, VENUS, MARS, NODE}` — ตรงข้ามกับ `SLOW_TRANSIT_FACTORS`
  ที่มีอยู่แล้ว) เทียบกับจุดส่วนตัว (personal point) ของ radix/directed เท่านั้น ที่ orb แคบมาก
  (`FINE_TIMING_ORB_DEGREES = 0.5`)
- **ทำไมไม่ใช้ midpoint search แบบเดียวกับ `find_transit_pictures()`:** การหาวันที่แม่นยำมาจาก "ดาวจร
  ดวงเดียวมาทับจุดอ้างอิงคงที่" ไม่ใช่โครงสร้าง 4 ปัจจัยแบบ midpoint picture — จึงออกแบบเป็นการเช็กจุดต่อ
  จุดตรงๆ ไม่ใช่ combinatorics เต็มรูปแบบ ง่ายกว่าและตรงกับ use case มากกว่า
- Schema: เพิ่ม `FineTimingHit` และ field `TransitResult.fine_timing` (ไม่แตะ `PictureResult.type`
  Literal เดิม เพื่อไม่ให้กระทบ frontend ที่มี ternary `type === "type1" ? ... : ...` อยู่แล้ว)
- Frontend: เพิ่ม type `FineTimingHit` ใน `lib/api.ts` และ component `FineTimingList` ใน
  `ReadingResult.tsx` แสดงใต้ตาราง picture ของแท็บ Transit

---

## 6. สรุปการแมปกับโค้ดจริง

| แนวคิดจากผู้ใช้ | Implement ที่ไหน | สถานะ |
|---|---|---|
| จาน 90° = Core Story | `engine.py::_find_pictures` | แก้บั๊ก mod-45 แล้ว |
| จาน 90°/45° = ภาพรวมเดือน (predictive) | `solar_arc.py::find_directed_pictures` (ใช้ `_dial90_orb` ตัวเดียวกัน) | ได้รับการแก้บั๊กไปด้วยอัตโนมัติ เพราะ import ร่วมกัน |
| จาน 22.5° = ระดับวัน/สัปดาห์ | `transit.py::find_fine_timing_hits` (ใหม่) | Implement แล้ว |
| "orb แคบ = เรื่องใหญ่" | `engine.py::_significance_suffix` + `main.py::_forecast_picture_label` | Implement แล้ว |

## 7. สิ่งที่ยังไม่ได้ทำ / ควรตรวจต่อ

- ตัวเลข `SIGNIFICANT_ORB_DEGREES`/`FINE_TIMING_ORB_DEGREES` (0.5°) เป็นค่าประมาณ ยังไม่ยืนยันจากแหล่ง
  ภายนอกที่เชื่อถือได้ 100% เพราะเว็บหลักโดน network proxy บล็อก — ถ้าหาแหล่งที่เชื่อถือได้เพิ่มเติมควร
  กลับมาปรับ
- ยังไม่ได้ทำ frontend end-to-end browser test เต็มรูปแบบสำหรับส่วน fine-timing (ตรวจแค่ `next build` +
  `eslint` ผ่านเท่านั้น เพราะการทดสอบจริงต้องผ่าน auth + backend เต็มระบบ)
- แนวคิด "จาน 22.5° สำหรับ natal/solar-arc" (ไม่ใช่แค่ transit) ยังไม่ได้ทำ — ผู้ใช้เน้นว่าจาน 22.5°
  เหมาะกับ "วันไหน" ซึ่งมีความหมายเฉพาะกับ transit เท่านั้น (natal/solar-arc ไม่มีมิติ "วัน" ให้จับ)
