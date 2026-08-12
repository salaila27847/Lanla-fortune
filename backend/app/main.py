from __future__ import annotations

import asyncio

from dotenv import load_dotenv
from fastapi import FastAPI

from app.core.schema import BirthData, SynthesisOutput
from app.modules.oracle.engine import draw as oracle_draw
from app.modules.tarot.engine import draw as tarot_draw
from app.modules.uranian.engine import calculate as uranian_calculate
from app.synthesis.master_interpreter import synthesize

load_dotenv()

app = FastAPI(title="Fortune App API")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/reading", response_model=SynthesisOutput)
async def get_reading(birth_data: BirthData) -> SynthesisOutput:
    # Run all 3 engines concurrently — see CLAUDE.md performance requirement.
    uranian_result, tarot_result, oracle_result = await asyncio.gather(
        uranian_calculate(birth_data),
        tarot_draw(),
        oracle_draw(),
    )
    return await synthesize(uranian_result, tarot_result, oracle_result)
