# Uranian KB — รายการข้อมูลที่ยังขาด (สำหรับหาข้อมูลเพิ่มเติม)

รายการนี้รวบรวมทุก "ช่องว่างเนื้อหา" ที่เหลืออยู่ใน Uranian knowledge base ที่ต้องใช้ต้นฉบับหนังสือ
มาเติม (ไม่ใช่งานเขียนโค้ด — งานเขียนโค้ดที่เหลือ เช่น rate limit ของ forecast หรือ antiscia ใน
solar_arc/transit ทำเองได้โดยไม่ต้องรอข้อมูลเพิ่ม จึงไม่อยู่ในลิสต์นี้)

**วิธีใช้**: ไล่ตามหัวข้อ/หน้าหนังสือด้านล่าง เมื่อเจอเนื้อหาต้นฉบับ (ภาษาอังกฤษ) ของรายการไหน
**ไม่ต้องแปลเอง** — ก็อปปี้ประโยคต้นฉบับส่งกลับมาพร้อมระบุคู่ปัจจัย (เช่น "M+ARIES ขาด NODE: ...")
แล้วผมจะแปล+ใส่ในไฟล์ YAML ให้ตรง field ที่ถูกต้องเลย ถ้าตรวจแล้วว่า OCR เพี้ยนจนอ่านไม่ออกจริงๆ
ให้ข้ามได้เลย ไม่ต้องเดา (ตามนโยบายเดิมของโปรเจกต์ในทุกไฟล์ KB — ดู `# missing:` comment ในไฟล์จริง)

---

## 1. `axis_meanings.yaml` — แกน ARIES (ยังไม่มีเนื้อหาเลย) — **ควรเช็คก่อน**

ต้นฉบับ: *The Language of Uranian Astrology* โดย Roger A. Jacobson — เช็คว่ามีตาราง "Aries-axis"
(คู่กับปัจจัยอื่นแบบเดียวกับที่มีอยู่แล้วสำหรับแกน M/A/Sun/Moon/Node) หรือไม่ — ดูตัวอย่างรูปแบบที่ต้องการ
ได้ที่ `backend/app/knowledge_base/uranian/research/uranian-delineation-axes.md` หัวข้อ 3-6

ARIES จับคู่กับ M/A/SUN/MOON/NODE มีเนื้อหาอยู่แล้ว (backfill จากแกนนั้นๆ กลับมา เพราะ midpoint
สมมาตร) — เหลือแค่ 16 คู่นี้ที่ต้องหาเนื้อหาใหม่จริง:

- [ ] ARIES + MERCURY
- [ ] ARIES + VENUS
- [ ] ARIES + MARS
- [ ] ARIES + JUPITER
- [ ] ARIES + SATURN
- [ ] ARIES + URANUS
- [ ] ARIES + NEPTUNE
- [ ] ARIES + PLUTO
- [ ] ARIES + CUPIDO
- [ ] ARIES + HADES
- [ ] ARIES + ZEUS
- [ ] ARIES + KRONOS
- [ ] ARIES + APOLLON
- [ ] ARIES + ADMETOS
- [ ] ARIES + VULKANUS
- [ ] ARIES + POSEIDON

## 2. `axis_meanings.yaml` — แกน SUN ขาด 2 คู่ (priority ต่ำ)

บันทึกเดิมบอกว่า "ต้นฉบับไม่ได้ระบุไว้" — อาจไม่มีจริงๆ ในหนังสือ แต่ลองเช็คตาราง Sun-axis อีกรอบ
เผื่อพลาดตอนถอดความครั้งแรก:

- [ ] SUN + APOLLON
- [ ] SUN + ADMETOS

## 3. `witte_pictures.yaml` — 5 คู่ที่ขาดไปทั้งคู่ (สำคัญสุด หาให้ก่อน 75 รายการด้านล่าง)

ต้นฉบับ: *Rules for Planetary Pictures (Uranian System)* — Alfred Witte, เรียบเรียงโดย Hans
Niggemann (ค.ศ. 1959) — คู่เหล่านี้มาจากรอบทำงานก่อนหน้า ยังไม่เคยลองกลับไปอ่าน OCR ดิบหาเลย:

- [ ] **A + NODE** — หมวด Ascendant, หน้า 64-82
- [ ] **A + CUPIDO** — หมวด Ascendant, หน้า 64-82
- [ ] **A + ADMETOS** — หมวด Ascendant, หน้า 64-82
- [ ] **CUPIDO + SUN** — หมวด Sun, หน้า 44-63
- [ ] **APOLLON + SUN** — หมวด Sun, หน้า 44-63

