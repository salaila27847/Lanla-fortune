"""Oracle card engine.

Draws from the YAML-configured decks in
backend/app/knowledge_base/oracle/decks/<deck_id>/. The default deck,
"lanla_original", is the app's own custom deck merging 3 themes: guardian
spirits, Thai spirit animals, and sacred flowers. Additional decks can be
added later as sibling folders and selected via the `deck` argument.

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

DECKS_DIR = Path(__file__).resolve().parents[2] / "knowledge_base" / "oracle" / "decks"
DEFAULT_DECK = "lanla_original"


@lru_cache
def _load_deck_cards(deck: str) -> tuple[dict[str, Any], ...]:
    deck_dir = DECKS_DIR / deck
    meta = yaml.safe_load((deck_dir / "deck.yaml").read_text(encoding="utf-8"))

    cards: list[dict[str, Any]] = []
    for category in meta["categories"]:
        data = yaml.safe_load((deck_dir / category["file"]).read_text(encoding="utf-8"))
        for card in data["cards"]:
            cards.append({**card, "category": data["category"], "category_th": data["category_th"]})
    return tuple(cards)


async def draw(deck: str = DEFAULT_DECK, count: int = 1) -> EngineResult:
    cards = _load_deck_cards(deck)
    drawn = random.sample(cards, k=min(count, len(cards)))

    findings = [
        Finding(
            label=f"{card['name_th']} ({card['category_th']})",
            meaning=card["meaning"],
            weight=0.6,
        )
        for card in drawn
    ]
    themes = list(dict.fromkeys(kw for card in drawn for kw in card["keywords"]))[:5]

    return EngineResult(
        engine="oracle",
        summary=drawn[0]["meaning"],
        themes=themes,
        raw_findings=findings,
        confidence=0.65,
    )
