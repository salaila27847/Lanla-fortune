"""Tests for the real Uranian engine (Phase 3 — replaces the Phase 1
mock). Keep test_engine_contracts.py's schema check separate; this file
checks the actual astronomical calculation and knowledge-base content.
"""

from __future__ import annotations

from datetime import date, time

import pytest
import swisseph as swe
import yaml

from app.core.schema import BirthData
from app.modules.uranian.engine import (
    CLASSICAL_SWE_IDS,
    KB_DIR,
    PERSONAL_POINT_IDS,
    SIGNIFICANT_ORB_DEGREES,
    TNP_SWE_IDS,
    _angular_distance,
    _antiscia_finding,
    _antiscion,
    _dial90_orb,
    _dial225_orb,
    _dial_fold_orb,
    _factor_category,
    _factor_display_name,
    _factor_keywords,
    _find_antiscia_contacts,
    _find_pictures,
    _house_finding,
    _house_for_longitude,
    _julian_day_ut,
    _load_axis_meanings,
    _load_factors,
    _load_house_meanings,
    _load_planetary_pictures,
    _load_points,
    _load_signs,
    _load_witte_pictures,
    _midpoint,
    _midpoint_matrix,
    _picture_finding,
    _sign_for_longitude,
    _significance_suffix,
    calculate,
)

BIRTH_WITH_TIME = BirthData(
    date=date(1990, 1, 1),
    time=time(6, 30),
    place="Bangkok",
    latitude=13.7563,
    longitude=100.5018,
    timezone="Asia/Bangkok",
)

BIRTH_WITHOUT_TIME = BirthData(
    date=date(1990, 1, 1),
    time=None,
    place="Bangkok",
    latitude=13.7563,
    longitude=100.5018,
    timezone="Asia/Bangkok",
)


def test_points_kb_covers_all_eight_tnps():
    points = _load_points()
    assert set(points) == set(TNP_SWE_IDS)
    for point in points.values():
        assert point["meaning_core"]
        assert point["keywords"]


def test_signs_kb_has_twelve_signs_in_order():
    signs = _load_signs()
    assert len(signs) == 12
    assert [s["start_degree"] for s in signs] == [i * 30 for i in range(12)]


def test_sign_lookup_wraps_correctly():
    assert _sign_for_longitude(0)["id"] == "aries"
    assert _sign_for_longitude(29.9)["id"] == "aries"
    assert _sign_for_longitude(30)["id"] == "taurus"
    assert _sign_for_longitude(359.9)["id"] == "pisces"


def test_midpoint_uses_shorter_arc():
    assert _midpoint(10, 20) == 15
    # 350 and 10 are 20 apart via 0, not 340 apart the long way
    assert _midpoint(350, 10) == 0


def test_dial90_orb_wraps_within_quadrant():
    assert _dial90_orb(10, 10) == 0
    assert _dial90_orb(10, 100) == pytest.approx(
        0.0, abs=1e-9
    )  # 90° apart: square/opposition family


def test_dial90_orb_catches_the_semisquare_sesquiquadrate_family():
    # Folding at 45° (not 90°) is the fix: Witte's own dial reads
    # semisquare/sesquiquadrate as a hit too ("show as oppositions"),
    # so 45°/135° apart must register as tightly as 90°/180° apart.
    assert _dial90_orb(0, 45) == pytest.approx(0.0, abs=1e-9)
    assert _dial90_orb(0, 135) == pytest.approx(0.0, abs=1e-9)
    assert _dial90_orb(0, 225) == pytest.approx(0.0, abs=1e-9)
    assert _dial90_orb(0, 315) == pytest.approx(0.0, abs=1e-9)


def test_dial90_orb_maxes_out_at_the_true_midpoint_between_hard_aspects():
    # 22.5° apart is exactly between two hard-aspect-family points (0°
    # and 45°) — the worst case for this fold, and not a hit at any
    # sane orb. Confirms the fold doesn't over-match.
    assert _dial90_orb(0, 22.5) == pytest.approx(22.5)


