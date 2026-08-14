"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";

type Props = {
  title: string;
  subtitle: string;
  cardCount: number;
  /** Total cards in the deck spread out for picking (e.g. 78 tarot, 88 oracle). */
  deckSize: number;
  /** How many overlapping rows to arrange the deck into (3-4 looks best). */
  rows: number;
  /** Labels in *pick order* (1st card picked, 2nd, ...) — not tied to a
   * fixed position in the spread, since the user picks freely. */
  positionLabels?: string[];
  onComplete: () => void;
  nextLabel: string;
  onSkip?: () => void;
  skipLabel?: string;
};

function shuffledDeckOrder(deckSize: number): number[] {
  const order = Array.from({ length: deckSize }, (_, i) => i);
  for (let i = order.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [order[i], order[j]] = [order[j], order[i]];
  }
  return order;
}

function splitIntoRows(order: number[], rows: number): number[][] {
  const perRow = Math.ceil(order.length / rows);
  const result: number[][] = [];
  for (let r = 0; r < rows; r++) {
    const row = order.slice(r * perRow, (r + 1) * perRow);
    if (row.length > 0) result.push(row);
  }
  return result;
}

const CARD_WIDTH = 26;
const CARD_HEIGHT = 39;
// Overlap (in px) must stay comfortably under half of each dimension —
// otherwise a card's own geometric center falls inside the region the
// next (higher z-index) card/row covers, and a tap/click aimed dead
// center hits the neighbor instead of the intended card.
const OVERLAP_X = 9;
const OVERLAP_Y = 13;

export default function CardDrawStep({
  title,
  subtitle,
  cardCount,
  deckSize,
  rows,
  positionLabels,
  onComplete,
  nextLabel,
  onSkip,
  skipLabel,
}: Props) {
  // Shuffled once per mount — the deck the user sees is "fresh" each time
  // this step is entered. All cards look identical face-down, so which
  // slot ends up where is cosmetic; the actual card drawn is decided
  // server-side independent of which spread position was tapped.
  const [deckOrder] = useState(() => shuffledDeckOrder(deckSize));
  const rowsOfIndices = useMemo(() => splitIntoRows(deckOrder, rows), [deckOrder, rows]);
  const [pickedOrder, setPickedOrder] = useState<number[]>([]);

  const isDone = pickedOrder.length >= cardCount;

  function pickCard(deckIndex: number) {
    if (isDone || pickedOrder.includes(deckIndex)) return;
    setPickedOrder((prev) => [...prev, deckIndex]);
  }

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col items-center gap-6 text-center">
      <div>
        <h2 className="text-xl font-semibold text-zinc-950 dark:text-zinc-50">{title}</h2>
        <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">{subtitle}</p>
      </div>

      {positionLabels ? (
        <div className="flex flex-wrap justify-center gap-2">
          {positionLabels.map((label, i) => (
            <span
              key={`${label}-${i}`}
              className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                i < pickedOrder.length
                  ? "border-zinc-950 bg-zinc-950 text-zinc-50 dark:border-zinc-50 dark:bg-zinc-50 dark:text-zinc-950"
                  : "border-zinc-300 text-zinc-500 dark:border-zinc-700 dark:text-zinc-400"
              }`}
            >
              {label}
            </span>
          ))}
        </div>
      ) : (
        <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
          เลือกแล้ว {pickedOrder.length} / {cardCount} ใบ
        </p>
      )}

      <div className="w-full overflow-x-auto py-2">
        <div className="flex w-fit flex-col items-start mx-auto">
          {rowsOfIndices.map((rowIndices, rowIdx) => (
            <div
              key={rowIdx}
              className="flex"
              style={{ marginTop: rowIdx === 0 ? 0 : -OVERLAP_Y, zIndex: rowIdx }}
            >
              {rowIndices.map((deckIndex, i) => {
                const pickNumber = pickedOrder.indexOf(deckIndex) + 1;
                const isPicked = pickNumber > 0;
                return (
                  <motion.button
                    key={deckIndex}
                    type="button"
                    onClick={() => pickCard(deckIndex)}
                    disabled={isPicked || isDone}
                    aria-label={isPicked ? `ไพ่ที่เลือกลำดับ ${pickNumber}` : "แตะเพื่อเลือกไพ่ใบนี้"}
                    className="relative shrink-0 [perspective:600px]"
                    style={{
                      width: CARD_WIDTH,
                      height: CARD_HEIGHT,
                      marginLeft: i === 0 ? 0 : -OVERLAP_X,
                      zIndex: i,
                    }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <motion.div
                      aria-hidden="true"
                      className="absolute inset-0 rounded-[3px] [transform-style:preserve-3d]"
                      animate={{ rotateY: isPicked ? 180 : 0 }}
                      transition={{ duration: 0.45 }}
                    >
                      <div className="absolute inset-0 flex items-center justify-center rounded-[3px] border border-zinc-300 bg-gradient-to-br from-zinc-800 to-zinc-950 text-[10px] text-zinc-400 [backface-visibility:hidden] dark:border-zinc-700">
                        ✦
                      </div>
                      <div className="absolute inset-0 flex items-center justify-center rounded-[3px] border border-zinc-300 bg-white text-[10px] font-semibold text-zinc-700 [backface-visibility:hidden] [transform:rotateY(180deg)] dark:border-zinc-700 dark:bg-zinc-100 dark:text-zinc-800">
                        {pickNumber || ""}
                      </div>
                    </motion.div>
                  </motion.button>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      <p className="text-xs text-zinc-500 dark:text-zinc-400">
        ไพ่ทั้งสำรับถูกสับเรียบร้อยแล้ว แตะไพ่ที่รู้สึกดึงดูดใจให้ครบ {cardCount} ใบ
      </p>

      <button
        type="button"
        disabled={!isDone}
        onClick={onComplete}
        className="rounded-full bg-zinc-950 px-6 py-3 text-sm font-medium text-zinc-50 transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-40 dark:bg-zinc-50 dark:text-zinc-950 dark:hover:bg-zinc-200"
      >
        {nextLabel}
      </button>

      {onSkip && (
        <button
          type="button"
          onClick={onSkip}
          className="text-sm text-zinc-500 underline-offset-2 hover:underline dark:text-zinc-400"
        >
          {skipLabel}
        </button>
      )}
    </div>
  );
}
