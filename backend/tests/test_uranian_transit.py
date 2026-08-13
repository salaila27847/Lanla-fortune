"""Tests for the transit/station/lunar-return/relocation module — see
app/modules/uranian/transit.py for the techniques it covers (wired into
POST /api/forecast in app/main.py)."""

from __future__ import annotations

from datetime import date, time

import pytest
import swisseph as swe

from app.core.schema import BirthData
from app.modules.uranian.engine import _compute_positions, _julian_day_ut
from app.modules.uranian.transit import (
    daily_speed,
    find_lunar_return,
    find_stations_in_range,
    find_transit_pictures,
    relocated_angles,
    transit_forecast,
    transit_positions,
)

BIRTH_WITH_TIME = BirthData(
    date=date(1990, 7, 22),
    time=time(15, 52),
    place="Trang, Thailand",
    latitude=7.5563,
    longitude=99.6114,
    timezone="Asia/Bangkok",
)

BIRTH_WITHOUT_TIME = BirthData(
    date=date(1990, 7, 22),
    time=None,
    place="Trang, Thailand",
    latitude=7.5563,
    longitude=99.6114,
    timezone="Asia/Bangkok",
)


def test_transit_positions_covers_nineteen_factors():
    positions = transit_positions(date(2026, 8, 13))
    expected = {
        "SUN",
        "MOON",
        "MERCURY",
        "VENUS",
        "MARS",
        "JUPITER",
        "SATURN",
        "URANUS",
        "NEPTUNE",
        "PLUTO",
        "CUPIDO",
        "HADES",
        "ZEUS",
        "KRONOS",
        "APOLLON",
        "ADMETOS",
        "VULKANUS",
        "POSEIDON",
        "NODE",
    }
    assert set(positions) == expected
    for factor, lon in positions.items():
        assert 0.0 <= lon < 360.0, f"{factor} out of range: {lon}"


def test_transit_positions_omits_daily_ma_without_birth_data():
    positions = transit_positions(date(2026, 8, 13))
    assert "A" not in positions
    assert "M" not in positions


def test_transit_positions_includes_daily_ma_with_birth_data():
    positions = transit_positions(date(2026, 8, 13), birth_data=BIRTH_WITH_TIME)
    jd = swe.julday(2026, 8, 13, 12.0)
    _, expected_ascmc = swe.houses(jd, BIRTH_WITH_TIME.latitude, BIRTH_WITH_TIME.longitude, b"P")
    assert positions["A"] == pytest.approx(expected_ascmc[0])
    assert positions["M"] == pytest.approx(expected_ascmc[1])


def test_transit_forecast_smoke_test_on_a_real_chart():
    jd, known_time = _julian_day_ut(BIRTH_WITH_TIME)
    natal_positions = _compute_positions(jd, BIRTH_WITH_TIME, known_time)
    pictures = transit_forecast(natal_positions, date(2026, 8, 13))
    for picture in pictures:
        assert picture["type"] in {"type1", "type2"}
        assert 0 <= picture["orb"] <= 1.0  # transit orb is tight


def test_transit_axes_enabled_by_daily_ma_find_purely_transit_pictures():
    # With Daily M/A included, a picture can be entirely "today's sky"
    # (no radix or directed factor at all) as long as it involves today's
    # M or A — this is the "Transit Axes" technique.
    jd, known_time = _julian_day_ut(BIRTH_WITH_TIME)
    natal_positions = _compute_positions(jd, BIRTH_WITH_TIME, known_time)
    pictures = transit_forecast(natal_positions, date(2026, 8, 13), birth_data=BIRTH_WITH_TIME)
    purely_transit = [p for p in pictures if all(f.startswith("t:") for f in p["factors"])]
    assert len(purely_transit) > 0
    assert all(any(f in {"t:A", "t:M"} for f in p["factors"]) for p in purely_transit)


# ---------- find_transit_pictures (synthetic positions) ----------


def test_transit_factor_hitting_a_radix_midpoint_is_detected():
    natal = {"M": 0.0, "KRONOS": 40.0, "SATURN": 200.0}
    transit = {
        "M": 20.2,
        "KRONOS": 90.0,
        "SATURN": 10.0,
    }  # transit "M" near the radix M/KRONOS midpoint (20)
    pictures = find_transit_pictures(natal, transit)
    matches = [p for p in pictures if p["factors"] == frozenset({"r:M", "r:KRONOS", "t:M"})]
    assert len(matches) == 1
    assert matches[0]["orb"] < 0.5


def test_all_radix_picture_is_excluded():
    natal = {
        "M": 0.0,
        "KRONOS": 40.0,
        "SATURN": 200.0,
    }  # r:M/r:KRONOS=r:SATURN exists but is purely radix
    transit = {
        "M": 100.0,
        "KRONOS": 150.0,
        "SATURN": 250.0,
    }  # kept well away from the radix midpoint
    pictures = find_transit_pictures(natal, transit)
    assert not any(p["factors"] == frozenset({"r:M", "r:KRONOS", "r:SATURN"}) for p in pictures)


def test_transit_transit_aspect_requires_a_radix_personal_point():
    # transit Jupiter/Saturn's midpoint hitting transit Mars alone (no
    # personal point anywhere) must be dropped, per the source doc's
    # rule that a transit-transit configuration without a personal-point
    # link is a "world event", not personal.
    natal = {"MERCURY": 0.0}  # no personal points in the natal set at all
    transit = {"JUPITER": 0.0, "SATURN": 40.0, "MARS": 20.0}
    pictures = find_transit_pictures(natal, transit)
    assert pictures == []


