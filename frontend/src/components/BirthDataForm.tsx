"use client";

import { useState } from "react";
import type { BirthData } from "@/lib/api";

type CityPreset = {
  label: string;
  place: string;
  latitude: number;
  longitude: number;
  timezone: string;
};

const CITY_PRESETS: CityPreset[] = [
  { label: "กรุงเทพฯ", place: "กรุงเทพมหานคร", latitude: 13.7563, longitude: 100.5018, timezone: "Asia/Bangkok" },
  { label: "เชียงใหม่", place: "เชียงใหม่", latitude: 18.7883, longitude: 98.9853, timezone: "Asia/Bangkok" },
  { label: "ขอนแก่น", place: "ขอนแก่น", latitude: 16.4419, longitude: 102.8360, timezone: "Asia/Bangkok" },
  { label: "หาดใหญ่", place: "หาดใหญ่", latitude: 7.0084, longitude: 100.4747, timezone: "Asia/Bangkok" },
];

type Props = {
  onSubmit: (birthData: BirthData) => void;
};

export default function BirthDataForm({ onSubmit }: Props) {
  const [date, setDate] = useState("");
  const [knowsTime, setKnowsTime] = useState(true);
  const [time, setTime] = useState("12:00");
  const [place, setPlace] = useState(CITY_PRESETS[0].place);
  const [latitude, setLatitude] = useState(CITY_PRESETS[0].latitude);
  const [longitude, setLongitude] = useState(CITY_PRESETS[0].longitude);
  const [timezone, setTimezone] = useState(CITY_PRESETS[0].timezone);

  function applyPreset(preset: CityPreset) {
    setPlace(preset.place);
    setLatitude(preset.latitude);
    setLongitude(preset.longitude);
    setTimezone(preset.timezone);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!date) return;

    onSubmit({
      date,
      time: knowsTime ? `${time}:00` : null,
      place,
      latitude,
      longitude,
      timezone,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="mx-auto flex w-full max-w-md flex-col gap-6">
      <div className="flex flex-col gap-1.5">
        <label htmlFor="date" className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
          วันเกิด
        </label>
        <input
          id="date"
          type="date"
          required
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-950 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
        />
      </div>

      <div className="flex flex-col gap-1.5">
        <div className="flex items-center justify-between">
          <label htmlFor="time" className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
            เวลาเกิด
          </label>
          <label className="flex items-center gap-1.5 text-xs text-zinc-500 dark:text-zinc-400">
            <input
              type="checkbox"
              checked={!knowsTime}
              onChange={(e) => setKnowsTime(!e.target.checked)}
            />
            ไม่ทราบเวลาเกิด
          </label>
        </div>
        <input
          id="time"
          type="time"
          disabled={!knowsTime}
          value={time}
          onChange={(e) => setTime(e.target.value)}
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-950 disabled:opacity-40 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
        />
        {!knowsTime && (
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            หากไม่ทราบเวลาเกิด ผลการวิเคราะห์ยูเรเนียนบางส่วนอาจมีความแม่นยำจำกัด
          </p>
        )}
      </div>

      <div className="flex flex-col gap-1.5">
        <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300">สถานที่เกิด</span>
        <div className="flex flex-wrap gap-2">
          {CITY_PRESETS.map((preset) => (
            <button
              key={preset.label}
              type="button"
              onClick={() => applyPreset(preset)}
              className="rounded-full border border-zinc-300 px-3 py-1 text-xs text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
            >
              {preset.label}
            </button>
          ))}
        </div>
        <input
          type="text"
          value={place}
          onChange={(e) => setPlace(e.target.value)}
          placeholder="ชื่อจังหวัด/เมือง"
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-950 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
        />
        <div className="grid grid-cols-2 gap-2">
          <input
            type="number"
            step="0.0001"
            value={latitude}
            onChange={(e) => setLatitude(Number(e.target.value))}
            aria-label="ละติจูด"
            className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-950 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
          />
          <input
            type="number"
            step="0.0001"
            value={longitude}
            onChange={(e) => setLongitude(Number(e.target.value))}
            aria-label="ลองจิจูด"
            className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-950 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
          />
        </div>
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor="timezone" className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
          เขตเวลา
        </label>
        <input
          id="timezone"
          type="text"
          value={timezone}
          onChange={(e) => setTimezone(e.target.value)}
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-950 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
        />
      </div>

      <button
        type="submit"
        className="mt-2 rounded-full bg-zinc-950 px-6 py-3 text-sm font-medium text-zinc-50 transition-colors hover:bg-zinc-800 dark:bg-zinc-50 dark:text-zinc-950 dark:hover:bg-zinc-200"
      >
        ถัดไป: จั่วไพ่ทาโรต์
      </button>
    </form>
  );
}
