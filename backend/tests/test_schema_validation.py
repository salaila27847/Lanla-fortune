"""BirthData validates at the API boundary so bad client input fails fast
with a clear 422-style error instead of crashing an engine deep inside
/api/reading (e.g. zoneinfo.ZoneInfoNotFoundError from an unknown
timezone string, which a free-text frontend field can easily produce).
"""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from app.core.schema import BirthData


def _valid_kwargs(**overrides):
    kwargs = {
        "date": date(1990, 1, 1),
        "time": None,
        "place": "Bangkok",
        "latitude": 13.7563,
        "longitude": 100.5018,
        "timezone": "Asia/Bangkok",
    }
    kwargs.update(overrides)
    return kwargs


def test_valid_birth_data_is_accepted():
    BirthData(**_valid_kwargs())


def test_unknown_timezone_is_rejected():
    with pytest.raises(ValidationError):
        BirthData(**_valid_kwargs(timezone="Not/A_Real_Zone"))


@pytest.mark.parametrize("latitude", [-91, 91])
def test_out_of_range_latitude_is_rejected(latitude):
    with pytest.raises(ValidationError):
        BirthData(**_valid_kwargs(latitude=latitude))


@pytest.mark.parametrize("longitude", [-181, 181])
def test_out_of_range_longitude_is_rejected(longitude):
    with pytest.raises(ValidationError):
        BirthData(**_valid_kwargs(longitude=longitude))