def test_transit_transit_aspect_landing_on_a_radix_personal_point_is_kept():
    natal = {"SUN": 20.0}
    transit = {"JUPITER": 0.0, "SATURN": 40.0}  # midpoint = 20, exactly on natal Sun
    pictures = find_transit_pictures(natal, transit)
    matches = [p for p in pictures if p["factors"] == frozenset({"t:JUPITER", "t:SATURN", "r:SUN"})]
    assert len(matches) == 1
    assert matches[0]["orb"] < 0.01


def test_arc_locked_pair_excludes_radix_vs_directed_both_directly_and_cross_paired():
    # directed = radix + one constant arc for every body, so ANY split
    # of {r:Sun, d:Sun, r:Venus, d:Venus} into two pairs is a near-fixed
    # function of the arc alone: both the direct pairing (radix Sun/Venus
    # vs directed Sun/Venus) and the "cross" pairing (radix Sun/directed
    # Venus vs directed Sun/radix Venus) reduce to the same identity —
    # midpoint(x, y+k) == midpoint(x+k, y) for a shared k.
    from app.modules.uranian.transit import _is_arc_locked_pair

    direct = (frozenset({"r:SUN", "r:VENUS"}), frozenset({"d:SUN", "d:VENUS"}))
    cross = (frozenset({"r:SUN", "d:VENUS"}), frozenset({"d:SUN", "r:VENUS"}))
    assert _is_arc_locked_pair(*direct) is True
    assert _is_arc_locked_pair(*cross) is True


def test_arc_locked_pair_does_not_exclude_transit_combinations():
    # Transit motion isn't a shared constant offset from radix (each
    # body moves independently), so no radix/transit or directed/transit
    # split is degenerate this way, however the bodies are split.
    from app.modules.uranian.transit import _is_arc_locked_pair

    radix_vs_transit = (frozenset({"r:SUN", "r:VENUS"}), frozenset({"t:SUN", "t:VENUS"}))
    cross_with_transit = (frozenset({"r:SUN", "t:VENUS"}), frozenset({"t:SUN", "r:VENUS"}))
    assert _is_arc_locked_pair(*radix_vs_transit) is False
    assert _is_arc_locked_pair(*cross_with_transit) is False


def test_same_body_radix_vs_directed_type2_picture_is_excluded_end_to_end():
    # arc=90 makes the radix and directed Sun/Venus midpoints coincide
    # exactly — confirms the exclusion actually reaches find_transit_pictures,
    # not just the _is_arc_locked_pair helper in isolation.
    natal = {"SUN": 0.0, "VENUS": 20.0}
    directed = {"SUN": 90.0, "VENUS": 110.0}
    pictures = find_transit_pictures(natal, transit_positions_={}, directed_positions_=directed)
    assert pictures == []


# ---------- station points ----------


def test_daily_speed_matches_direct_swisseph_call():
    jd = swe.julday(2026, 8, 13, 12.0)
    expected = swe.calc_ut(jd, swe.SATURN)[0][3]
    assert daily_speed("SATURN", date(2026, 8, 13)) == pytest.approx(expected)


def test_find_stations_in_range_finds_known_mercury_retrograde_window():
    # Mercury retrograde Feb-Mar 2026 is a matter of ephemeris fact, not
    # an assumption — this pins the station-scan against real motion.
    stations = find_stations_in_range("MERCURY", date(2026, 2, 1), date(2026, 4, 1))
    assert len(stations) == 2
    assert date(2026, 2, 20) < stations[0] < date(2026, 3, 1)
    assert date(2026, 3, 15) < stations[1] < date(2026, 3, 25)


def test_find_stations_in_range_is_empty_when_no_station_occurs():
    # Saturn is retrograde the entire window here — no sign change.
    stations = find_stations_in_range("SATURN", date(2026, 8, 1), date(2026, 8, 10))
    assert stations == []


# ---------- lunar return ----------


def test_lunar_return_lands_on_the_natal_moon_degree():
    natal_moon = 122.6017
    return_dt = find_lunar_return(natal_moon, date(2026, 8, 13))
    assert return_dt.date() >= date(2026, 8, 13)
    assert (return_dt.date() - date(2026, 8, 13)).days <= 30

    jd = swe.julday(
        return_dt.year,
        return_dt.month,
        return_dt.day,
        return_dt.hour + return_dt.minute / 60 + return_dt.second / 3600,
    )
    moon_lon_at_return = swe.calc_ut(jd, swe.MOON)[0][0]
    diff = abs((moon_lon_at_return - natal_moon + 180) % 360 - 180)
    assert diff < 0.01


def test_lunar_return_raises_if_not_found_within_max_days():
    with pytest.raises(ValueError):
        find_lunar_return(122.6017, date(2026, 8, 13), max_days=1)


# ---------- relocation ----------


def test_relocated_angles_differ_from_natal_for_a_different_location():
    jd, known_time = _julian_day_ut(BIRTH_WITH_TIME)
    natal_positions = _compute_positions(jd, BIRTH_WITH_TIME, known_time)

    relocated = relocated_angles(BIRTH_WITH_TIME, 13.7563, 100.5018)  # Bangkok instead of Trang
    assert relocated["A"] != pytest.approx(natal_positions["A"], abs=0.01)
    assert 0.0 <= relocated["A"] < 360.0
    assert 0.0 <= relocated["M"] < 360.0


def test_relocated_angles_requires_a_known_birth_time():
    with pytest.raises(ValueError):
        relocated_angles(BIRTH_WITHOUT_TIME, 13.7563, 100.5018)