แต่ละคู่ต้องมี third-factor ครบ 20 รายการ (ปัจจัยอื่นทั้งหมดที่ไม่ใช่ตัวมันเอง) เหมือนคู่อื่นๆ ในไฟล์

## 4. `witte_pictures.yaml` — third-factor ที่ขาดในคู่ที่มีเนื้อหาอยู่แล้วบางส่วน (75 รายการ)

จัดกลุ่มตามหมวด/หน้าหนังสือ ไล่ตามหน้าเดียวกันจะเจอครบทีเดียวทั้งหมวด — คำใบ้ในวงเล็บบอกตำแหน่ง
คร่าวๆ ในย่อหน้าของคู่นั้น (เช่น "between the Moon and Mercury entries" หมายถึงตำแหน่งในลำดับ
third-factor ของคู่นั้นเอง ไม่ใช่หน้าอื่น)

### หมวด เมริเดียน (M) — หน้า 1-22 (8 คู่)

- [ ] **M+ARIES** ขาด: NODE (OCR line dropped/merged between Moon and Mercury entries)
- [ ] **M+A** ขาด: NODE (not found in OCR)
- [ ] **M+MOON** ขาด: NEPTUNE (OCR line dropped between Uranus and Pluto entries)
- [ ] **M+JUPITER** ขาด: HADES (not found in OCR)
- [ ] **M+SATURN** ขาด: ARIES (not found in OCR)
- [ ] **M+URANUS** ขาด: MARS (not found in OCR)
- [ ] **M+VULKANUS** ขาด: ADMETOS (OCR merged "-Ad -Po" into one line, only the Poseidon half was recoverable)
- [ ] **M+POSEIDON** ขาด: ADMETOS (not found in OCR)

### หมวด จุดอาริส (Aries) — หน้า 23-43 (9 คู่)

- [ ] **ARIES+SUN** ขาด: NEPTUNE, APOLLON (OCR เพี้ยนเกินกู้คืนได้อย่างมั่นใจ)
- [ ] **ARIES+NODE** ขาด: MOON (บรรทัด OCR หายไประหว่างช่วง Ascendant กับ Mercury)
- [ ] **ARIES+MERCURY** ขาด: NODE (หาไม่พบใน OCR)
- [ ] **ARIES+URANUS** ขาด: ADMETOS (หาไม่พบใน OCR)
- [ ] **ARIES+NEPTUNE** ขาด: MOON (หาไม่พบใน OCR)
- [ ] **ARIES+HADES** ขาด: MERCURY, CUPIDO, KRONOS (OCR เพี้ยนเกินกู้คืนได้อย่างมั่นใจ — ทั้งหมวดนี้คุณภาพ OCR แย่กว่าหมวดอื่นมาก)
- [ ] **ARIES+ZEUS** ขาด: CUPIDO (บรรทัดปนกับ Hades ใน OCR แยกไม่ออก)
- [ ] **ARIES+KRONOS** ขาด: MOON, SATURN (หาไม่พบใน OCR)
- [ ] **ARIES+APOLLON** ขาด: URANUS (หาไม่พบใน OCR)

### หมวด อาทิตย์ (Sun) — หน้า 44-63 (8 คู่)

- [ ] **SUN+NODE** ขาด: MARS (บรรทัด OCR หายไประหว่างช่วง Venus กับ Jupiter)
- [ ] **SUN+VENUS** ขาด: MOON, NODE, MERCURY, MARS, SATURN (OCR เพี้ยนเกินกู้คืนได้อย่างมั่นใจ)
- [ ] **SUN+SATURN** ขาด: VULKANUS (หาไม่พบใน OCR)
- [ ] **SUN+NEPTUNE** ขาด: VULKANUS (หาไม่พบใน OCR)
- [ ] **SUN+PLUTO** ขาด: CUPIDO, HADES, ZEUS, KRONOS, ADMETOS, VULKANUS, POSEIDON (OCR เพี้ยนเกินกู้คืนได้อย่างมั่นใจตั้งแต่ช่วง Neptune เป็นต้นไป)
- [ ] **SUN+HADES** ขาด: CUPIDO, ZEUS, KRONOS, APOLLON, ADMETOS, VULKANUS, POSEIDON (OCR เพี้ยนเกินกู้คืนได้อย่างมั่นใจหลังช่วง Pluto)
- [ ] **SUN+ZEUS** ขาด: ADMETOS (หาไม่พบใน OCR)
- [ ] **SUN+VULKANUS** ขาด: MARS, JUPITER (หาไม่พบใน OCR)

