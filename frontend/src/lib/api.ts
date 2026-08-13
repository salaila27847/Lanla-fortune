export type Finding = {
  label: string;
  meaning: string;
  weight: number;
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

export type SynthesisOutput = {
  final_reading: string;
  convergent_themes: string[];
  divergent_notes: string[];
  per_engine_breakdown: Record<string, EngineResult>;
};

export type ReadingRecord = {
  id: number;
  created_at: string;
  birth_data: BirthData;
  synthesis: SynthesisOutput;
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

export async function getReading(birthData: BirthData): Promise<SynthesisOutput> {
  const res = await fetch("/api/reading", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(birthData),
  });

  if (!res.ok) {
    throw new ReadingRequestError(res.status, await extractErrorDetail(res));
  }

  return res.json();
}

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

export type SolarArcResult = { arc_degrees: number; pictures: PictureResult[] };
export type TransitResult = { pictures: PictureResult[] };
export type LunarReturnResult = { return_at: string };
export type RelocationResult = { ascendant: number; midheaven: number };

export type ForecastResponse = {
  solar_arc: SolarArcResult | null;
  transit: TransitResult | null;
  lunar_return: LunarReturnResult | null;
  relocation: RelocationResult | null;
};

export function hasForecastOptions(options: ForecastOptions): boolean {
  return Boolean(options.solar_arc || options.transit || options.lunar_return || options.relocation);
}

export async function getForecast(
  birthData: BirthData,
  options: ForecastOptions,
): Promise<ForecastResponse> {
  const res = await fetch("/api/forecast", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ birth_data: birthData, ...options }),
  });

  if (!res.ok) {
    throw new ReadingRequestError(res.status, await extractErrorDetail(res));
  }

  return res.json();
}
