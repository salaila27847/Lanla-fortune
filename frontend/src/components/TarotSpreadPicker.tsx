"use client";

import { TAROT_SPREADS, type TarotSpreadInfo } from "@/lib/tarotSpreads";

type Props = {
  onSelect: (spread: TarotSpreadInfo) => void;
  onSkip: () => void;
};

export default function TarotSpreadPicker({ onSelect, onSkip }: Props) {
  return (
    <div className="mx-auto flex w-full max-w-lg flex-col items-center gap-8 text-center">
      <div>
        <h2 className="text-xl font-semibold text-zinc-950 dark:text-zinc-50">
          เลือกรูปแบบไพ่ทาโรต์
        </h2>
        <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
          เลือกเลย์เอาท์ที่ตรงกับคำถามของคุณ
        </p>
      </div>

      <div className="grid w-full gap-3 sm:grid-cols-2">
        {TAROT_SPREADS.map((spread) => (
          <button
            key={spread.id}
            type="button"
            onClick={() => onSelect(spread)}
            className="flex flex-col items-start gap-1 rounded-xl border border-zinc-300 p-4 text-left transition-colors hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-800"
          >
            <span className="text-sm font-semibold text-zinc-950 dark:text-zinc-50">
              {spread.name_th}
            </span>
            <span className="text-xs text-zinc-500 dark:text-zinc-400">
              {spread.positions.length} ใบ · {spread.description_th}
            </span>
          </button>
        ))}
      </div>

      <button
        type="button"
        onClick={onSkip}
        className="text-sm text-zinc-500 underline-offset-2 hover:underline dark:text-zinc-400"
      >
        ข้ามไพ่ทาโรต์ (ไม่ใช้ศาสตร์นี้)
      </button>
    </div>
  );
}