### หมวด อาเซนแดนต์ (Ascendant) — หน้า 64-82 (4 คู่)

- [ ] **A+SATURN** ขาด: CUPIDO (หาไม่พบใน OCR)
- [ ] **A+ZEUS** ขาด: CUPIDO (หาไม่พบใน OCR)
- [ ] **A+VULKANUS** ขาด: MARS (หาไม่พบใน OCR)
- [ ] **A+POSEIDON** ขาด: MARS (หาไม่พบใน OCR)

### หมวด จันทร์ (Moon) — หน้า 83-102 (7 คู่)

- [ ] **MOON+MERCURY** ขาด: M, ARIES, SUN (OCR ต้นย่อหน้าเสียหายจนประโยคของ 3 ปัจจัยนี้ปนกันแยกไม่ออก)
- [ ] **MOON+VENUS** ขาด: ZEUS, NEPTUNE (หาไม่พบใน OCR)
- [ ] **MOON+MARS** ขาด: URANUS (หาไม่พบใน OCR)
- [ ] **MOON+SATURN** ขาด: POSEIDON (หาไม่พบใน OCR)
- [ ] **MOON+HADES** ขาด: VULKANUS (หาไม่พบใน OCR)
- [ ] **MOON+ZEUS** ขาด: APOLLON (หาไม่พบใน OCR)
- [ ] **MOON+KRONOS** ขาด: ADMETOS (หาไม่พบใน OCR), CUPIDO (OCR รวมเข้ากับรายการของ PLUTO แยกไม่ออกว่าข้อความส่วนใดเป็นของปัจจัยใด)

### หมวด โหนด (Node) — หน้า 102-118 (8 คู่)

- [ ] **NODE+MARS** ขาด: KRONOS (หาไม่พบใน OCR)
- [ ] **NODE+SATURN** ขาด: PLUTO (หาไม่พบใน OCR)
- [ ] **NODE+URANUS** ขาด: MOON (หาไม่พบใน OCR)
- [ ] **NODE+HADES** ขาด: KRONOS (หาไม่พบใน OCR)
- [ ] **NODE+KRONOS** ขาด: A (หาไม่พบใน OCR)
- [ ] **NODE+APOLLON** ขาด: A (หาไม่พบใน OCR)
- [ ] **NODE+ADMETOS** ขาด: ARIES (หาไม่พบใน OCR)
- [ ] **NODE+VULKANUS** ขาด: MOON (หาไม่พบใน OCR)

### หมวด พุธ (Mercury) — หน้า 119-134 (2 คู่)

- [ ] **MERCURY+NEPTUNE** ขาด: NODE, PLUTO, CUPIDO (บรรทัด OCR หายไประหว่างช่วงต่างๆ)
- [ ] **MERCURY+APOLLON** ขาด: KRONOS (หาไม่พบใน OCR)

### หมวด ศุกร์ (Venus) — หน้า 135-149 (6 คู่)

- [ ] **VENUS+MARS** ขาด: POSEIDON (หาไม่พบใน OCR)
- [ ] **VENUS+SATURN** ขาด: MARS (หาไม่พบใน OCR)
- [ ] **VENUS+URANUS** ขาด: A, JUPITER (หาไม่พบใน OCR)
- [ ] **VENUS+PLUTO** ขาด: MARS (หาไม่พบใน OCR)
- [ ] **VENUS+CUPIDO** ขาด: NEPTUNE, APOLLON, ADMETOS (หาไม่พบใน OCR)
- [ ] **VENUS+HADES** ขาด: MERCURY (หาไม่พบใน OCR)

### หมวด อังคาร (Mars) — หน้า 150-164 (2 คู่)

- [ ] **MARS+KRONOS** ขาด: ARIES (หาไม่พบใน OCR)
- [ ] **MARS+ADMETOS** ขาด: VULKANUS (หาไม่พบใน OCR)

### หมวด พฤหัสบดี (Jupiter) — หน้า 165-177 (4 คู่)

- [ ] **JUPITER+URANUS** ขาด: VULKANUS (หาไม่พบใน OCR)
- [ ] **JUPITER+HADES** ขาด: KRONOS, APOLLON, VULKANUS (หาไม่พบใน OCR)
- [ ] **JUPITER+APOLLON** ขาด: NEPTUNE (หาไม่พบใน OCR)
- [ ] **JUPITER+ADMETOS** ขาด: MARS (หาไม่พบใน OCR)

### หมวด เสาร์ (Saturn) — หน้า 178-189 (5 คู่)

