"""Uranian astrology engine.

Computes all 22 Hamburg School factors — the 10 classical bodies (Sun
through Pluto), the 8 trans-Neptunian points (Cupido, Hades, Zeus,
Kronos, Apollon, Admetos, Vulkanus, Poseidon), the (true) Node, the
Aries Point, and — when the birth time is known — Ascendant/Midheaven —
via pyswisseph's built-in Moshier ephemeris (no external data files or
network access needed).

Four kinds of findings are produced:

1. Placement findings — each of the 8 TNPs by zodiac sign (unchanged
   from the original stub-replacement implementation).
2. Planetary-picture findings — 90°-dial midpoint structures among all
   22 factors: Type I (a single factor sits on another pair's midpoint,
   e.g. Mars/Saturn=Uranus) and Type II (two pairs' midpoints coincide,
   e.g. M/Moon=Venus/Sun). "90°-dial" means the full hard-aspect family
   the dial reads as a hit — conjunction, semisquare, square,
   sesquiquadrate, and opposition (see _dial90_orb) — not just
   conjunction/square/opposition. Only pictures involving at least one
   personal point (Sun, Moon, M, A, Node, Aries Point) are kept. Each
   picture is matched against the curated combinations glossary;
   unmatched pictures fall back to a meaning composed from each
   factor's own keywords. A picture whose orb is tight enough
   (≤ SIGNIFICANT_ORB_DEGREES) gets a "reads as unavoidable" marker
   appended to its label — the dial-hierarchy principle that a
   near-exact hit is a stronger theme, not just a present one.
3. Antiscia-contact findings — a factor sitting on another factor's
   antiscion (its mirror point across the Cancer/Capricorn solstitial
   axis, same declination). Symmetric and independent of the midpoint
   search above; per the source material antiscia read weaker than a
   direct picture, so these are always appended after the Type I/II
   picture findings, never mixed in ahead of them by orb alone. See
   backend/app/knowledge_base/uranian/research/uranian-niggemann-primary-source.md
   section 3 for the formula and the primary-source citation.
4. House-placement findings — the 10 classical planets and 8 TNPs each
   assigned to one of the 12 houses of the Meridian house system (the
   axial-rotation/equatorial system Uranian astrology uses — 10th cusp
   equals M exactly, 1st cusp is the Equatorial Ascendant/East Point
   rather than the ecliptic Ascendant). pyswisseph implements this
   directly via swe.houses(..., hsys=b"X"); no equal-house-from-M
   projection needs to be hand-rolled (see _house_cusps). Only computed
   when the birth time is known, since the cusps depend on it the same
   way A/M do. Node/Aries Point/M/A are excluded — the source material
   doesn't give house-placement meanings for them, and M/A define
   cusps 10/1 rather than falling inside a house themselves. Each
   finding's meaning combines the factor's own house nature
   (house_meanings.yaml) with that house number's general topic
   (house_number_meanings.yaml) — e.g. Mars in house 5 reads
   differently from Mars in house 8 even though both are "Mars'"
   nature. _house_cusps/_house_placements are also reused by
   main.py to place directed/transit/relocated positions into houses
   for the forecast endpoints (see solar_arc.py/transit.py docstrings).

Meanings are assembled from backend/app/knowledge_base/uranian/
(points.yaml, signs.yaml, factors.yaml, planetary_pictures.yaml,
axis_meanings.yaml, witte_pictures.yaml, house_meanings.yaml,
house_number_meanings.yaml), never hardcoded here.

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

ANTISCIA_ORB_DEGREES = 1.5  # a mirror-point hit reads like a direct conjunction, so it gets the same tight orb as Type I
MAX_ANTISCIA_FINDINGS = (
    5  # antiscia are the weakest finding type; keep them a minority of the payload
)

SIGNIFICANT_ORB_DEGREES = 0.5  # a hit this tight reads as a near-exact, harder-to-avoid theme — see _significance_suffix()


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


@lru_cache
def _load_witte_pictures() -> dict[frozenset[str], dict[str, str]]:
    """The exact "Rules for Planetary Pictures" glossary: base pair -> third
    factor -> specific meaning (Type I only). Far more granular than
    planetary_pictures.yaml's pair-only entries, so _picture_finding()
    checks this first for Type I pictures."""
    data = yaml.safe_load((KB_DIR / "witte_pictures.yaml").read_text(encoding="utf-8"))
    return {
        frozenset(base_pair["factors"]): {
            entry["third_factor"]: entry["meaning_th"] for entry in base_pair["entries"]
        }
        for base_pair in data["base_pairs"]
    }


@lru_cache
def _load_house_meanings() -> dict[str, str]:
    """factor id -> the general nature of the house that factor occupies
    (independent of which house number). Covers the 10 classical planets
    + 8 TNPs only — see house_meanings.yaml's header for why Node/Aries
    Point/M/A are excluded."""
    data = yaml.safe_load((KB_DIR / "house_meanings.yaml").read_text(encoding="utf-8"))
    return {entry["factor"]: entry["meaning_th"] for entry in data["house_meanings"]}


@lru_cache
def _load_house_number_meanings() -> dict[int, str]:
    """house number (1-12) -> its general topic, independent of which
    factor occupies it — complements _load_house_meanings() (which is
    "this factor's house nature" independent of the house number)."""
    data = yaml.safe_load((KB_DIR / "house_number_meanings.yaml").read_text(encoding="utf-8"))
    return {entry["house"]: entry["meaning_th"] for entry in data["house_number_meanings"]}


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


def _dial_fold_orb(a: float, b: float, fold_degrees: float) -> float:
    """Distance to the nearest multiple of fold_degrees between two
    longitudes — the family of hard aspects a dial of that size reads as
    a "hit" (a single dial position), since every multiple of
    fold_degrees folds onto the same point."""
    diff = abs((a - b) % fold_degrees)
    return min(diff, fold_degrees - diff)


def _dial90_orb(a: float, b: float) -> float:
    """Hard-aspect-family distance the 90° dial reads as a hit:
    conjunction, semisquare, square, sesquiquadrate, and opposition
    (0°/45°/90°/135°/180°, the 8th harmonic) — folded at 45°, not 90°.

    Folding at 90° alone would only catch the 0°/90°/180°/270° family
    (a-b near a multiple of 90) and silently miss 45°/135°/225°/315°
    (semisquare/sesquiquadrate) entirely, even though Witte's own
    description of the dial reads both as valid hits: "squares and
    oppositions show as conjunctions, while the semi- and
    sesqui-squares show as oppositions" — i.e. the same dial position,
    just read from either the "same point" or "opposite point" side.
    Ludwig Rudolph made the same point about the 45° dial specifically:
    it isn't a separate instrument, it's the 90° dial's own data read
    from the other side. Folding at 45° captures both readings in one
    check. See backend/app/knowledge_base/uranian/research/
    uranian-dial-hierarchy.md for the full citation trail."""
    return _dial_fold_orb(a, b, 45.0)


SEMI_OCTILE_DIAL_DEGREES = 22.5  # the 16th harmonic — finer than the 90° dial's own 8th-harmonic family; see _dial225_orb in transit.py


def _dial225_orb(a: float, b: float) -> float:
    """16th-harmonic hard-aspect-family distance (22.5° increments) —
    the full semi-octile family (22.5°/45°/67.5°/90°/112.5°/135°/157.5°/
    180°...), a strict superset of _dial90_orb's 8th-harmonic family.
    Used for the fine "which day" timing pass in transit.py, not for
    natal/directed picture-finding — see the module docstring."""
    return _dial_fold_orb(a, b, SEMI_OCTILE_DIAL_DEGREES)


def _antiscion(longitude: float) -> float:
    """Mirror a longitude across the Cancer(90°)/Capricorn(270°) axis —
    the point with the same declination on the other side of the
    solstitial axis. Symmetric: antiscion(antiscion(x)) == x."""
    return (180.0 - longitude) % 360.0


def _angular_distance(a: float, b: float) -> float:
    """Shortest separation between two longitudes on the full 360° circle."""
    diff = abs(a - b) % 360
    return min(diff, 360 - diff)


HOUSE_SYSTEM_MERIDIAN = b"X"  # pyswisseph's axial-rotation/Meridian house system —
# verified via swe.house_name(b"X") == "axial rotation system/Meridian houses". Its
# 10th cusp equals M and its 1st cusp is the Equatorial Ascendant (East Point), matching
# Uranian astrology's house convention exactly, so no equal-house-from-M projection
# needs to be computed by hand — this one library call already does the equatorial
# division + great-circle-to-ecliptic projection.


def _house_cusps(jd: float, latitude: float, longitude: float) -> tuple[float, ...] | None:
    """The 12 Meridian-system house cusps, in zodiacal order starting at
    the 1st house, for the given moment and location. None when the
    ephemeris call fails. Takes lat/lon directly (not a BirthData) so
    solar_arc.py/transit.py can reuse it for a relocated site rather than
    only the birth location — see main.py's relocation handling."""
    try:
        cusps, _ = swe.houses(jd, latitude, longitude, HOUSE_SYSTEM_MERIDIAN)
        return cusps
    except swe.Error:
        return None


