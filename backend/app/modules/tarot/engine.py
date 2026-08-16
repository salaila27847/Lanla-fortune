"""Tarot engine.

Draws from the YAML-configured deck and spreads in
backend/app/knowledge_base/tarot/ (major_arcana.yaml, minor_arcana.yaml,
spreads.yaml) — a 78-card deck with standard Rider-Waite-Smith-tradition
meanings written in Thai, since no reusable "Destiny Matrix" reference
file could be found (see knowledge_base/tarot/README.md).

The function signature and return type (EngineResult) must not change —
the synthesis layer depends on this contract.
"""

from __future__ import annotations

import random
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.core.schema import EngineResult, Finding

KB_DIR = Path(__file__).resolve().parents[2] / "knowledge_base" / "tarot"
DEFAULT_SPREAD = "three_card"


@lru_cache
def _load_deck() -> tuple[dict[str, Any], ...]:
    cards: list[dict[str, Any]] = []

    major = yaml.safe_load((KB_DIR / "major_arcana.yaml").read_text(encoding="utf-8"))
    cards.extend(major["cards"])

    minor = yaml.safe_load((KB_DIR / "minor_arcana.yaml").read_text(encoding="utf-8"))
    cards.extend(minor["cards"])

    return tuple(cards)


@lru_cache
def _load_spread(spread_type: str) -> dict[str, Any]:
    data = yaml.safe_load((KB_DIR / "spreads.yaml").read_text(encoding="utf-8"))
    for spread in data["spreads"]:
        if spread["id"] == spread_type:
            return spread
    raise ValueError(f"Unknown tarot spread: {spread_type}")


async def draw(spread_type: str = DEFAULT_SPREAD) -> EngineResult:
    deck = _load_deck()
    positions = _load_spread(spread_type)["positions"]
    drawn_cards = random.sample(deck, k=len(positions))

    findings: list[Finding] = []
    themes: list[str] = []
    first_meaning = ""
    present_meaning = ""

    for position, card in zip(positions, drawn_cards):
        is_reversed = random.choice([True, False])
        meaning = card["meaning_reversed"] if is_reversed else card["meaning_upright"]
        keywords = card["keywords_reversed"] if is_reversed else card["keywords_upright"]
        orientation = "กลับหัว" if is_reversed else "ตั้งตรง"

        findings.append(
            Finding(
                label=f"{card['name_th']} ({orientation}) — {position['label_th']}",
                meaning=meaning,
                weight=0.6,
            )
        )
        themes.extend(keywords)
        first_meaning = first_meaning or meaning
        if position["id"] == "present":
            present_meaning = meaning

    return EngineResult(
        engine="tarot",
        summary=present_meaning or first_meaning,
        themes=list(dict.fromkeys(themes)),
        raw_findings=findings,
        confidence=0.65,
    )
