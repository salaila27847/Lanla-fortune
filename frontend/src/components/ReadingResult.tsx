"use client";

import { useState } from "react";
import CardDrawStep, { type DrawableCard } from "@/components/CardDrawStep";
import { randomOracleCount } from "@/lib/random";
import {
  drawOracleDeck,
  getFollowUpReading,
  type FineTimingHit,
  type ForecastResponse,
  type HousePlacementResult,
  type OracleDeck,
  type PictureResult,
  type SynthesisOutput,
} from "@/lib/api";

type Props = {
  result: SynthesisOutput;
  onRestart: () => void;
};

const ENGINE_LABELS: Record<string, string> = {
  uranian: "โหราศาสตร์ยูเรเนียน",
  tarot: "ไพ่ทาโรต์",
  oracle: "ไพ่ออราเคิล",
};

const ENGINES = ["uranian", "tarot", "oracle"] as const;

type Tab = "overview" | "uranian" | "tarot" | "oracle" | "forecast";

type ForecastSection = "solar_arc" | "transit" | "lunar_return" | "relocation";

const FORECAST_SECTION_LABELS: Record<ForecastSection, string> = {
  solar_arc: "Solar Arc",
  transit: "Transit",
  lunar_return: "Lunar Return",
  relocation: "Relocation",
};

function availableForecastSections(forecast: ForecastResponse): ForecastSection[] {
  return (Object.keys(FORECAST_SECTION_LABELS) as ForecastSection[]).filter((key) => forecast[key]);
}

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