def test_antiscion_mirrors_across_the_solstitial_axis():
    assert _antiscion(0) == pytest.approx(180.0)  # Aries <-> Libra
    assert _antiscion(90) == pytest.approx(90.0)  # Cancer is its own antiscion
    assert _antiscion(270) == pytest.approx(270.0)  # so is Capricorn
    assert _antiscion(60) == pytest.approx(120.0)  # Gemini 0 <-> Leo 0, both 30 from Cancer


def test_antiscion_is_its_own_inverse():
    for longitude in (0, 15, 90, 183.4, 270, 359.9):
        assert _antiscion(_antiscion(longitude)) == pytest.approx(longitude, abs=1e-9)


def test_angular_distance_takes_the_shorter_way_around():
    assert _angular_distance(10, 20) == pytest.approx(10.0)
    assert _angular_distance(350, 10) == pytest.approx(20.0)
    assert _angular_distance(0, 180) == pytest.approx(180.0)


def test_dial_fold_orb_is_generic_over_fold_size():
    assert _dial_fold_orb(0, 90, 90.0) == pytest.approx(0.0, abs=1e-9)
    assert _dial_fold_orb(0, 45, 90.0) == pytest.approx(45.0)  # the old (buggy) 90°-only behavior
    assert _dial90_orb(a=0, b=45) == pytest.approx(_dial_fold_orb(0, 45, 45.0))


def test_dial225_orb_catches_the_semi_octile_family_the_90_dial_misses():
    # 22.5°/67.5°/112.5°/157.5° apart are real hits on the 16th-harmonic
    # dial but never register on the (45°-folded) 90° dial.
    for offset in (22.5, 67.5, 112.5, 157.5, 202.5, 337.5):
        assert _dial225_orb(0, offset) == pytest.approx(0.0, abs=1e-9)
        assert _dial90_orb(0, offset) == pytest.approx(22.5)  # a genuine miss on the coarser dial
    # Anything already a hit on the 90° dial is also a hit on the 22.5° dial (superset).
    assert _dial225_orb(0, 45) == pytest.approx(0.0, abs=1e-9)


def test_significance_suffix_only_appears_within_the_tight_orb():
    assert _significance_suffix(SIGNIFICANT_ORB_DEGREES) != ""
    assert _significance_suffix(SIGNIFICANT_ORB_DEGREES + 0.01) == ""


@pytest.mark.asyncio
async def test_calculate_with_known_time():
    result = await calculate(BIRTH_WITH_TIME)
    assert result.engine == "uranian"
    assert result.confidence == 0.55
    assert len(result.raw_findings) >= 8
    assert "mock" not in result.summary.lower()


@pytest.mark.asyncio
async def test_calculate_without_known_time_has_lower_confidence_and_caveat():
    result = await calculate(BIRTH_WITHOUT_TIME)
    assert result.confidence == 0.35
    assert any("ไม่ทราบเวลาเกิด" in f.label for f in result.raw_findings)


@pytest.mark.asyncio
async def test_calculate_is_deterministic_for_the_same_birth_data():
    first = await calculate(BIRTH_WITH_TIME)
    second = await calculate(BIRTH_WITH_TIME)
    assert [f.label for f in first.raw_findings] == [f.label for f in second.raw_findings]


# ---------- factors.yaml / planetary_pictures.yaml / axis_meanings.yaml ----------


def test_factors_kb_covers_the_other_fourteen_factors():
    factors = _load_factors()
    expected = {"SUN", "MOON", "M", "A", "NODE", "ARIES"} | {
        "MERCURY",
        "VENUS",
        "MARS",
        "JUPITER",
        "SATURN",
        "URANUS",
        "NEPTUNE",
        "PLUTO",
    }
    assert set(factors) == expected
    for factor in factors.values():
        assert factor["meaning_core"]
        assert factor["keywords"]
        assert factor["category"] in {"personal_point", "planet"}


def test_all_twenty_two_factors_are_resolvable():
    """factors.yaml (14) + points.yaml (8 TNPs, lowercase ids) together must
    cover every factor id the engine can produce in a picture."""
    all_ids = set(_load_factors()) | {tnp.upper() for tnp in TNP_SWE_IDS}
    assert len(all_ids) == 22
    for factor_id in all_ids:
        assert _factor_display_name(factor_id)
        assert _factor_keywords(factor_id)


def test_factor_category_classifies_tnps_planets_and_personal_points():
    assert _factor_category("CUPIDO") == "transneptunian"
    assert _factor_category("MERCURY") == "planet"
    assert _factor_category("SUN") == "personal_point"


