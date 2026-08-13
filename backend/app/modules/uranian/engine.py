"""Uranian astrology engine.

Computes all 22 Hamburg School factors — the 10 classical bodies (Sun
through Pluto), the 8 trans-Neptunian points (Cupido, Hades, Zeus,
Kronos, Apollon, Admetos, Vulkanus, Poseidon), the (true) Node, the
Aries Point, and — when the birth time is known — Ascendant/Midheaven —
via pyswisseph's built-in Moshier ephemeris (no external data files or
network access needed).

Two kinds of findings are produced:

1. Placement findings — each of the 8 TNPs by zodiac sign (unchanged
   from the original stub-replacement implementation).
2. Planetary-picture findings — 90°-dial midpoint structures among all
   22 factors: Type I (a single factor sits on another pair's midpoint,
   e.g. Mars/Saturn=Uranus) and Type II (two pairs' midpoints coincide,
   e.g. M/Moon=Venus/Sun). Only pictures involving at least one personal
   point (Sun, Moon, M, A, Node, Aries Point) are kept. Each picture is
   matched against the curated combinations glossary; unmatched pictures
   fall back to a meaning composed from each factor's own keywords.

Meanings are assembled from backend/app/knowledge_base/uranian/
(points.yaml, signs.yaml, factors.yaml, planetary_pictures.yaml,
axis_meanings.yaml), never hardcoded here.

The function signature and return type (EngineResult) must not change —
the synthesis layer depends on this contract.
"""

from __future__ import annotations

from datetime import datetime
from datetime import time as dt_time
from functools import lru_cache
from itertools import combinations
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import swisseph as swe
import yaml

from app.core.schema import BirthData, EngineResult, Finding

KB_DIR = Path(__file__).resolve().parents[2] / "knowledge_base" / "uranian"

TNP_SWE_IDS: dict[str, int] = {
    "cupido": 40,
    "hades": 41,
    "zeus": 42,
    "kronos": 43,
    "apollon": 44,
    "admetos": 45,
    "vulkanus": 46,
    "poseidon": 47,
}
CLASSICAL_SWE_IDS: dict[str, int] = {
    "SUN": swe.SUN,
    "MOON": swe.MOON,
    "MERCURY": swe.MERCURY,
    "VENUS": swe.VENUS,
    "MARS": swe.MARS,
    "JUPITER": swe.JUPITER,
    "SATURN": swe.SATURN,
    "URANUS": swe.URANUS,
    "NEPTUNE": swe.NEPTUNE,
    "PLUTO": swe.PLUTO,
}
PERSONAL_POINT_IDS = frozenset({"SUN", "MOON", "M", "A", "NODE", "ARIES"})
_CATEGORY_RANK = {"transneptunian": 0, "planet": 1, "personal_point": 2}

TYPE1_ORB_DEGREES = 1.5  # off-center orb for a single factor on another pair's midpoint
TYPE2_ORB_DEGREES = 3.0  # off-side orb for two pairs' midpoints coinciding
MAX_PICTURE_FINDINGS = 10  # cap picture findings so payloads stay proportionate


@lru_cache
def _load_points() -> dict[str, dict[str, Any]]:
    data = yaml.safe_load((KB_DIR / "points.yaml").read_text(encoding="utf-8"))
    return {point["id"]: point for point in data["points"]}


@lru_cache
def _load_signs() -> tuple[dict[str, Any], ...]:
    data = yaml.safe_load((KB_DIR / "signs.yaml").read_text(encoding="utf-8"))
    return tuple(data["signs"])


@lru_cache
def _load_factors() -> dict[str, dict[str, Any]]:
    data = yaml.safe_load((KB_DIR / "factors.yaml").read_text(encoding="utf-8"))
    return {factor["id"]: factor for factor in data["factors"]}


@lru_cache
def _load_planetary_pictures() -> dict[frozenset[str], dict[str, str]]:
    data = yaml.safe_load((KB_DIR / "planetary_pictures.yaml").read_text(encoding="utf-8"))
    return {frozenset(entry["factors"]): entry for entry in data["pictures"]}


@lru_cache
def _load_axis_meanings() -> dict[str, dict[str, str]]:
    data = yaml.safe_load((KB_DIR / "axis_meanings.yaml").read_text(encoding="utf-8"))
    return {
        axis["axis"]: {entry["paired_factor"]: entry["meaning_th"] for entry in axis["entries"]}
        for axis in data["axes"]
    }