def _house_for_longitude(longitude: float, cusps: tuple[float, ...]) -> int:
    """Which of the 12 houses a longitude falls in, given that system's
    cusps in zodiacal order. Meridian houses aren't equal-sized on the
    ecliptic (only on the equator, before the great-circle projection), so
    this is the general cusp-to-cusp containment test rather than a fixed
    30°-per-house lookup."""
    for house_index in range(12):
        start = cusps[house_index]
        end = cusps[(house_index + 1) % 12]
        span = (end - start) % 360
        offset = (longitude - start) % 360
        if offset < span:
            return house_index + 1
    return 12


def _house_placements(positions: dict[str, float], cusps: tuple[float, ...]) -> dict[str, int]:
    """Which house each of house_meanings.yaml's 18 factors (10 classical
    planets + 8 TNPs) falls in, given a set of cusps — generic over
    *whose* cusps and *whose* positions are passed in, so the natal
    engine, solar_arc.py (directed positions against radix cusps), and
    main.py's transit/relocation handling can all share it. Silently
    skips any factor missing from positions (e.g. a caller that only
    passes a subset)."""
    house_meanings = _load_house_meanings()
    return {
        factor_id: _house_for_longitude(positions[factor_id], cusps)
        for factor_id in house_meanings
        if factor_id in positions
    }


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