- [ ] **SATURN+PLUTO** ขาด: KRONOS (หาไม่พบใน OCR)
- [ ] **SATURN+HADES** ขาด: KRONOS (หาไม่พบใน OCR)
- [ ] **SATURN+ZEUS** ขาด: MOON (หาไม่พบใน OCR)
- [ ] **SATURN+ADMETOS** ขาด: KRONOS (หาไม่พบใน OCR)
- [ ] **SATURN+VULKANUS** ขาด: CUPIDO (หาไม่พบใน OCR)

### หมวด ยูเรนัส (Uranus) — หน้า 190-200 (2 คู่)

- [ ] **URANUS+KRONOS** ขาด: PLUTO (OCR damage — entry not recoverable between the Neptune and Cupido entries)
- [ ] **URANUS+ADMETOS** ขาด: VENUS (OCR damage — entry not recoverable between the Mercury and Mars entries)

### หมวด เนปจูน (Neptune) — หน้า 201-210 (2 คู่)

- [ ] **NEPTUNE+ZEUS** ขาด: SATURN (OCR damage — entry not recoverable between the Jupiter and Uranus entries)
- [ ] **NEPTUNE+ADMETOS** ขาด: VENUS, HADES (OCR damage — both entries dropped in badly merged text; VENUS between the Mercury and Mars entries, HADES between the Cupido and Zeus entries)

### หมวด พลูโต (Pluto) — หน้า 211-219 (2 คู่)

- [ ] **PLUTO+CUPIDO** ขาด: ADMETOS (OCR damage — entry not recoverable between the Apollon and Vulkanus entries)
- [ ] **PLUTO+HADES** ขาด: CUPIDO (OCR damage — entry not recoverable between the Neptune and Zeus entries)

### หมวด คิวปิโด (Cupido) — หน้า 220-227 (2 คู่)

- [ ] **CUPIDO+ZEUS** ขาด: NODE, VULKANUS (OCR damage — both entries dropped in badly merged text; NODE between the Moon and Mercury entries, VULKANUS between the Admetos and Poseidon entries)
- [ ] **CUPIDO+KRONOS** ขาด: A (OCR damage — entry not recoverable between the Sun and Moon entries)

### หมวด โครนอส (Kronos) — หน้า 241-245 (2 คู่)

- [ ] **KRONOS+ADMETOS** ขาด: MARS, NODE (OCR damage — both entries dropped in badly merged text; MARS between the Venus and Jupiter entries, NODE between the Moon and Mercury entries)
- [ ] **KRONOS+VULKANUS** ขาด: SATURN (OCR damage — entry not recoverable between the Jupiter and Uranus entries)

### หมวด อพอลโล (Apollon) — หน้า 246-249 (1 คู่)

- [ ] **APOLLON+POSEIDON** ขาด: VENUS (OCR damage — entry not recoverable between the Mercury and Mars entries)

### หมวด แอดเมโทส (Admetos) — หน้า 250-252 (1 คู่)

- [ ] **ADMETOS+POSEIDON** ขาด: APOLLON (OCR damage — the source text under this marker exactly duplicates the Kronos entry that precedes it, original content unrecoverable)

หมวดที่ไม่ปรากฏในลิสต์นี้ (Jupiter/Saturn ผ่านมาแล้ว, Hades, Zeus, Vulkanus, Poseidon) ไม่มี
third-factor ขาดเลยในคู่ที่มีอยู่ — ไม่ต้องเช็คซ้ำ

---

## สรุปจำนวน

| ไฟล์ | รายการที่ขาด |
|---|---|
| `axis_meanings.yaml` — แกน ARIES | 16 คู่ใหม่ |
| `axis_meanings.yaml` — แกน SUN | 2 คู่ (priority ต่ำ) |
| `witte_pictures.yaml` — คู่ที่ขาดทั้งคู่ | 5 คู่ × 20 third-factor/คู่ |
| `witte_pictures.yaml` — third-factor เดี่ยวในคู่ที่มีอยู่ | 75 คู่ (รวม ~100 third-factor entries) |

ไม่ต้องทำให้ครบ 100% ก็ได้ — ไฟล์เหล่านี้ใช้งานได้จริงตั้งแต่ตอนนี้แล้ว (226/231 base pairs,
4,400 รายการใน witte_pictures.yaml) รายการนี้มีไว้สำหรับตอนที่อยากลดช่องว่างที่เหลือลงเรื่อยๆ
เท่านั้น — ส่งมาเท่าที่หาได้ ทีละคู่หรือทีละหมวดก็ได้ ไม่ต้องรอให้ครบก่อนส่ง
