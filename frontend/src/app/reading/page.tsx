"use client";

import { useState } from "react";
import BirthDataForm from "@/components/BirthDataForm";
import TarotSpreadPicker from "@/components/TarotSpreadPicker";
import OracleQuestionForm from "@/components/OracleQuestionForm";
import CardDrawStep, { type DrawableCard } from "@/components/CardDrawStep";
import ReadingResult from "@/components/ReadingResult";
import { randomOracleCount } from "@/lib/random";
import {
  drawOracleDeck,
  drawTarotDeck,
  getReading,
  ReadingRequestError,
  type BirthData,
  type ForecastOptions,
  type OracleDeck,
  type SynthesisOutput,
  type TarotDeck,
} from "@/lib/api";
import type { TarotSpreadInfo } from "@/lib/tarotSpreads";

type Step =
  | "birth-data"
  | "tarot-spread"
  | "tarot-draw"
  | "oracle-question"
  | "oracle-draw"
  | "loading"
  | "result"
  | "error";

// What to retry when the "loading" step's fetch fails — reconstructed from
// state already on hand rather than stashing a closure in useState.
type PendingAction = "tarot-deck" | "oracle-deck" | "reading";

export default function ReadingPage() {
  const [step, setStep] = useState<Step>("birth-data");
  const [loadingMessage, setLoadingMessage] = useState("");
  const [pendingAction, setPendingAction] = useState<PendingAction>("reading");

  const [birthData, setBirthData] = useState<BirthData | null>(null);
  const [forecastOptions, setForecastOptions] = useState<ForecastOptions>({});
  const [uranianSkipped, setUranianSkipped] = useState(false);

  const [tarotSpread, setTarotSpread] = useState<TarotSpreadInfo | null>(null);
  const [tarotSkipped, setTarotSkipped] = useState(false);
  const [tarotDeck, setTarotDeck] = useState<TarotDeck | null>(null);
  const [tarotPicks, setTarotPicks] = useState<{ card_id: string; reversed: boolean }[]>([]);

  const [oracleQuestion, setOracleQuestion] = useState<string | null>(null);
  const [oracleCount, setOracleCount] = useState<number | null>(null);
  const [oracleDeck, setOracleDeck] = useState<OracleDeck | null>(null);
  const [oraclePicks, setOraclePicks] = useState<string[]>([]);
  const [oracleSkipped, setOracleSkipped] = useState(false);

  const [result, setResult] = useState<SynthesisOutput | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [isInputError, setIsInputError] = useState(false);

  function restart() {
    setStep("birth-data");
    setBirthData(null);
    setForecastOptions({});
    setUranianSkipped(false);
    setTarotSpread(null);
    setTarotSkipped(false);
    setTarotDeck(null);
    setTarotPicks([]);
    setOracleQuestion(null);
    setOracleCount(null);
    setOracleDeck(null);
    setOraclePicks([]);
    setOracleSkipped(false);
    setResult(null);
    setErrorMessage("");
    setIsInputError(false);
  }

  // Fetches a real shuffled tarot deck before showing the card grid, so
  // the position the user taps reveals a genuine pick (see CLAUDE.md's
  // oracle/tarot "user really picks" decision) instead of a cosmetic one
  // assigned after the fact.
  async function enterTarotDraw(spread: TarotSpreadInfo) {
    setTarotSpread(spread);
    setTarotSkipped(false);
    setPendingAction("tarot-deck");
    setLoadingMessage("กำลังสับไพ่ทาโรต์...");
    setStep("loading");
    try {
      const deck = await drawTarotDeck(spread.id);
      setTarotDeck(deck);
      setStep("tarot-draw");
    } catch {
      setErrorMessage("ไม่สามารถจั่วไพ่ทาโรต์ได้ในขณะนี้ กรุณาลองใหม่อีกครั้ง");
      setIsInputError(false);
      setStep("error");
    }
  }

  async function enterOracleDraw() {
    setOracleCount(randomOracleCount());
    setPendingAction("oracle-deck");
    setLoadingMessage("กำลังสับไพ่ออราเคิล...");
    setStep("loading");
    try {
      const deck = await drawOracleDeck();
      setOracleDeck(deck);
      setStep("oracle-draw");
    } catch {
      setErrorMessage("ไม่สามารถจั่วไพ่ออราเคิลได้ในขณะนี้ กรุณาลองใหม่อีกครั้ง");
      setIsInputError(false);
      setStep("error");
    }
  }

  // Oracle is the only discipline that always has a card count (system
  // randomized, 3-9) — but whether it also needs a question first depends
  // on whether it's the *only* discipline in play (both others skipped).
  function enterOracleStage(skippedUranian: boolean, skippedTarot: boolean) {
    if (skippedUranian && skippedTarot) {
      setStep("oracle-question");
    } else {
      void enterOracleDraw();
    }
  }

  // `picks` is accepted as a parameter (defaulting to the oraclePicks
  // state, for the skip/retry paths) rather than always reading state,
  // because the oracle-draw step's onComplete calls setOraclePicks(...)
  // and fetchReading(...) synchronously in the same handler — state
  // updates don't apply until the next render, so reading `oraclePicks`
  // here right after setting it would still see the old (empty) value.
  async function fetchReading(skipOracle: boolean, picks: string[] = oraclePicks) {
    setOracleSkipped(skipOracle);
    if (!skipOracle) setOraclePicks(picks);
    setPendingAction("reading");
    setLoadingMessage("กำลังสังเคราะห์คำทำนาย...");
    setStep("loading");
    try {
      const reading = await getReading({
        ...(uranianSkipped ? {} : { birth_data: birthData as BirthData, ...forecastOptions }),
        ...(tarotSkipped
          ? {}
          : { tarot: { spread: (tarotSpread as TarotSpreadInfo).id, picks: tarotPicks } }),
        ...(skipOracle
          ? {}
          : {
              oracle: {
                picks,
                ...(oracleQuestion ? { question: oracleQuestion } : {}),
              },
            }),
      });
      setResult(reading);
      setStep("result");
    } catch (err) {
      if (err instanceof ReadingRequestError && err.status === 422) {
        setErrorMessage(`ข้อมูลที่กรอกไม่ถูกต้อง: ${err.detail ?? "กรุณาตรวจสอบข้อมูลอีกครั้ง"}`);
        setIsInputError(true);
      } else {
        setErrorMessage("ไม่สามารถเชื่อมต่อกับระบบดูดวงได้ในขณะนี้ กรุณาลองใหม่อีกครั้ง");
        setIsInputError(false);
      }
      setStep("error");
    }
  }

  function retry() {
    if (pendingAction === "tarot-deck" && tarotSpread) {
      void enterTarotDraw(tarotSpread);
    } else if (pendingAction === "oracle-deck") {
      void enterOracleDraw();
    } else {
      void fetchReading(oracleSkipped);
    }
  }

  // Oracle can only be skipped when at least one other discipline is
  // already in play — otherwise there would be nothing left to read.
  const oracleIsSkippable = !(uranianSkipped && tarotSkipped);

  return (
    <div className="flex flex-1 flex-col justify-center bg-zinc-50 px-6 py-16 dark:bg-black">
      {step === "birth-data" && (
        <BirthDataForm
          onSubmit={(data, options) => {
            setBirthData(data);
            setForecastOptions(options);
            setUranianSkipped(false);
            setStep("tarot-spread");
          }}
          onSkip={() => {
            setBirthData(null);
            setForecastOptions({});
            setUranianSkipped(true);
            setStep("tarot-spread");
          }}
        />
      )}

      {step === "tarot-spread" && (
        <TarotSpreadPicker
          onSelect={(spread) => void enterTarotDraw(spread)}
          onSkip={() => {
            setTarotSkipped(true);
            enterOracleStage(uranianSkipped, true);
          }}
        />
      )}

      {step === "tarot-draw" && tarotSpread && tarotDeck && (
        <CardDrawStep
          title={`จั่วไพ่ทาโรต์ — ${tarotSpread.name_th}`}
          subtitle="ตั้งสมาธิและแตะไพ่ที่รู้สึกดึงดูดใจทีละใบ"
          cardCount={tarotDeck.positions.length}
          cards={tarotDeck.cards.map(
            (c): DrawableCard => ({
              id: c.card_id,
              label: c.reversed ? `${c.name_th} (กลับหัว)` : c.name_th,
            }),
          )}
          rows={3}
          positionLabels={tarotDeck.positions}
          nextLabel="ถัดไป"
          onComplete={(picked) => {
            setTarotPicks(
              picked.map((p) => {
                const card = tarotDeck.cards.find((c) => c.card_id === p.id);
                return { card_id: p.id, reversed: card?.reversed ?? false };
              }),
            );
            enterOracleStage(uranianSkipped, false);
          }}
        />
      )}

      {step === "oracle-question" && (
        <OracleQuestionForm
          title="คำถามของคุณคืออะไร?"
          subtitle="พิมพ์คำถามที่อยากให้ไพ่ออราเคิลตอบ ก่อนเริ่มจั่วไพ่"
          submitLabel="ถัดไป: จั่วไพ่ออราเคิล"
          onSubmit={(question) => {
            setOracleQuestion(question);
            void enterOracleDraw();
          }}
        />
      )}

      {step === "oracle-draw" && oracleCount && oracleDeck && (
        <CardDrawStep
          title="จั่วไพ่ออราเคิล"
          subtitle={`ระบบสุ่มไพ่ออราเคิล ${oracleCount} ใบให้คุณเลือกจากทั้งสำรับ`}
          cardCount={oracleCount}
          cards={oracleDeck.cards.map((c): DrawableCard => ({ id: c.card_id, label: c.name_th }))}
          rows={4}
          nextLabel="ดูคำทำนาย"
          onComplete={(picked) => void fetchReading(false, picked.map((p) => p.id))}
          onSkip={oracleIsSkippable ? () => fetchReading(true) : undefined}
          skipLabel="ข้ามไพ่ออราเคิล"
        />
      )}

      {step === "loading" && (
        <div className="flex flex-col items-center gap-3 text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-950 dark:border-zinc-700 dark:border-t-zinc-50" />
          <p className="text-sm text-zinc-600 dark:text-zinc-400">{loadingMessage}</p>
        </div>
      )}

      {step === "error" && (
        <div className="flex flex-col items-center gap-4 text-center">
          <p className="text-sm text-red-600 dark:text-red-400">{errorMessage}</p>
          <button
            type="button"
            onClick={() => (isInputError ? restart() : retry())}
            className="rounded-full bg-zinc-950 px-6 py-2.5 text-sm font-medium text-zinc-50 dark:bg-zinc-50 dark:text-zinc-950"
          >
            {isInputError ? "แก้ไขข้อมูล" : "ลองใหม่"}
          </button>
        </div>
      )}

      {step === "result" && result && <ReadingResult result={result} onRestart={restart} />}
    </div>
  );
}