def _find_antiscia_contacts(
    positions: dict[str, float],
    personal_point_ids: frozenset[str],
    orb: float = ANTISCIA_ORB_DEGREES,
) -> list[dict[str, Any]]:
    """A factor sitting on another factor's antiscion. Symmetric —
    a on antiscion(b) implies b on antiscion(a) — so each pair is
    checked once. Kept separate from _find_pictures() since antiscia
    contacts are their own (weaker) finding type, not a midpoint
    structure. Keeps only contacts involving at least one personal
    point, and sorts tightest-orb first."""
    found: list[dict[str, Any]] = []
    for a, b in combinations(positions, 2):
        orb_hit = _angular_distance(positions[a], _antiscion(positions[b]))
        if orb_hit <= orb:
            pair = tuple(sorted((a, b)))
            found.append(
                {"type": "antiscia", "pair": pair, "factors": frozenset(pair), "orb": orb_hit}
            )

    found = [contact for contact in found if contact["factors"] & personal_point_ids]
    found.sort(key=lambda contact: contact["orb"])
    return found


def _significance_suffix(orb: float) -> str:
    """A short marker appended to a finding's label when its orb is
    tight enough to read as a near-exact hit, not just a loose one —
    the same "zoom in with a finer dial to see if it's a major theme"
    principle the 45°/22.5° dials apply, expressed here as a stricter
    orb threshold on the same underlying distance rather than a
    separate fold (see uranian-dial-hierarchy.md section 2)."""
    return " ★ ตรงเป๊ะ (เรื่องใหญ่ที่หลีกเลี่ยงยาก)" if orb <= SIGNIFICANT_ORB_DEGREES else ""


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
        label = (
            f"{disp(a)}/{disp(b)} = {disp(c)} (คลาดเคลื่อน {picture['orb']:.2f}°)"
            f"{_significance_suffix(picture['orb'])}"
        )
    else:
        a, b = picture["pair"]
        c, d = picture["pair_b"]
        label = (
            f"{disp(a)}/{disp(b)} = {disp(c)}/{disp(d)} (คลาดเคลื่อน {picture['orb']:.2f}°)"
            f"{_significance_suffix(picture['orb'])}"
        )

    witte_meaning = None
    if picture["type"] == "type1":
        witte_pair = _load_witte_pictures().get(frozenset(picture["pair"]))
        witte_meaning = witte_pair.get(picture["hit"]) if witte_pair else None

    glossary = _load_planetary_pictures()
    matches = [
        glossary[frozenset(combo)]
        for combo in combinations(sorted(factors), 2)
        if frozenset(combo) in glossary
    ]

    if witte_meaning:
        meaning = witte_meaning
        weight = 0.95
    elif matches:
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


