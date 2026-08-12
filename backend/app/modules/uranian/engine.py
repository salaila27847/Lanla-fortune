"""Uranian astrology engine.

Computes the 8 Hamburg School trans-Neptunian points (Cupido, Hades,
Zeus, Kronos, Apollon, Admetos, Vulkanus, Poseidon) via pyswisseph's
built-in Moshier ephemeris (swe_id 40-47 — no external data files or
network access needed), places them by zodiac sign, and checks which
land on a "main" 90°-dial midpoint of the birth's personal points
(Sun, Moon, and — when the birth time is known — Ascendant/MC).

Meanings are assembled from backend/app/knowledge_base/uranian/
(points.yaml, signs.yaml), never hardcoded here.

The function signature and return type (EngineResult) must not change —
the synthesis layer depends on this contract.
"""

from __future__ import annotations

from datetime import datetime
from datetime import time as dt_time
from functools import lru_cache
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
MIDPOINT_ORB_DEGREES = 1.5


@lru_cache
def _load_points() -> dict[str, dict[str, Any]]:
    data = yaml.safe_load((KB_DIR / "points.yaml").read_text(encoding="utf-8"))
    return {point["id"]: point for point in data["points"]}


@lru_cache
def _load_signs() -> tuple[dict[str, Any], ...]:
    data = yaml.safe_load((KB_DIR / "signs.yaml").read_text(encoding="utf-8"))
    return tuple(data["signs"])


def _sign_for_longitude(longitude: float) -> dict[str, Any]:
    return _load_signs()[int(longitude // 30) % 12]


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


def _personal_points(jd: float, birth_data: BirthData, known_time: bool) -> dict[str, float]:
    points = {
        "ดวงอาทิตย์": swe.calc_ut(jd, swe.SUN)[0][0],
        "ดวงจันทร์": swe.calc_ut(jd, swe.MOON)[0][0],
    }
    if known_time:
        try:
            _, ascmc = swe.houses(jd, birth_data.latitude, birth_data.longitude, b"P")
            points["ลัคนา"] = ascmc[0]
            points["เมอริเดียน"] = ascmc[1]
        except swe.Error:
            pass
    return points


async def calculate(birth_data: BirthData) -> EngineResult:
    jd, known_time = _julian_day_ut(birth_data)
    personal_points = _personal_points(jd, birth_data, known_time)
    tnp_longitudes = {name: swe.calc_ut(jd, swe_id)[0][0] for name, swe_id in TNP_SWE_IDS.items()}
    points_kb = _load_points()

    placement_findings: list[Finding] = []
    hit_findings: list[Finding] = []
    themes: list[str] = []

    for point_id, longitude in tnp_longitudes.items():
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

        for name_a, name_b in _pairs(list(personal_points)):
            midpoint = _midpoint(personal_points[name_a], personal_points[name_b])
            orb = _dial90_orb(longitude, midpoint)
            if orb <= MIDPOINT_ORB_DEGREES:
                hit_findings.append(
                    Finding(
                        label=f"{name_a}/{name_b} = {meta['name_th']} (คลาดเคลื่อน {orb:.1f}°)",
                        meaning=(
                            f"{meta['meaning_core']} มีบทบาทสำคัญตรงจุดเชื่อมระหว่าง"
                            f"{name_a}กับ{name_b}ของคุณ"
                        ),
                        weight=0.8,
                    )
                )
                themes.insert(0, meta["keywords"][0])

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

    findings = hit_findings + placement_findings
    summary = findings[0].meaning if findings else "ไม่สามารถคำนวณตำแหน่งดาวได้"

    return EngineResult(
        engine="uranian",
        summary=summary,
        themes=list(dict.fromkeys(themes))[:5],
        raw_findings=findings,
        confidence=0.55 if known_time else 0.35,
    )


def _pairs(items: list[str]) -> list[tuple[str, str]]:
    return [(items[i], items[j]) for i in range(len(items)) for j in range(i + 1, len(items))]