def _sign_for_longitude(longitude: float) -> dict[str, Any]:
    return _load_signs()[int(longitude // 30) % 12]


def _factor_display_name(factor_id: str) -> str:
    factors = _load_factors()
    if factor_id in factors:
        return factors[factor_id]["name_th"]
    return _load_points()[factor_id.lower()]["name_th"]


def _factor_keywords(factor_id: str) -> list[str]:
    factors = _load_factors()
    if factor_id in factors:
        return factors[factor_id]["keywords"]
    return _load_points()[factor_id.lower()]["keywords"]


def _factor_category(factor_id: str) -> str:
    if factor_id.lower() in TNP_SWE_IDS:
        return "transneptunian"
    return _load_factors()[factor_id]["category"]


def _julian_day_ut(birth_data: BirthData) -> tuple[float, bool]:
    known_time = birth_data.time is not None
    local_time = birth_data.time or dt_time(12, 0)

    local_dt = datetime.combine(birth_data.date, local_time, tzinfo=ZoneInfo(birth_data.timezone))
    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))

    hour = utc_dt.hour + utc_dt.minute / 60 + utc_dt.second / 3600
    return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hour), known_time


def _midpoint(a: float, b: float) -> float:
    """Midpoint via the shorter arc between two ecliptic longitudes."""
    diff = (b - a) % 360
    if diff > 180:
        diff -= 360
    return (a + diff / 2) % 360


def _dial90_orb(a: float, b: float) -> float:
    """Distance between two longitudes on the 90° dial (mod 90)."""
    diff = abs((a - b) % 90)
    return min(diff, 90 - diff)


def _compute_positions(jd: float, birth_data: BirthData, known_time: bool) -> dict[str, float]:
    """Longitudes for all factors that don't need the birth time, plus
    Ascendant/Midheaven when it's known. Dict insertion order is fixed
    (classical bodies, then TNPs, then Node/Aries, then Asc/MC) so the
    picture search below is deterministic run-to-run."""
    positions: dict[str, float] = {
        factor_id: swe.calc_ut(jd, swe_id)[0][0] for factor_id, swe_id in CLASSICAL_SWE_IDS.items()
    }
    for point_id, swe_id in TNP_SWE_IDS.items():
        positions[point_id.upper()] = swe.calc_ut(jd, swe_id)[0][0]
    positions["NODE"] = swe.calc_ut(jd, swe.TRUE_NODE)[0][0]
    positions["ARIES"] = 0.0

    if known_time:
        try:
            _, ascmc = swe.houses(jd, birth_data.latitude, birth_data.longitude, b"P")
            positions["A"] = ascmc[0]
            positions["M"] = ascmc[1]
        except swe.Error:
            pass
    return positions


def _midpoint_matrix(positions: dict[str, float]) -> dict[frozenset[str], float]:
    return {
        frozenset((a, b)): _midpoint(positions[a], positions[b])
        for a, b in combinations(positions, 2)
    }


def _find_pictures(
    positions: dict[str, float],
    personal_point_ids: frozenset[str],
    orb_type1: float = TYPE1_ORB_DEGREES,
    orb_type2: float = TYPE2_ORB_DEGREES,
) -> list[dict[str, Any]]:
    """Type I (pair's midpoint hit by a third factor) and Type II (two
    pairs' midpoints coincide) planetary pictures, on the 90° dial.
    Keeps only pictures that include at least one personal point, and
    sorts tightest-orb first."""
    midpoints = _midpoint_matrix(positions)
    found: list[dict[str, Any]] = []

    for pair, mp in midpoints.items():
        for factor, longitude in positions.items():
            if factor in pair:
                continue
            orb = _dial90_orb(longitude, mp)
            if orb <= orb_type1:
                a, b = sorted(pair)
                found.append(
                    {
                        "type": "type1",
                        "pair": (a, b),
                        "hit": factor,
                        "factors": frozenset(pair | {factor}),
                        "orb": orb,
                    }
                )

    pair_items = list(midpoints.items())
    for i, (pair_a, mp_a) in enumerate(pair_items):
        for pair_b, mp_b in pair_items[i + 1 :]:
            if pair_a & pair_b:
                continue
            orb = _dial90_orb(mp_a, mp_b)
            if orb <= orb_type2:
                found.append(
                    {
                        "type": "type2",
                        "pair": tuple(sorted(pair_a)),
                        "pair_b": tuple(sorted(pair_b)),
                        "factors": frozenset(pair_a | pair_b),
                        "orb": orb,
                    }
                )

    found = [picture for picture in found if picture["factors"] & personal_point_ids]
    found.sort(key=lambda picture: picture["orb"])
    return found