def test_planetary_pictures_kb_has_no_duplicate_pairs():
    pictures = _load_planetary_pictures()
    assert len(pictures) == 50
    for entry in pictures.values():
        assert entry["meaning_th"]
        assert entry["source_ref"]


def test_axis_meanings_kb_has_m_axis_paired_with_every_other_factor():
    axis_m = _load_axis_meanings()["M"]
    all_ids = set(_load_factors()) | {tnp.upper() for tnp in TNP_SWE_IDS}
    assert set(axis_m) == all_ids - {"M"}


@pytest.mark.parametrize("axis_id", ["A", "MOON", "NODE"])
def test_axis_meanings_kb_has_full_coverage_for_a_moon_node_axes(axis_id):
    axis = _load_axis_meanings()[axis_id]
    all_ids = set(_load_factors()) | {tnp.upper() for tnp in TNP_SWE_IDS}
    assert set(axis) == all_ids - {axis_id}


def test_axis_meanings_kb_sun_axis_covers_all_but_two_undocumented_factors():
    # The source book never gives Sun+Apollon / Sun+Admetos meanings.
    axis_sun = _load_axis_meanings()["SUN"]
    all_ids = set(_load_factors()) | {tnp.upper() for tnp in TNP_SWE_IDS}
    assert set(axis_sun) == all_ids - {"SUN", "APOLLON", "ADMETOS"}


def test_witte_pictures_kb_covers_all_twenty_one_meridian_base_pairs():
    witte = _load_witte_pictures()
    all_ids = set(_load_factors()) | {tnp.upper() for tnp in TNP_SWE_IDS}
    m_pairs = {pair for pair in witte if "M" in pair}
    assert {next(iter(pair - {"M"})) for pair in m_pairs} == all_ids - {"M"}


def test_witte_pictures_kb_covers_all_twenty_aries_base_pairs():
    # M+ARIES lives in the Meridian section already, so Aries's own section
    # only needs the other 20 factors.
    witte = _load_witte_pictures()
    all_ids = set(_load_factors()) | {tnp.upper() for tnp in TNP_SWE_IDS}
    aries_pairs = {pair for pair in witte if "ARIES" in pair and "M" not in pair}
    assert {next(iter(pair - {"ARIES"})) for pair in aries_pairs} == all_ids - {"ARIES", "M"}


def test_witte_pictures_kb_third_factors_are_valid_and_distinct_from_the_pair():
    witte = _load_witte_pictures()
    all_ids = set(_load_factors()) | {tnp.upper() for tnp in TNP_SWE_IDS}
    for pair, entries in witte.items():
        assert entries, pair
        for third_factor, meaning in entries.items():
            assert third_factor in all_ids
            assert third_factor not in pair
            assert meaning.strip()


def test_witte_pictures_kb_has_no_duplicate_base_pairs():
    data = yaml.safe_load((KB_DIR / "witte_pictures.yaml").read_text(encoding="utf-8"))
    seen = set()
    for base_pair in data["base_pairs"]:
        key = frozenset(base_pair["factors"])
        assert key not in seen, base_pair["factors"]
        seen.add(key)


# ---------- planetary picture detection (synthetic positions) ----------


def test_type1_picture_detected_when_factor_sits_on_a_midpoint():
    # M-KRONOS midpoint is 20; JUPITER sits right on it.
    positions = {"M": 0.0, "KRONOS": 40.0, "JUPITER": 20.0, "SATURN": 200.0}
    midpoints = _midpoint_matrix(positions)
    pictures = [
        p
        for p in _find_pictures(positions, PERSONAL_POINT_IDS)
        if p["type"] == "type1" and p["factors"] == frozenset({"M", "KRONOS", "JUPITER"})
    ]
    assert len(pictures) == 1
    assert pictures[0]["orb"] < 0.01
    assert midpoints[frozenset({"M", "KRONOS"})] == pytest.approx(20.0)


def test_type1_picture_out_of_orb_is_not_detected():
    positions = {"M": 0.0, "KRONOS": 40.0, "JUPITER": 25.0}  # 5° off the 20° midpoint
    pictures = _find_pictures(positions, PERSONAL_POINT_IDS)
    assert not any(p["factors"] == frozenset({"M", "KRONOS", "JUPITER"}) for p in pictures)