def _house_finding(factor_id: str, house_number: int) -> Finding:
    meaning = _load_house_meanings()[factor_id]
    topic = _load_house_number_meanings().get(house_number)
    if topic:
        meaning += f" (เรือนที่ {house_number} หมายถึง: {topic})"
    return Finding(
        label=f"{_factor_display_name(factor_id)} อยู่เรือนที่ {house_number} (ระบบเรือนเมริเดียน)",
        meaning=meaning,
        weight=0.4,
    )


def _antiscia_finding(contact: dict[str, Any]) -> Finding:
    a, b = contact["pair"]
    disp = _factor_display_name
    label = (
        f"{disp(a)} พาดจุดสะท้อน (antiscion) ของ {disp(b)} (คลาดเคลื่อน {contact['orb']:.2f}°)"
        f"{_significance_suffix(contact['orb'])}"
    )

    glossary = _load_planetary_pictures()
    match = glossary.get(frozenset((a, b)))
    if match:
        meaning = f"{match['meaning_th']} (เชื่อมโยงผ่านจุดสะท้อนแกนครีษมายัน ผลอ่อนกว่าคอนจังชันจริง)"
        weight = 0.5
    else:
        keywords = [keywords[0] for f in (a, b) if (keywords := _factor_keywords(f))]
        meaning = (
            f"{disp(a)} และ {disp(b)} เชื่อมโยงกันผ่านจุดสะท้อน (antiscion) ข้ามแกนครีษมายัน "
            f"(Cancer/Capricorn) สะท้อนพลัง: {', '.join(dict.fromkeys(keywords))}"
        )
        weight = 0.35

    return Finding(label=label, meaning=meaning, weight=weight)


async def calculate(birth_data: BirthData) -> EngineResult:
    jd, known_time = _julian_day_ut(birth_data)
    positions = _compute_positions(jd, birth_data, known_time)
    points_kb = _load_points()

    placement_findings: list[Finding] = []
    picture_findings: list[Finding] = []
    house_findings: list[Finding] = []
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

    # Appended after the picture findings (never sorted in ahead of them by
    # orb alone) — antiscia read weaker than a direct picture per the source
    # material, regardless of how tight the antiscion hit is.
    antiscia_contacts = _find_antiscia_contacts(positions, PERSONAL_POINT_IDS)[
        :MAX_ANTISCIA_FINDINGS
    ]
    for contact in antiscia_contacts:
        picture_findings.append(_antiscia_finding(contact))
        theme = _picture_theme(contact)
        if theme:
            themes.append(theme)

    if known_time:
        cusps = _house_cusps(jd, birth_data.latitude, birth_data.longitude)
        if cusps is not None:
            for factor_id, house_number in _house_placements(positions, cusps).items():
                house_findings.append(_house_finding(factor_id, house_number))

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

    findings = picture_findings + placement_findings + house_findings
    summary = findings[0].meaning if findings else "ไม่สามารถคำนวณตำแหน่งดาวได้"

    return EngineResult(
        engine="uranian",
        summary=summary,
        themes=list(dict.fromkeys(themes)),
        raw_findings=findings,
        confidence=0.55 if known_time else 0.35,
    )