function FineTimingList({ hits }: { hits: FineTimingHit[] }) {
  if (hits.length === 0) return null;
  return (
    <div className="flex flex-col gap-2">
      <h4 className="text-xs font-semibold text-zinc-500 dark:text-zinc-400">
        จุดเวลาที่แม่นเป็นพิเศษ (จาน 22.5°)
      </h4>
      <ul className="space-y-1">
        {hits.map((hit, i) => (
          <li
            key={i}
            className="rounded-lg border border-zinc-200 px-3 py-2 text-sm text-zinc-700 dark:border-zinc-800 dark:text-zinc-300"
          >
            {hit.label} <span className="text-zinc-400 dark:text-zinc-500">({hit.orb.toFixed(2)}°)</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function HousePlacementTable({ placements }: { placements: HousePlacementResult[] }) {
  if (placements.length === 0) return null;
  return (
    <div className="flex flex-col gap-2">
      <h4 className="text-xs font-semibold text-zinc-500 dark:text-zinc-400">ตำแหน่งเรือน (ระบบเรือนเมริเดียน)</h4>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-zinc-200 text-xs text-zinc-500 dark:border-zinc-800 dark:text-zinc-400">
              <th className="py-2 pr-4 font-medium">ปัจจัย</th>
              <th className="py-2 font-medium">เรือน</th>
            </tr>
          </thead>
          <tbody>
            {placements.map((placement, i) => (
              <tr key={i} className="border-b border-zinc-100 dark:border-zinc-900">
                <td className="py-2 pr-4 text-zinc-800 dark:text-zinc-200">{placement.label}</td>
                <td className="py-2 text-zinc-500 dark:text-zinc-400">{placement.house_number}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ForecastSectionContent({
  section,
  forecast,
}: {
  section: ForecastSection;
  forecast: ForecastResponse;
}) {
  if (section === "solar_arc" && forecast.solar_arc) {
    return (
      <div className="flex flex-col gap-2">
        <h3 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">
          Solar Arc — ส่วนโค้งสุริยะ {forecast.solar_arc.arc_degrees.toFixed(2)}°
        </h3>
        <PictureTable pictures={forecast.solar_arc.pictures} />
        <HousePlacementTable placements={forecast.solar_arc.house_placements} />
      </div>
    );
  }
  if (section === "transit" && forecast.transit) {
    return (
      <div className="flex flex-col gap-2">
        <h3 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">Transit — ดาวโคจรผ่าน</h3>
        <PictureTable pictures={forecast.transit.pictures} />
        <FineTimingList hits={forecast.transit.fine_timing} />
        <HousePlacementTable placements={forecast.transit.house_placements} />
      </div>
    );
  }
  if (section === "lunar_return" && forecast.lunar_return) {
    return (
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
    );
  }
  if (section === "relocation" && forecast.relocation) {
    return (
      <div className="flex flex-col gap-2">
        <h3 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">Relocation — ดวงย้ายถิ่น</h3>
        <p className="text-sm text-zinc-800 dark:text-zinc-200">
          ลัคนาใหม่ {forecast.relocation.ascendant.toFixed(2)}° · มิเดียมใหม่{" "}
          {forecast.relocation.midheaven.toFixed(2)}°
        </p>
        <HousePlacementTable placements={forecast.relocation.house_placements} />
      </div>
    );
  }
  return null;
}

function ForecastTab({ forecast }: { forecast: ForecastResponse }) {
  const sections = availableForecastSections(forecast);
  const [active, setActive] = useState<ForecastSection>(sections[0]);

  if (sections.length === 0) return null;

  return (
    <div className="flex flex-col gap-6">
      {sections.length > 1 && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-zinc-500 dark:text-zinc-400">ข้ามไปดู:</span>
          {sections.map((section) => (
            <button
              key={section}
              type="button"
              onClick={() => setActive(section)}
              className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                active === section
                  ? "border-zinc-950 bg-zinc-950 text-zinc-50 dark:border-zinc-50 dark:bg-zinc-50 dark:text-zinc-950"
                  : "border-zinc-300 text-zinc-600 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-400 dark:hover:bg-zinc-800"
              }`}
            >
              {FORECAST_SECTION_LABELS[section]}
            </button>
          ))}
        </div>
      )}
      <ForecastSectionContent section={active} forecast={forecast} />
    </div>
  );
}

type FollowUpStage = "idle" | "deck-loading" | "drawing" | "loading";

export default function ReadingResult({ result, onRestart }: Props) {
  const [activeResult, setActiveResult] = useState(result);
  const [tab, setTab] = useState<Tab>("overview");

  const [followUpStage, setFollowUpStage] = useState<FollowUpStage>("idle");
  const [followUpQuestion, setFollowUpQuestion] = useState("");
  const [followUpCardCount, setFollowUpCardCount] = useState(0);
  const [followUpDeck, setFollowUpDeck] = useState<OracleDeck | null>(null);
  const [followUpError, setFollowUpError] = useState("");

  const forecast = activeResult.forecast;
  const hasForecast = Boolean(forecast && availableForecastSections(forecast).length > 0);
  const engineTabs = ENGINES.filter((engine) => activeResult.per_engine_breakdown[engine]);

  const tabs: { id: Tab; label: string }[] = [
    { id: "overview", label: "ภาพรวม" },
    ...engineTabs.map((engine) => ({ id: engine as Tab, label: ENGINE_LABELS[engine] })),
    ...(hasForecast ? [{ id: "forecast" as const, label: "การพยากรณ์ล่วงหน้า" }] : []),
  ];

  // Fetches a real shuffled oracle deck before showing the card grid, so
  // the position the user taps reveals a genuine pick — same reasoning
  // as the initial reading's draw steps (see reading/page.tsx).
  async function startFollowUpDraw() {
    if (!followUpQuestion.trim()) return;
    setFollowUpError("");
    setFollowUpCardCount(randomOracleCount());
    setFollowUpStage("deck-loading");
    try {
      const deck = await drawOracleDeck();
      setFollowUpDeck(deck);
      setFollowUpStage("drawing");
    } catch {
      setFollowUpError("ไม่สามารถจั่วไพ่ออราเคิลได้ในขณะนี้ กรุณาลองใหม่อีกครั้ง");
      setFollowUpStage("idle");
    }
  }

  async function submitFollowUp(picks: string[]) {
    setFollowUpStage("loading");
    try {
      const updated = await getFollowUpReading({
        previous: activeResult,
        question: followUpQuestion.trim(),
        oracle_picks: picks,
      });
      setActiveResult(updated);
      setTab("overview");
      setFollowUpQuestion("");
      setFollowUpDeck(null);
      setFollowUpStage("idle");
    } catch {
      setFollowUpError("ไม่สามารถถามเพิ่มเติมได้ในขณะนี้ กรุณาลองใหม่อีกครั้ง");
      setFollowUpStage("idle");
    }
  }

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
            {activeResult.final_reading}
          </p>

          {activeResult.convergent_themes.length > 0 && (
            <div>
              <h3 className="mb-2 text-sm font-semibold text-zinc-700 dark:text-zinc-300">
                จุดร่วมของแต่ละศาสตร์
              </h3>
              <div className="flex flex-wrap gap-2">
                {activeResult.convergent_themes.map((theme) => (
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

          {activeResult.divergent_notes.length > 0 && (
            <div>
              <h3 className="mb-2 text-sm font-semibold text-zinc-700 dark:text-zinc-300">
                จุดที่แต่ละศาสตร์มองต่างกัน
              </h3>
              <ul className="list-inside list-disc space-y-1 text-sm text-zinc-600 dark:text-zinc-400">
                {activeResult.divergent_notes.map((note, i) => (
                  <li key={i}>{note}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {ENGINES.map(
        (engine) =>
          tab === engine &&
          activeResult.per_engine_breakdown[engine] && (
            <div key={engine} className="flex flex-col gap-4">
              {engine === "oracle" && activeResult.oracle_question && (
                <p className="rounded-lg bg-zinc-100 px-3 py-2 text-sm italic text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
                  คำถามที่ถาม: “{activeResult.oracle_question}”
                </p>
              )}
              <p className="text-base leading-7 text-zinc-800 dark:text-zinc-200">
                {activeResult.per_engine_breakdown[engine]?.summary}
              </p>
              <div className="flex flex-wrap gap-2">
                {activeResult.per_engine_breakdown[engine]?.themes.map((theme) => (
                  <span
                    key={theme}
                    className="rounded-full bg-zinc-100 px-3 py-1 text-xs text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
                  >
                    {theme}
                  </span>
                ))}
              </div>
              <ul className="space-y-3">
                {activeResult.per_engine_breakdown[engine]?.raw_findings.map((finding, i) => (
                  <li
                    key={i}
                    className="rounded-lg border border-zinc-200 p-3 text-sm dark:border-zinc-800"
                  >
                    <p className="font-medium text-zinc-800 dark:text-zinc-200">{finding.label}</p>
                    <p className="mt-1 text-zinc-600 dark:text-zinc-400">{finding.meaning}</p>
                    {finding.voice && (
                      <p className="mt-2 border-l-2 border-zinc-300 pl-3 italic text-zinc-500 dark:border-zinc-700 dark:text-zinc-400">
                        “{finding.voice}”
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ),
      )}

      {tab === "forecast" && forecast && <ForecastTab forecast={forecast} />}

      <div className="rounded-xl border border-zinc-200 p-5 dark:border-zinc-800">
        <h3 className="mb-3 text-sm font-semibold text-zinc-700 dark:text-zinc-300">
          มีคำถามเพิ่มเติมไหม?
        </h3>

        {followUpStage === "idle" && (
          <div className="flex flex-col gap-3">
            <textarea
              value={followUpQuestion}
              onChange={(e) => setFollowUpQuestion(e.target.value)}
              rows={3}
              maxLength={500}
              placeholder="ถามต่อจากคำทำนายนี้..."
              aria-label="คำถามเพิ่มเติม"
              className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-950 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
            />
            <button
              type="button"
              disabled={!followUpQuestion.trim()}
              onClick={startFollowUpDraw}
              className="mx-auto rounded-full bg-zinc-950 px-6 py-2.5 text-sm font-medium text-zinc-50 transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-40 dark:bg-zinc-50 dark:text-zinc-950 dark:hover:bg-zinc-200"
            >
              ถามเพิ่ม
            </button>
            {followUpError && (
              <p className="text-center text-sm text-red-600 dark:text-red-400">{followUpError}</p>
            )}
          </div>
        )}

        {followUpStage === "deck-loading" && (
          <div className="flex flex-col items-center gap-3 py-4 text-center">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-950 dark:border-zinc-700 dark:border-t-zinc-50" />
            <p className="text-sm text-zinc-600 dark:text-zinc-400">กำลังสับไพ่ออราเคิล...</p>
          </div>
        )}

        {followUpStage === "drawing" && followUpDeck && (
          <CardDrawStep
            title="จั่วไพ่ออราเคิลเพิ่มเติม"
            subtitle={`ระบบสุ่มไพ่ออราเคิล ${followUpCardCount} ใบให้คุณเลือกจากทั้งสำรับ`}
            cardCount={followUpCardCount}
            cards={followUpDeck.cards.map((c): DrawableCard => ({ id: c.card_id, label: c.name_th }))}
            rows={4}
            nextLabel="ดูคำทำนาย"
            onComplete={(picked) => void submitFollowUp(picked.map((p) => p.id))}
          />
        )}

        {followUpStage === "loading" && (
          <div className="flex flex-col items-center gap-3 py-4 text-center">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-950 dark:border-zinc-700 dark:border-t-zinc-50" />
            <p className="text-sm text-zinc-600 dark:text-zinc-400">กำลังสังเคราะห์คำทำนายเพิ่มเติม...</p>
          </div>
        )}
      </div>

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
