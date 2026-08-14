"use client";

import { useState } from "react";

type Props = {
  title: string;
  subtitle: string;
  submitLabel: string;
  onSubmit: (question: string) => void;
};

export default function OracleQuestionForm({ title, subtitle, submitLabel, onSubmit }: Props) {
  const [question, setQuestion] = useState("");
  const trimmed = question.trim();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (trimmed) onSubmit(trimmed);
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mx-auto flex w-full max-w-md flex-col gap-4 text-center"
    >
      <div>
        <h2 className="text-xl font-semibold text-zinc-950 dark:text-zinc-50">{title}</h2>
        <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">{subtitle}</p>
      </div>

      <textarea
        required
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        rows={4}
        maxLength={500}
        placeholder="เช่น ความรักของฉันในช่วงนี้จะเป็นอย่างไร"
        aria-label="คำถามของคุณ"
        className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-950 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
      />

      <button
        type="submit"
        disabled={!trimmed}
        className="mx-auto rounded-full bg-zinc-950 px-6 py-3 text-sm font-medium text-zinc-50 transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-40 dark:bg-zinc-50 dark:text-zinc-950 dark:hover:bg-zinc-200"
      >
        {submitLabel}
      </button>
    </form>
  );
}