def _picture_theme(picture: dict[str, Any]) -> str | None:
    """One keyword to feed into the engine's themes, from whichever
    factor in the picture is most distinctive (TNP > planet > personal
    point, since personal points recur in nearly every picture)."""
    ranked = sorted(picture["factors"], key=lambda f: _CATEGORY_RANK[_factor_category(f)])
    for factor in ranked:
        keywords = _factor_keywords(factor)
        if keywords:
            return keywords[0]
    return None


def _picture_finding(picture: dict[str, Any]) -> Finding:
    factors = picture["factors"]
    disp = _factor_display_name

    if picture["type"] == "type1":
        a, b = picture["pair"]
        c = picture["hit"]
        label = f"{disp(a)}/{disp(b)} = {disp(c)} (คลาดเคลื่อน {picture['orb']:.2f}°)"
    else:
        a, b = picture["pair"]
        c, d = picture["pair_b"]
        label = f"{disp(a)}/{disp(b)} = {disp(c)}/{disp(d)} (คลาดเคลื่อน {picture['orb']:.2f}°)"

    glossary = _load_planetary_pictures()
    matches = [
        glossary[frozenset(combo)]
        for combo in combinations(sorted(factors), 2)
        if frozenset(combo) in glossary
    ]

    if matches:
        meaning = " ".join(dict.fromkeys(match["meaning_th"] for match in matches))
        weight = 0.85 if picture["type"] == "type2" else 0.75
    else:
        names = "/".join(disp(f) for f in sorted(factors))
        keywords = [keywords[0] for f in sorted(factors) if (keywords := _factor_keywords(f))]
        meaning = f"{names} เชื่อมโยงกันในดวงชะตา สะท้อนพลัง: {', '.join(dict.fromkeys(keywords))}"
        weight = 0.55 if picture["type"] == "type2" else 0.45

    all_axes = _load_axis_meanings()
    for axis_id in sorted(factors & all_axes.keys()):
        axis_entries = all_axes[axis_id]
        for other in sorted(factors - {axis_id}):
            axis_meaning = axis_entries.get(other)
            if axis_meaning:
                meaning += f" (บนแกน {axis_id}: {axis_meaning})"

    return Finding(label=label, meaning=meaning, weight=weight)


async def calculate(birth_data: BirthData) -> EngineResult:
    jd, known_time = _julian_day_ut(birth_data)
    positions = _compute_positions(jd, birth_data, known_time)
    points_kb = _load_points()

    placement_findings: list[Finding] = []
    picture_findings: list[Finding] = []
    themes: list[str] = []

    for point_id in TNP_SWE_IDS:
        longitude = positions[point_id.upper()]
        meta = points_kb[point_id]
        sign = _sign_for_longitude(longitude)
        degree_in_sign = longitude % 30

        placement_findings.append(
            Finding(
                label=f"{meta['name_th']} ที่ {sign['name_th']} {degree_in_sign:.1f}°",
                meaning=f"{meta['meaning_core']} — {sign['modifier']}",
                weight=0.5,
            )
        )
        themes.extend(meta["keywords"][:2])

    pictures = _find_pictures(positions, PERSONAL_POINT_IDS)[:MAX_PICTURE_FINDINGS]
    for picture in pictures:
        picture_findings.append(_picture_finding(picture))
        theme = _picture_theme(picture)
        if theme:
            themes.insert(0, theme)

    if not known_time:
        placement_findings.append(
            Finding(
                label="ไม่ทราบเวลาเกิด",
                meaning=(
                    "ระบบใช้เที่ยงวันเป็นค่าประมาณ ตำแหน่งดวงจันทร์และมุมลัคนา/เมอริเดียน"
                    "อาจมีความคลาดเคลื่อน ผลลัพธ์ในส่วนนี้จึงมีความแม่นยำจำกัด"
                ),
                weight=0.3,
            )
        )

    findings = picture_findings + placement_findings
    summary = findings[0].meaning if findings else "ไม่สามารถคำนวณตำแหน่งดาวได้"

    return EngineResult(
        engine="uranian",
        summary=summary,
        themes=list(dict.fromkeys(themes))[:5],
        raw_findings=findings,
        confidence=0.55 if known_time else 0.35,
    )
