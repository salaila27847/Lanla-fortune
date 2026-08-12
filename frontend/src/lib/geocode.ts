export type GeocodeResult = {
  displayName: string;
  latitude: number;
  longitude: number;
  countryCode: string | null;
};

type NominatimResult = {
  display_name: string;
  lat: string;
  lon: string;
  address?: { country_code?: string };
};

export async function searchPlace(query: string, signal?: AbortSignal): Promise<GeocodeResult[]> {
  const params = new URLSearchParams({
    format: "jsonv2",
    q: query,
    addressdetails: "1",
    limit: "5",
    "accept-language": "th",
  });

  const res = await fetch(`https://nominatim.openstreetmap.org/search?${params.toString()}`, { signal });

  if (!res.ok) {
    throw new Error(`Geocoding request failed: ${res.status}`);
  }

  const body: NominatimResult[] = await res.json();

  return body.map((item) => ({
    displayName: item.display_name,
    latitude: Number(item.lat),
    longitude: Number(item.lon),
    countryCode: item.address?.country_code ?? null,
  }));
}
