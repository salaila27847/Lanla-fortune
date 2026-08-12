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

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function getReading(birthData: BirthData): Promise<SynthesisOutput> {
  const res = await fetch(`${API_BASE_URL}/api/reading`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(birthData),
  });

  if (!res.ok) {
    throw new Error(`Reading request failed: ${res.status}`);
  }

  return res.json();
}
