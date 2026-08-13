"use client";

import { useEffect, useRef, useState } from "react";
import type { BirthData, ForecastOptions } from "@/lib/api";
import { searchPlace, type GeocodeResult } from "@/lib/geocode";

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

const TODAY = new Date().toISOString().slice(0, 10);

type Props = {
  onSubmit: (birthData: BirthData, forecastOptions: ForecastOptions) => void;
};

export default function BirthDataForm({ onSubmit }: Props) {
  const [date, setDate] = useState("");
  const [knowsTime, setKnowsTime] = useState(true);
  const [time, setTime] = useState("12:00");
  const [place, setPlace] = useState(CITY_PRESETS[0].place);
  const [latitude, setLatitude] = useState(CITY_PRESETS[0].latitude);
  const [longitude, setLongitude] = useState(CITY_PRESETS[0].longitude);
  const [timezone, setTimezone] = useState(CITY_PRESETS[0].timezone);

  const [solarArcEnabled, setSolarArcEnabled] = useState(false);
  const [solarArcDate, setSolarArcDate] = useState(TODAY);
  const [transitEnabled, setTransitEnabled] = useState(false);
  const [transitDate, setTransitDate] = useState(TODAY);
  const [lunarReturnEnabled, setLunarReturnEnabled] = useState(false);
  const [lunarReturnDate, setLunarReturnDate] = useState(TODAY);
  const [relocationEnabled, setRelocationEnabled] = useState(false);
  const [relocationPlace, setRelocationPlace] = useState("");
  const [relocationLat, setRelocationLat] = useState(0);
  const [relocationLon, setRelocationLon] = useState(0);

  const [searchResults, setSearchResults] = useState<GeocodeResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [showResults, setShowResults] = useState(false);
  const skipNextSearchRef = useRef(false);

  useEffect(() => {
    if (skipNextSearchRef.current) {
      skipNextSearchRef.current = false;
      return;
    }

    const controller = new AbortController();
    const timer = setTimeout(async () => {
      if (place.trim().length < 2) {
        setSearchResults([]);
        setSearchError(null);
        return;
      }

      setIsSearching(true);
      setSearchError(null);
      try {
        const results = await searchPlace(place, controller.signal);
        setSearchResults(results);
        setShowResults(true);
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          setSearchResults([]);
          setSearchError("ค้นหาสถานที่ไม่สำเร็จ กรุณาลองใหม่ หรือกรอกพิกัดด้านล่างด้วยตนเอง");
        }
      } finally {
        setIsSearching(false);
      }
    }, 600);

    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [place]);

  function applyPreset(preset: CityPreset) {
    skipNextSearchRef.current = true;
    setPlace(preset.place);
    setLatitude(preset.latitude);
    setLongitude(preset.longitude);
    setTimezone(preset.timezone);
    setShowResults(false);
    setSearchResults([]);
  }

  function applySearchResult(result: GeocodeResult) {
    skipNextSearchRef.current = true;
    setPlace(result.displayName);
    setLatitude(result.latitude);
    setLongitude(result.longitude);
    if (result.countryCode === "th") {
      setTimezone("Asia/Bangkok");
    }
    setShowResults(false);
    setSearchResults([]);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!date) return;

    const forecastOptions: ForecastOptions = {
      ...(solarArcEnabled && { solar_arc: { target_date: solarArcDate } }),
      ...(transitEnabled && { transit: { target_date: transitDate } }),
      ...(lunarReturnEnabled && { lunar_return: { search_start: lunarReturnDate } }),
      ...(relocationEnabled && {
        relocation: { place: relocationPlace, latitude: relocationLat, longitude: relocationLon },
      }),
    };

    onSubmit(
      {
        date,
        time: knowsTime ? `${time}:00` : null,
        place,
        latitude,
        longitude,
        timezone,
      },
      forecastOptions,
    );
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
        <div className="relative">
          <input
            type="text"
            value={place}
            onChange={(e) => setPlace(e.target.value)}
            onFocus={() => searchResults.length > 0 && setShowResults(true)}
            onBlur={() => setTimeout(() => setShowResults(false), 150)}
            placeholder="พิมพ์ชื่อจังหวัด/เมือง เพื่อค้นหาพิกัดอัตโนมัติ"
            autoComplete="off"
            className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-950 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
          />
          {isSearching && (
            <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">กำลังค้นหา...</p>
          )}
          {searchError && (
            <p className="mt-1 text-xs text-red-600 dark:text-red-400">{searchError}</p>
          )}
          {showResults && searchResults.length > 0 && (
            <div className="absolute z-10 mt-1 w-full overflow-hidden rounded-lg border border-zinc-300 bg-white shadow-lg dark:border-zinc-700 dark:bg-zinc-900">
              {searchResults.map((result, index) => (
                <button
                  key={`${result.latitude}-${result.longitude}-${index}`}
                  type="button"
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => applySearchResult(result)}
                  className="block w-full border-b border-zinc-100 px-3 py-2 text-left text-xs text-zinc-700 last:border-b-0 hover:bg-zinc-100 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-800"
                >
                  {result.displayName}
                </button>
              ))}
              <p className="bg-zinc-50 px-3 py-1 text-[10px] text-zinc-400 dark:bg-zinc-950 dark:text-zinc-500">
                ค้นหาสถานที่โดย OpenStreetMap
              </p>
            </div>
          )}
        </div>
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

      <div className="flex flex-col gap-3 rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
        <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
          การพยากรณ์ล่วงหน้า (ไม่บังคับ)
        </span>
        <p className="text-xs text-zinc-500 dark:text-zinc-400">
          ผลลัพธ์ส่วนนี้เป็นตารางดิบจากเอนจินยูเรเนียนโดยตรง ยังไม่ผ่านการสังเคราะห์คำทำนาย
        </p>

        <label className="flex items-center gap-2 text-sm text-zinc-700 dark:text-zinc-300">
          <input
            type="checkbox"
            checked={solarArcEnabled}
            onChange={(e) => setSolarArcEnabled(e.target.checked)}
          />
          Solar Arc (ส่วนโค้งสุริยะ)
        </label>
        {solarArcEnabled && (
          <input
            type="date"
            value={solarArcDate}
            onChange={(e) => setSolarArcDate(e.target.value)}
            aria-label="วันที่ต้องการดู Solar Arc"
            className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-950 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
          />
        )}

        <label className="flex items-center gap-2 text-sm text-zinc-700 dark:text-zinc-300">
          <input
            type="checkbox"
            checked={transitEnabled}
            onChange={(e) => setTransitEnabled(e.target.checked)}
          />
          Transit (ดาวโคจรผ่าน)
        </label>
        {transitEnabled && (
          <input
            type="date"
            value={transitDate}
            onChange={(e) => setTransitDate(e.target.value)}
            aria-label="วันที่ต้องการดู Transit"
            className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-950 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
          />
        )}

        <label className="flex items-center gap-2 text-sm text-zinc-700 dark:text-zinc-300">
          <input
            type="checkbox"
            checked={lunarReturnEnabled}
            onChange={(e) => setLunarReturnEnabled(e.target.checked)}
          />
          Lunar Return (จันทร์คืนตำแหน่งเกิด)
        </label>
        {lunarReturnEnabled && (
          <div className="flex flex-col gap-1">
            <input
              type="date"
              value={lunarReturnDate}
              onChange={(e) => setLunarReturnDate(e.target.value)}
              aria-label="เริ่มค้นหา Lunar Return จากวันที่"
              className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-950 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
            />
            <p className="text-xs text-zinc-500 dark:text-zinc-400">
              ค้นหาวันที่ดวงจันทร์โคจรกลับมาตำแหน่งเกิด นับจากวันที่นี้เป็นต้นไป
            </p>
          </div>
        )}

        <label className="flex items-center gap-2 text-sm text-zinc-700 dark:text-zinc-300">
          <input
            type="checkbox"
            checked={relocationEnabled}
            onChange={(e) => setRelocationEnabled(e.target.checked)}
          />
          Relocation (ดวงย้ายถิ่น)
        </label>
        {relocationEnabled && (
          <div className="flex flex-col gap-2">
            <input
              type="text"
              value={relocationPlace}
              onChange={(e) => setRelocationPlace(e.target.value)}
              placeholder="ชื่อสถานที่ปลายทาง"
              className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-950 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
            />
            <div className="grid grid-cols-2 gap-2">
              <input
                type="number"
                step="0.0001"
                value={relocationLat}
                onChange={(e) => setRelocationLat(Number(e.target.value))}
                aria-label="ละติจูดปลายทาง"
                className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-950 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
              />
              <input
                type="number"
                step="0.0001"
                value={relocationLon}
                onChange={(e) => setRelocationLon(Number(e.target.value))}
                aria-label="ลองจิจูดปลายทาง"
                className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-950 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
              />
            </div>
            {!knowsTime && (
              <p className="text-xs text-red-600 dark:text-red-400">
                ต้องทราบเวลาเกิดจึงจะคำนวณดวงย้ายถิ่นได้
              </p>
            )}
          </div>
        )}
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
