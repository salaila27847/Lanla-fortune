"use client";

import { useState } from "react";
import { motion } from "framer-motion";

type Props = {
  title: string;
  subtitle: string;
  cardCount: number;
  positionLabels?: string[];
  onComplete: () => void;
  nextLabel: string;
  onSkip?: () => void;
  skipLabel?: string;
};

export default function CardDrawStep({
  title,
  subtitle,
  cardCount,
  positionLabels,
  onComplete,
  nextLabel,
  onSkip,
  skipLabel,
}: Props) {
  const [flipped, setFlipped] = useState<boolean[]>(() => Array(cardCount).fill(false));

  const allFlipped = flipped.every(Boolean);

  function flipCard(index: number) {
    setFlipped((prev) => {
      const next = [...prev];
      next[index] = true;
      return next;
    });
  }

  return (
    <div className="mx-auto flex w-full max-w-md flex-col items-center gap-8 text-center">
      <div>
        <h2 className="text-xl font-semibold text-zinc-950 dark:text-zinc-50">{title}</h2>
        <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">{subtitle}</p>
      </div>

      <div className="flex flex-wrap justify-center gap-4">
        {flipped.map((isFlipped, index) => (
          <div key={index} className="flex flex-col items-center gap-1.5">
            <motion.button
              type="button"
              onClick={() => flipCard(index)}
              disabled={isFlipped}
              aria-label={isFlipped ? `ไพ่ใบที่ ${index + 1} เปิดแล้ว` : `เปิดไพ่ใบที่ ${index + 1}`}
              className="relative h-36 w-24 [perspective:1000px]"
              whileTap={{ scale: 0.95 }}
            >
              <motion.div
                aria-hidden="true"
                className="absolute inset-0 rounded-xl [transform-style:preserve-3d]"
                animate={{ rotateY: isFlipped ? 180 : 0 }}
                transition={{ duration: 0.6 }}
              >
                <div className="absolute inset-0 flex items-center justify-center rounded-xl border border-zinc-300 bg-gradient-to-br from-zinc-800 to-zinc-950 text-2xl [backface-visibility:hidden] dark:border-zinc-700">
                  ✦
                </div>
                <div className="absolute inset-0 flex items-center justify-center rounded-xl border border-zinc-300 bg-white text-sm text-zinc-500 [backface-visibility:hidden] [transform:rotateY(180deg)] dark:border-zinc-700 dark:bg-zinc-100 dark:text-zinc-600">
                  เปิดแล้ว
                </div>
              </motion.div>
            </motion.button>
            {positionLabels?.[index] && (
              <span className="text-xs text-zinc-500 dark:text-zinc-400">
                {positionLabels[index]}
              </span>
            )}
          </div>
        ))}
      </div>

      <button
        type="button"
        disabled={!allFlipped}
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
