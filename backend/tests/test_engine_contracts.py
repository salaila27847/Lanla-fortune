"""Every engine must return a valid EngineResult — this is the contract
the synthesis layer relies on. Keep this test passing as engines move
from mock to real implementations in Phase 5.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.core.schema import BirthData, EngineResult
from app.modules.oracle.engine import draw as oracle_draw
from app.modules.tarot.engine import draw as tarot_draw
from app.modules.uranian.engine import calculate as uranian_calculate


@pytest.mark.asyncio
async def test_uranian_engine_contract():
    birth_data = BirthData(
        date=date(1990, 1, 1),
        place="Bangkok",
        latitude=13.75,
        longitude=100.5,
        timezone="Asia/Bangkok",
    )
    result = await uranian_calculate(birth_data)
    assert isinstance(result, EngineResult)
    assert result.engine == "uranian"


@pytest.mark.asyncio
async def test_tarot_engine_contract():
    result = await tarot_draw()
    assert isinstance(result, EngineResult)
    assert result.engine == "tarot"


@pytest.mark.asyncio
async def test_oracle_engine_contract():
    result = await oracle_draw()
    assert isinstance(result, EngineResult)
    assert result.engine == "oracle"