def test_type2_picture_detected_when_two_midpoints_coincide():
    # M/MOON midpoint = 10; VENUS/SUN midpoint = 10 too.
    positions = {"M": 0.0, "MOON": 20.0, "VENUS": 11.0, "SUN": 9.0}
    pictures = [
        p
        for p in _find_pictures(positions, PERSONAL_POINT_IDS)
        if p["type"] == "type2" and p["factors"] == frozenset({"M", "MOON", "VENUS", "SUN"})
    ]
    assert len(pictures) == 1


def test_type2_picture_requires_four_distinct_factors():
    positions = {"M": 0.0, "MOON": 20.0, "SUN": 10.0}
    pictures = _find_pictures(positions, PERSONAL_POINT_IDS)
    assert not any(p["type"] == "type2" for p in pictures)


def test_pictures_without_a_personal_point_are_filtered_out():
    # MERCURY/SATURN midpoint hit by VENUS — no personal point involved.
    positions = {"MERCURY": 0.0, "SATURN": 40.0, "VENUS": 20.0}
    pictures = _find_pictures(positions, PERSONAL_POINT_IDS)
    assert pictures == []


def test_picture_finding_uses_glossary_meaning_when_a_pair_matches():
    # witte_pictures.yaml now covers the whole book (226/231 base pairs), so a
    # pair-only fixture needs a hit that's specifically absent for that pair.
    # NEPTUNE+ZEUS is in witte_pictures.yaml but its SATURN entry was lost to
    # OCR damage (see the pair's `# missing:` note), so this hit falls through
    # to planetary_pictures.yaml's pair-only entry -- exercising that tier.
    picture = {
        "type": "type1",
        "pair": ("NEPTUNE", "ZEUS"),
        "hit": "SATURN",
        "factors": frozenset({"NEPTUNE", "ZEUS", "SATURN"}),
        "orb": 0.2,
    }
    finding = _picture_finding(picture)
    assert "จินตนาการเชิงสร้างสรรค์" in finding.meaning
    assert finding.weight == 0.75


def test_picture_finding_label_marks_a_tight_orb_as_significant():
    tight = {
        "type": "type1",
        "pair": ("NEPTUNE", "ZEUS"),
        "hit": "SATURN",
        "factors": frozenset({"NEPTUNE", "ZEUS", "SATURN"}),
        "orb": 0.1,
    }
    loose = {**tight, "orb": 1.4}
    assert "★" in _picture_finding(tight).label
    assert "★" not in _picture_finding(loose).label


def test_picture_finding_prefers_witte_exact_match_over_generic_glossary():
    # M+VULKANUS=CUPIDO has a specific entry in witte_pictures.yaml (the real
    # Rules for Planetary Pictures glossary) — it should win over
    # planetary_pictures.yaml's pair-only entries and the generic fallback.
    picture = {
        "type": "type1",
        "pair": ("M", "VULKANUS"),
        "hit": "CUPIDO",
        "factors": frozenset({"M", "VULKANUS", "CUPIDO"}),
        "orb": 0.2,
    }
    finding = _picture_finding(picture)
    assert finding.weight == 0.95
    assert finding.meaning.startswith("อำนาจและอิทธิพลผ่านครอบครัวหรือชุมชน")


def test_picture_finding_uses_witte_exact_match_for_a_non_m_base_pair():
    # ARIES+JUPITER=MARS comes from the Aries section, not the Meridian one —
    # confirms the lookup isn't hardcoded to M-containing pairs.
    picture = {
        "type": "type1",
        "pair": ("ARIES", "JUPITER"),
        "hit": "MARS",
        "factors": frozenset({"ARIES", "JUPITER", "MARS"}),
        "orb": 0.1,
    }
    finding = _picture_finding(picture)
    assert finding.weight == 0.95
    assert finding.meaning.startswith("ความสุขในความรักกับผู้ชาย")


