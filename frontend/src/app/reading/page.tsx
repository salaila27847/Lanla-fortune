"use client";

import { useState } from "react";
import BirthDataForm from "@/components/BirthDataForm";
import TarotSpreadPicker from "@/components/TarotSpreadPicker";
import OracleQuestionForm from "@/components/OracleQuestionForm";
import CardDrawStep from "@/components/CardDrawStep";
import ReadingResult from "@/components/ReadingResult";
import { randomOracleCount } from "@/lib/random";
import { ORACLE_DECK_SIZE, TAROT_DECK_SIZE } from "@/lib/deckSizes";
import {
  getReading,
  ReadingRequestError,
  type BirthData,
  type ForecastOptions,
  type SynthesisOutput,
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

export default function ReadingPage() {
  const [step, setStep] = useState<Step>("birth-data");

  const [birthData, setBirthData] = useState<BirthData | null>(null);
  const [forecastOptions, setForecastOptions] = useState<ForecastOptions>({});
  const [uranianSkipped, setUranianSkipped] = useState(false);

  const [tarotSpread, setTarotSpread] = useState<TarotSpreadInfo | null>(null);
  const [tarotSkipped, setTarotSkipped] = useState(false);

  const [oracleQuestion, setOracleQuestion] = useState<string | null>(null);
  const [oracleCount, setOracleCount] = useState<number | null>(null);
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
    setOracleQuestion(null);
    setOracleCount(null);
    setOracleSkipped(false);
    setResult(null);
    setErrorMessage("");
    setIsInputError(false);
  }

  // Oracle is the only discipline that always has a card count (system
  // randomized, 3-9) — but whether it also needs a question first depends
  // on whether it's the *only* discipline in play (both others skipped).
  function enterOracleStage(skippedUranian: boolean, skippedTarot: boolean) {
    if (skippedUranian && skippedTarot) {
      setStep("oracle-question");
    } else {
      setOracleCount(randomOracleCount());
      setStep("oracle-draw");
    }
  }

  async function fetchReading(skipOracle: boolean) {
    setOracleSkipped(skipOracle);
    setStep("loading");
    try {
      const reading = await getReading({
        ...(uranianSkipped ? {} : { birth_data: birthData as BirthData, ...forecastOptions }),
        ...(tarotSkipped ? {} : { tarot: { spread: (tarotSpread as TarotSpreadInfo).id } }),
        ...(skipOracle
          ? {}
          : {
              oracle: {
                card_count: oracleCount as number,
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
          onSelect={(spread) => {
            setTarotSpread(spread);
            setTarotSkipped(false);
            setStep("tarot-draw");
          }}
          onSkip={() => {
            setTarotSkipped(true);
            enterOracleStage(uranianSkipped, true);
          }}
        />
      )}

      {step === "tarot-draw" && tarotSpread && (
        <CardDrawStep
          title={`จั่วไพ่ทาโรต์ — ${tarotSpread.name_th}`}
          subtitle="ตั้งสมาธิและแตะไพ่ที่รู้สึกดึงดูดใจทีละใบ"
          cardCount={tarotSpread.positions.length}
          deckSize={TAROT_DECK_SIZE}
          rows={3}
          positionLabels={tarotSpread.positions}
          nextLabel="ถัดไป"
          onComplete={() => enterOracleStage(uranianSkipped, false)}
        />
      )}

      {step === "oracle-question" && (
        <OracleQuestionForm
          title="คำถามของคุณคืออะไร?"
          subtitle="พิมพ์คำถามที่อยากให้ไพ่ออราเคิลตอบ ก่อนเริ่มจั่วไพ่"
          submitLabel="ถัดไป: จั่วไพ่ออราเคิล"
          onSubmit={(question) => {
            setOracleQuestion(question);
            setOracleCount(randomOracleCount());
            setStep("oracle-draw");
          }}
        />
      )}

      {step === "oracle-draw" && oracleCount && (
        <CardDrawStep
          title="จั่วไพ่ออราเคิล"
          subtitle={`ระบบสุ่มไพ่ออราเคิล ${oracleCount} ใบให้คุณเลือกจากทั้งสำรับ`}
          cardCount={oracleCount}
          deckSize={ORACLE_DECK_SIZE}
          rows={4}
          nextLabel="ดูคำทำนาย"
          onComplete={() => fetchReading(false)}
          onSkip={oracleIsSkippable ? () => fetchReading(true) : undefined}
          skipLabel="ข้ามไพ่ออราเคิล"
        />
      )}

      {step === "loading" && (
        <div className="flex flex-col items-center gap-3 text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-950 dark:border-zinc-700 dark:border-t-zinc-50" />
          <p className="text-sm text-zinc-600 dark:text-zinc-400">กำลังสังเคราะห์คำทำนาย...</p>
        </div>
      )}

      {step === "error" && (
        <div className="flex flex-col items-center gap-4 text-center">
          <p className="text-sm text-red-600 dark:text-red-400">{errorMessage}</p>
          <button
            type="button"
            onClick={() => (isInputError ? restart() : fetchReading(oracleSkipped))}
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
