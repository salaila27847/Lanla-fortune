export type Finding = {
  label: string;
  meaning: string;
  weight: number;
  voice: string | null;
};

export type EngineResult = {
  engine: "uranian" | "tarot" | "oracle";
  summary: string;
  themes: string[];
  raw_findings: Finding[];
  confidence: number;
};

export type BirthData = {
  date: string; // YYYY-MM-DD
  time: string | null; // HH:MM:SS
  place: string;
  latitude: number;
  longitude: number;
  timezone: string;
};

export type ForecastOptions = {
  solar_arc?: { target_date: string };
  transit?: { target_date: string };
  lunar_return?: { search_start: string };
  relocation?: { place: string; latitude: number; longitude: number };
};

export type PictureResult = {
  type: "type1" | "type2";
  label: string;
  factors: string[];
  orb: number;
};

export type FineTimingHit = {
  label: string;
  transit_factor: string;
  reference_factor: string;
  orb: number;
};

export type HousePlacementResult = {
  factor: string;
  house_number: number;
  label: string;
};

export type SolarArcResult = {
  arc_degrees: number;
  pictures: PictureResult[];
  house_placements: HousePlacementResult[];
};
export type TransitResult = {
  pictures: PictureResult[];
  fine_timing: FineTimingHit[];
  house_placements: HousePlacementResult[];
};
export type LunarReturnResult = { return_at: string };
export type RelocationResult = {
  ascendant: number;
  midheaven: number;
  house_placements: HousePlacementResult[];
};

export type ForecastResponse = {
  solar_arc: SolarArcResult | null;
  transit: TransitResult | null;
  lunar_return: LunarReturnResult | null;
  relocation: RelocationResult | null;
};

export type SynthesisOutput = {
  final_reading: string;
  convergent_themes: string[];
  divergent_notes: string[];
  per_engine_breakdown: Partial<Record<"uranian" | "tarot" | "oracle", EngineResult>>;
  forecast: ForecastResponse | null;
  oracle_question?: string | null;
};

export type ReadingRecord = {
  id: number;
  created_at: string;
  birth_data: BirthData | null;
  synthesis: SynthesisOutput;
};

// Real cards fetched from a full shuffled deck (POST /api/oracle/draw,
// POST /api/tarot/draw) — so a tap on the card grid reveals a specific,
// already-decided card instead of a cosmetic one assigned afterward.
export type OracleCardPreview = {
  card_id: string;
  name_th: string;
  category_th: string;
  meaning: string;
  keywords: string[];
};

export type OracleDeck = { cards: OracleCardPreview[] };

export type TarotCardPreview = {
  card_id: string;
  name_th: string;
  reversed: boolean;
  meaning: string;
  keywords: string[];
};

export type TarotDeck = { positions: string[]; cards: TarotCardPreview[] };

// Body shape for POST /api/reading — birth_data/tarot/oracle are each
// independently optional, since the user can skip any 1 or 2 of the 3
// disciplines (see backend/app/core/schema.py's ReadingRequest). At least
// one of the three must be present, or the backend rejects with 422.
// tarot.picks/oracle.picks are the cards the user actually revealed (in
// tap order) from the deck /api/tarot/draw or /api/oracle/draw returned —
// trusted as-is server-side, but re-looked-up by id for the real meaning.
export type ReadingSubmission = ForecastOptions & {
  birth_data?: BirthData;
  tarot?: { spread: string; picks: { card_id: string; reversed: boolean }[] };
  oracle?: { picks: string[]; question?: string };
};

export type FollowUpSubmission = {
  previous: SynthesisOutput;
  question: string;
  oracle_picks: string[];
};

export class ReadingRequestError extends Error {
  status: number;
  detail?: string;

  constructor(status: number, detail?: string) {
    super(detail ?? `Reading request failed: ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

async function extractErrorDetail(res: Response): Promise<string | undefined> {
  try {
    const body = await res.json();
    if (Array.isArray(body?.detail)) {
      return body.detail
        .map((item: { msg?: string }) => item.msg)
        .filter(Boolean)
        .join(", ");
    }
    if (typeof body?.detail === "string") {
      return body.detail;
    }
  } catch {
    // response body wasn't JSON — fall back to a generic message
  }
  return undefined;
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    throw new ReadingRequestError(res.status, await extractErrorDetail(res));
  }

  return res.json();
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) {
    throw new ReadingRequestError(res.status, await extractErrorDetail(res));
  }
  return res.json();
}

export async function getReading(submission: ReadingSubmission): Promise<SynthesisOutput> {
  return postJson("/api/reading", submission);
}

// The birth data remembered from the user's most recently submitted
// reading that included it (see backend/app/main.py's
// _remember_birth_data) — used to prefill BirthDataForm for a returning
// user instead of making them retype it every time. Best-effort: callers
// should treat a thrown error the same as "nothing saved" rather than
// blocking the form.
export async function getSavedBirthData(): Promise<BirthData | null> {
  return getJson("/api/profile/birth-data");
}

export async function clearSavedBirthData(): Promise<void> {
  const res = await fetch("/api/profile/birth-data", { method: "DELETE" });
  if (!res.ok) {
    throw new ReadingRequestError(res.status, await extractErrorDetail(res));
  }
}

export async function getFollowUpReading(
  submission: FollowUpSubmission,
): Promise<SynthesisOutput> {
  return postJson("/api/reading/follow-up", submission);
}

export async function drawOracleDeck(deck?: string): Promise<OracleDeck> {
  return postJson("/api/oracle/draw", deck ? { deck } : {});
}

export async function drawTarotDeck(spread: string): Promise<TarotDeck> {
  return postJson("/api/tarot/draw", { spread });
}