def test_picture_finding_ignores_witte_pictures_for_type2():
    # witte_pictures.yaml only covers Type I (pair + single third factor) —
    # Type II pictures must still fall through to the generic glossary/composition.
    picture = {
        "type": "type2",
        "pair": ("M", "VULKANUS"),
        "pair_b": ("CUPIDO", "ZEUS"),
        "factors": frozenset({"M", "VULKANUS", "CUPIDO", "ZEUS"}),
        "orb": 0.2,
    }
    finding = _picture_finding(picture)
    assert finding.weight != 0.95


def test_picture_finding_falls_back_to_generic_composition_when_unmatched():
    # witte_pictures.yaml now covers the whole book, but 5 base pairs never
    # made it in even as a whole entry -- OCR damage from the Ascendant/Sun
    # chapters (done in an earlier session), never recovered. APOLLON+SUN is
    # one of them, and it's absent from planetary_pictures.yaml's curated 50
    # pairs too, so this exercises the generic keyword-composition tier.
    picture = {
        "type": "type1",
        "pair": ("APOLLON", "SUN"),
        "hit": "MOON",
        "factors": frozenset({"APOLLON", "SUN", "MOON"}),
        "orb": 0.2,
    }
    finding = _picture_finding(picture)
    assert finding.weight == 0.45
    assert "เชื่อมโยงกันในดวงชะตา" in finding.meaning


def test_picture_finding_appends_axis_m_note_when_m_is_involved():
    picture = {
        "type": "type1",
        "pair": ("M", "SATURN"),
        "hit": "SUN",
        "factors": frozenset({"M", "SATURN", "SUN"}),
        "orb": 0.2,
    }
    finding = _picture_finding(picture)
    assert "บนแกน M" in finding.meaning


def test_picture_finding_appends_axis_note_for_a_non_m_axis():
    # NODE is now a documented axis too, not just M.
    picture = {
        "type": "type1",
        "pair": ("NODE", "VENUS"),
        "hit": "MARS",
        "factors": frozenset({"NODE", "VENUS", "MARS"}),
        "orb": 0.2,
    }
    finding = _picture_finding(picture)
    assert "บนแกน NODE" in finding.meaning


def test_picture_finding_appends_notes_for_every_axis_present_in_the_picture():
    # Both M and SUN are axes, and both are present in this picture — each
    # should contribute its own axis note, not just the first one found.
    picture = {
        "type": "type2",
        "pair": ("M", "MARS"),
        "pair_b": ("SUN", "SATURN"),
        "factors": frozenset({"M", "MARS", "SUN", "SATURN"}),
        "orb": 0.2,
    }
    finding = _picture_finding(picture)
    assert "บนแกน M" in finding.meaning
    assert "บนแกน SUN" in finding.meaning


# ---------- antiscia ----------


def test_antiscia_contact_detected_when_a_factor_sits_on_a_mirror_point():
    # antiscion(SUN=100) = 80; MOON sits right on it.
    positions = {"SUN": 100.0, "MOON": 80.0, "MARS": 200.0}
    contacts = _find_antiscia_contacts(positions, PERSONAL_POINT_IDS)
    assert len(contacts) == 1
    assert contacts[0]["pair"] == ("MOON", "SUN")
    assert contacts[0]["orb"] < 0.01


def test_antiscia_contact_is_symmetric():
    # Same configuration read from the other factor's side should agree.
    positions = {"SUN": 100.0, "MOON": 80.0}
    contacts = _find_antiscia_contacts(positions, PERSONAL_POINT_IDS)
    assert len(contacts) == 1
    assert contacts[0]["factors"] == frozenset({"SUN", "MOON"})


def test_antiscia_contact_out_of_orb_is_not_detected():
    positions = {"SUN": 100.0, "MOON": 75.0}  # 5 off the 80 antiscion
    assert _find_antiscia_contacts(positions, PERSONAL_POINT_IDS) == []


def test_antiscia_contacts_without_a_personal_point_are_filtered_out():
    positions = {"MERCURY": 100.0, "VENUS": 80.0}
    assert _find_antiscia_contacts(positions, PERSONAL_POINT_IDS) == []


def test_antiscia_finding_uses_glossary_meaning_when_a_pair_matches():
    glossary_pair = next(iter(_load_planetary_pictures()))
    a, b = sorted(glossary_pair)
    contact = {"type": "antiscia", "pair": (a, b), "factors": frozenset((a, b)), "orb": 0.3}
    finding = _antiscia_finding(contact)
    assert finding.weight == 0.5
    assert "จุดสะท้อนแกนครีษมายัน" in finding.meaning


