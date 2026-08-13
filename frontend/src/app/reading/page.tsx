"use client";

import { useState } from "react";
import BirthDataForm from "@/components/BirthDataForm";
import CardDrawStep from "@/components/CardDrawStep";
import ReadingResult from "@/components/ReadingResult";
import {
  getReading,
  ReadingRequestError,
  type BirthData,
  type ForecastOptions,
  type SynthesisOutput,
} from "@/lib/api";

type Step = "birth-data" | "tarot" | "oracle" | "loading" | "result" | "error";

export default function ReadingPage() {
  const [step, setStep] = useState<Step>("birth-data");
  const [birthData, setBirthData] = useState<BirthData | null>(null);
  const [forecastOptions, setForecastOptions] = useState<ForecastOptions>({});
  const [result, setResult] = useState<SynthesisOutput | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [isInputError, setIsInputError] = useState(false);

  function restart() {
    setStep("birth-data");
    setBirthData(null);
    setForecastOptions({});
    setResult(null);
    setErrorMessage("");
    setIsInputError(false);
  }

  async function fetchReading(data: BirthData) {
    setStep("loading");
    try {
      // Forecast options (if any) ride along in the same request, so the
      // synthesized reading itself can weave in Solar Arc/Transit/Lunar
      // Return/Relocation — see backend/app/main.py's ReadingRequest.
      const reading = await getReading(data, forecastOptions);
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

  return (
    <div className="flex flex-1 flex-col justify-center bg-zinc-50 px-6 py-16 dark:bg-black">
      {step === "birth-data" && (
        <BirthDataForm
          onSubmit={(data, options) => {
            setBirthData(data);
            setForecastOptions(options);
            setStep("tarot");
          }}
        />
      )}

      {step === "tarot" && (
        <CardDrawStep
          title="จั่วไพ่ทาโรต์"
          subtitle="ตั้งสมาธิและแตะไพ่ที่รู้สึกดึงดูดใจ"
          cardCount={3}
          nextLabel="ถัดไป: จั่วไพ่ออราเคิล"
          onComplete={() => setStep("oracle")}
        />
      )}

      {step === "oracle" && (
        <CardDrawStep
          title="จั่วไพ่ออราเคิล"
          subtitle="แตะไพ่ 1 ใบเพื่อรับข้อความนำทาง"
          cardCount={1}
          nextLabel="ดูคำทำนาย"
          onComplete={() => birthData && fetchReading(birthData)}
        />
      )}

      {step === "loading" && (
        <div className="flex flex-col items-center gap-3 text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-950 dark:border-zinc-700 dark:border-t-zinc-50" />
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            กำลังสังเคราะห์คำทำนายจากทั้ง 3 ศาสตร์...
          </p>
        </div>
      )}

      {step === "error" && (
        <div className="flex flex-col items-center gap-4 text-center">
          <p className="text-sm text-red-600 dark:text-red-400">{errorMessage}</p>
          <button
            type="button"
            onClick={() => (isInputError ? restart() : birthData && fetchReading(birthData))}
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
