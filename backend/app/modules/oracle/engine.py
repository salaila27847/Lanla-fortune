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


def shuffle(deck: str = DEFAULT_DECK) -> list[dict[str, Any]]:
    """Full-deck shuffle for the pick-your-own-card flow — the client
    fetches this (via POST /api/oracle/draw) before showing the card
    grid, so tapping a position reveals a specific, already-decided card
    rather than one picked at random after the fact."""
    cards = list(_load_deck_cards(deck))
    random.shuffle(cards)
    return cards


def build_result(drawn: list[dict[str, Any]]) -> EngineResult:
    """Aggregates an already-chosen, ordered list of card dicts (as
    returned by _load_deck_cards/shuffle) into an EngineResult — shared
    by the random draw() convenience wrapper below and the real
    pick-your-own-card flow (build_result_from_picks)."""
    findings = [
        Finding(
            label=f"{card['name_th']} ({card['category_th']})",
            meaning=card["meaning"],
            weight=0.6,
            voice=card.get("voice_th"),
        )
        for card in drawn
    ]
    themes = list(dict.fromkeys(kw for card in drawn for kw in card["keywords"]))

    return EngineResult(
        engine="oracle",
        summary=drawn[0]["meaning"],
        themes=themes,
        raw_findings=findings,
        confidence=0.65,
    )


def build_result_from_picks(picks: list[str], deck: str = DEFAULT_DECK) -> EngineResult:
    """Real pick-your-own-card flow: `picks` are the card ids the client
    revealed (in tap order) from a deck it already fetched via shuffle().
    Trusted as-is — no server-side session/token guarding which ids were
    "really" dealt — but every id is re-looked-up against our own
    knowledge base here, so the meaning text in the result is always
    authoritative, never client-submitted."""
    by_id = {card["id"]: card for card in _load_deck_cards(deck)}
    if len(set(picks)) != len(picks):
        raise ValueError("เลือกไพ่ใบซ้ำกัน")
    try:
        drawn = [by_id[card_id] for card_id in picks]
    except KeyError as exc:
        raise ValueError(f"ไม่พบไพ่ id นี้ในสำรับ: {exc}") from exc
    return build_result(drawn)


async def draw(deck: str = DEFAULT_DECK, count: int = 1) -> EngineResult:
    """Convenience wrapper for a random (non-interactive) draw — used by
    tests and scripts. The real reading flow no longer calls this; it
    uses shuffle() + build_result_from_picks() instead, so the cards
    shown to the user really are the ones used in the reading."""
    cards = _load_deck_cards(deck)
    drawn = list(random.sample(cards, k=min(count, len(cards))))
    return build_result(drawn)
