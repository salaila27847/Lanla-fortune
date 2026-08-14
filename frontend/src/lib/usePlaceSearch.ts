"use client";

import { useEffect, useRef, useState } from "react";
import { searchPlace, type GeocodeResult } from "@/lib/geocode";

// Debounced OpenStreetMap/Nominatim place search, shared by any text field
// that should behave like the birth-place field: type → 600ms debounce →
// dropdown of matches. skipNextSearch() suppresses the search that would
// otherwise fire right after programmatically setting the field's value
// (e.g. after the caller applies a preset or a chosen search result).
export function usePlaceSearch(query: string) {
  const [results, setResults] = useState<GeocodeResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showResults, setShowResults] = useState(false);
  const skipNextRef = useRef(false);

  useEffect(() => {
    if (skipNextRef.current) {
      skipNextRef.current = false;
      return;
    }

    const controller = new AbortController();
    const timer = setTimeout(async () => {
      if (query.trim().length < 2) {
        setResults([]);
        setError(null);
        return;
      }

      setIsSearching(true);
      setError(null);
      try {
        const found = await searchPlace(query, controller.signal);
        setResults(found);
        setShowResults(true);
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          setResults([]);
          setError("ค้นหาสถานที่ไม่สำเร็จ กรุณาลองใหม่ หรือกรอกพิกัดด้านล่างด้วยตนเอง");
        }
      } finally {
        setIsSearching(false);
      }
    }, 600);

    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [query]);

  return {
    results,
    isSearching,
    error,
    showResults,
    setShowResults,
    skipNextSearch: () => {
      skipNextRef.current = true;
    },
  };
}
