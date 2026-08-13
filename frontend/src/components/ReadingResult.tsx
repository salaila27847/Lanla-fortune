"use client";

import { useState } from "react";
import type { ForecastResponse, PictureResult, SynthesisOutput } from "@/lib/api";

type Props = {
  result: SynthesisOutput;
  forecast?: ForecastResponse | null;
  onRestart: () => void;
};

const ENGINE_LABELS: Record<string, string> = {
  uranian: "โหราศาสตร์ยูเรเนียน",
  tarot: "ไพ่ทาโรต์",
  oracle: "ไพ่ออราเคิล",
};

type Tab = "overview" | "uranian" | "tarot" | "oracle" | "forecast";

function PictureTable({ pictures }: { pictures: PictureResult[] }) {
  if (pictures.length === 0) {
    return <p className="text-sm text-zinc-500 dark:text-zinc-400">ไม่พบ planetary picture ในช่วงนี้</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-zinc-200 text-xs text-zinc-500 dark:border-zinc-800 dark:text-zinc-400">
            <th className="py-2 pr-4 font-medium">Picture</th>
            <th className="py-2 pr-4 font-medium">ประเภท</th>
            <th className="py-2 font-medium">Orb</th>
          </tr>
        </thead>
        <tbody>
          {pictures.map((picture, i) => (
            <tr key={i} className="border-b border-zinc-100 dark:border-zinc-900">
              <td className="py-2 pr-4 text-zinc-800 dark:text-zinc-200">{picture.label}</td>
              <td className="py-2 pr-4 text-zinc-500 dark:text-zinc-400">
                {picture.type === "type1" ? "Type I" : "Type II"}
              </td>
              <td className="py-2 text-zinc-500 dark:text-zinc-400">{picture.orb.toFixed(2)}°</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function ReadingResult({ result, forecast, onRestart }: Props) {
  const [tab, setTab] = useState<Tab>("overview");

  const hasForecast = Boolean(
    forecast && (forecast.solar_arc || forecast.transit || forecast.lunar_return || forecast.relocation),
  );

  const tabs: { id: Tab; label: string }[] = [
    { id: "overview", label: "ภาพรวม" },
    { id: "uranian", label: ENGINE_LABELS.uranian },
    { id: "tarot", label: ENGINE_LABELS.tarot },
    { id: "oracle", label: ENGINE_LABELS.oracle },
    ...(hasForecast ? [{ id: "forecast" as const, label: "การพยากรณ์ล่วงหน้า" }] : []),
  ];

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-8">
      <div className="flex flex-wrap gap-2 border-b border-zinc-200 pb-2 dark:border-zinc-800">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
              tab === t.id
                ? "bg-zinc-950 text-zinc-50 dark:bg-zinc-50 dark:text-zinc-950"
                : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <div className="flex flex-col gap-6">
          <p className="whitespace-pre-line text-base leading-8 text-zinc-800 dark:text-zinc-200">
            {result.final_reading}
          </p>

          {result.convergent_themes.length > 0 && (
            <div>
              <h3 className="mb-2 text-sm font-semibold text-zinc-700 dark:text-zinc-300">
                จุดร่วมของ 3 ศาสตร์
              </h3>
              <div className="flex flex-wrap gap-2">
                {result.convergent_themes.map((theme) => (
                  <span
                    key={theme}
                    className="rounded-full bg-zinc-100 px-3 py-1 text-xs text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
                  >
                    {theme}
                  </span>
                ))}
              </div>
            </div>
          )}

          {result.divergent_notes.length > 0 && (
            <div>
              <h3 className="mb-2 text-sm font-semibold text-zinc-700 dark:text-zinc-300">
                จุดที่แต่ละศาสตร์มองต่างกัน
              </h3>
              <ul className="list-inside list-disc space-y-1 text-sm text-zinc-600 dark:text-zinc-400">
                {result.divergent_notes.map((note, i) => (
                  <li key={i}>{note}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {(["uranian", "tarot", "oracle"] as const).map(
        (engine) =>
          tab === engine && (
            <div key={engine} className="flex flex-col gap-4">
              <p className="text-base leading-7 text-zinc-800 dark:text-zinc-200">
                {result.per_engine_breakdown[engine]?.summary}
              </p>
              <div className="flex flex-wrap gap-2">
                {result.per_engine_breakdown[engine]?.themes.map((theme) => (
                  <span
                    key={theme}
                    className="rounded-full bg-zinc-100 px-3 py-1 text-xs text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
                  >
                    {theme}
                  </span>
                ))}
              </div>
              <ul className="space-y-3">
                {result.per_engine_breakdown[engine]?.raw_findings.map((finding, i) => (
                  <li
                    key={i}
                    className="rounded-lg border border-zinc-200 p-3 text-sm dark:border-zinc-800"
                  >
                    <p className="font-medium text-zinc-800 dark:text-zinc-200">{finding.label}</p>
                    <p className="mt-1 text-zinc-600 dark:text-zinc-400">{finding.meaning}</p>
                  </li>
                ))}
              </ul>
            </div>
          ),
      )}

      {tab === "forecast" && forecast && (
        <div className="flex flex-col gap-8">
          {forecast.solar_arc && (
            <div className="flex flex-col gap-2">
              <h3 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">
                Solar Arc — ส่วนโค้งสุริยะ {forecast.solar_arc.arc_degrees.toFixed(2)}°
              </h3>
              <PictureTable pictures={forecast.solar_arc.pictures} />
            </div>
          )}

          {forecast.transit && (
            <div className="flex flex-col gap-2">
              <h3 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">Transit — ดาวโคจรผ่าน</h3>
              <PictureTable pictures={forecast.transit.pictures} />
            </div>
          )}

          {forecast.lunar_return && (
            <div className="flex flex-col gap-2">
              <h3 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">
                Lunar Return — จันทร์คืนตำแหน่งเกิด
              </h3>
              <p className="text-sm text-zinc-800 dark:text-zinc-200">
                {new Date(forecast.lunar_return.return_at).toLocaleString("th-TH", {
                  dateStyle: "long",
                  timeStyle: "short",
                })}
              </p>
            </div>
          )}

          {forecast.relocation && (
            <div className="flex flex-col gap-2">
              <h3 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">
                Relocation — ดวงย้ายถิ่น
              </h3>
              <p className="text-sm text-zinc-800 dark:text-zinc-200">
                ลัคนาใหม่ {forecast.relocation.ascendant.toFixed(2)}° · มิเดียมใหม่{" "}
                {forecast.relocation.midheaven.toFixed(2)}°
              </p>
            </div>
          )}
        </div>
      )}

      <button
        type="button"
        onClick={onRestart}
        className="mx-auto mt-4 rounded-full border border-zinc-300 px-6 py-2.5 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
      >
        ดูดวงอีกครั้ง
      </button>
    </div>
  );
}
