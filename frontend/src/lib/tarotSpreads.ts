// Mirrors backend/app/knowledge_base/tarot/spreads.yaml — id, positions
// (in draw order), and card count must stay in sync with that file, since
// the backend zips these same positions against the cards it draws.
export type TarotSpreadInfo = {
  id: string;
  name_th: string;
  description_th: string;
  positions: string[];
};

export const TAROT_SPREADS: TarotSpreadInfo[] = [
  {
    id: "single_card",
    name_th: "ไพ่ใบเดียว",
    description_th: "คำตอบตรงประเด็น เหมาะกับคำถามที่ต้องการโฟกัสเดียว",
    positions: ["คำตอบ"],
  },
  {
    id: "three_card",
    name_th: "อดีต–ปัจจุบัน–อนาคต",
    description_th: "ภาพรวมสถานการณ์ตามช่วงเวลา",
    positions: ["อดีต", "ปัจจุบัน", "อนาคต"],
  },
  {
    id: "situation_advice",
    name_th: "สถานการณ์–อุปสรรค–คำแนะนำ",
    description_th: "เจาะปัญหาตรงหน้าและแนวทางแก้ไข",
    positions: ["สถานการณ์", "อุปสรรค", "คำแนะนำ"],
  },
  {
    id: "relationship_five",
    name_th: "ความสัมพันธ์ 5 ใบ",
    description_th: "มุมมองความสัมพันธ์ระหว่างคุณกับอีกฝ่าย",
    positions: ["คุณ", "อีกฝ่าย", "ความสัมพันธ์ตอนนี้", "ความท้าทาย", "แนวโน้ม"],
  },
  {
    id: "celtic_cross",
    name_th: "กากบาทเซลติก",
    description_th: "เจาะลึกภาพรวมชีวิตแบบครบทุกมิติ (10 ใบ)",
    positions: [
      "สถานการณ์ปัจจุบัน",
      "อุปสรรค",
      "รากฐาน / อดีตไกล",
      "อดีตใกล้",
      "เป้าหมาย / จุดสูงสุด",
      "อนาคตอันใกล้",
      "ตัวคุณเอง",
      "สิ่งแวดล้อมรอบตัว",
      "ความหวังและความกลัว",
      "ผลลัพธ์สุดท้าย",
    ],
  },
];