def test_antiscia_finding_label_marks_a_tight_orb_as_significant():
    glossary_pair = next(iter(_load_planetary_pictures()))
    a, b = sorted(glossary_pair)
    tight = {"type": "antiscia", "pair": (a, b), "factors": frozenset((a, b)), "orb": 0.1}
    loose = {**tight, "orb": 1.4}
    assert "★" in _antiscia_finding(tight).label
    assert "★" not in _antiscia_finding(loose).label


def test_antiscia_finding_falls_back_to_generic_composition_when_unmatched():
    contact = {
        "type": "antiscia",
        "pair": ("ARIES", "MOON"),
        "factors": frozenset({"ARIES", "MOON"}),
        "orb": 0.3,
    }
    assert frozenset({"ARIES", "MOON"}) not in _load_planetary_pictures()
    finding = _antiscia_finding(contact)
    assert finding.weight == 0.35
    assert "antiscion" in finding.meaning


# ---------- house_meanings.yaml / Meridian house placement ----------


def test_house_meanings_kb_covers_ten_classical_planets_and_eight_tnps():
    house_meanings = _load_house_meanings()
    expected = set(CLASSICAL_SWE_IDS) | {tnp.upper() for tnp in TNP_SWE_IDS}
    assert set(house_meanings) == expected
    for meaning in house_meanings.values():
        assert meaning


def test_house_for_longitude_handles_unequal_meridian_house_sizes():
    # Cusps deliberately unequal (Meridian houses aren't 30° apart on the
    # ecliptic) — house 1 spans 200->240 (40 wide), house 2 spans 240->260.
    cusps = (200.0, 240.0, 260.0, 280.0, 300.0, 320.0, 340.0, 0.0, 20.0, 40.0, 60.0, 80.0)
    assert _house_for_longitude(210.0, cusps) == 1
    assert _house_for_longitude(239.9, cusps) == 1
    assert _house_for_longitude(240.0, cusps) == 2
    assert _house_for_longitude(250.0, cusps) == 2


def test_house_for_longitude_wraps_across_the_360_seam():
    cusps = (350.0, 20.0, 50.0, 80.0, 110.0, 140.0, 170.0, 200.0, 230.0, 260.0, 290.0, 320.0)
    assert _house_for_longitude(0.0, cusps) == 1
    assert _house_for_longitude(349.9, cusps) == 12
    assert _house_for_longitude(10.0, cusps) == 1


def test_house_finding_reports_house_number_and_kb_meaning():
    finding = _house_finding("MARS", 5)
    assert "เรือนที่ 5" in finding.label
    assert finding.meaning == _load_house_meanings()["MARS"]
    assert finding.weight == 0.4


@pytest.mark.asyncio
async def test_calculate_with_known_time_includes_all_eighteen_house_placements():
    result = await calculate(BIRTH_WITH_TIME)
    house_labels = [f for f in result.raw_findings if "อยู่เรือนที่" in f.label]
    assert len(house_labels) == 18
    factor_names = {_factor_display_name(f) for f in _load_house_meanings()}
    assert all(any(name in f.label for name in factor_names) for f in house_labels)


@pytest.mark.asyncio
async def test_calculate_without_known_time_has_no_house_placements():
    result = await calculate(BIRTH_WITHOUT_TIME)
    assert not any("อยู่เรือนที่" in f.label for f in result.raw_findings)


@pytest.mark.asyncio
async def test_calculate_house_placement_matches_direct_meridian_house_lookup():
    jd, _ = _julian_day_ut(BIRTH_WITH_TIME)
    cusps, _ = swe.houses(jd, BIRTH_WITH_TIME.latitude, BIRTH_WITH_TIME.longitude, b"X")
    sun_longitude = swe.calc_ut(jd, swe.SUN)[0][0]
    expected_house = _house_for_longitude(sun_longitude, cusps)

    result = await calculate(BIRTH_WITH_TIME)
    sun_label = next(f for f in result.raw_findings if "อาทิตย์" in f.label and "อยู่เรือนที่" in f.label)
    assert f"เรือนที่ {expected_house}" in sun_label.label
