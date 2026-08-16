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


def shuffle() -> list[dict[str, Any]]:
    """Full 78-card deck shuffle for the pick-your-own-card flow, with
    orientation pre-decided per card — the client fetches this (via POST
    /api/tarot/draw) before showing the card grid, so tapping a position
    reveals a specific, already-decided card+orientation rather than one
    picked at random after the fact. Independent of spread choice: the
    spread only determines how many of these get used, not which cards
    exist to shuffle."""
    deck = list(_load_deck())
    random.shuffle(deck)
    return [{**card, "reversed": random.choice([True, False])} for card in deck]


def build_result(spread_type: str, drawn: list[tuple[dict[str, Any], bool]]) -> EngineResult:
    """Aggregates an already-chosen, ordered list of (card, is_reversed)
    pairs into an EngineResult — shared by the random draw() convenience
    wrapper below and the real pick-your-own-card flow
    (build_result_from_picks)."""
    positions = _load_spread(spread_type)["positions"]
    findings: list[Finding] = []
    themes: list[str] = []
    first_meaning = ""
    present_meaning = ""

    for position, (card, is_reversed) in zip(positions, drawn, strict=True):
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


def build_result_from_picks(spread_type: str, picks: list[tuple[str, bool]]) -> EngineResult:
    """Real pick-your-own-card flow: `picks` are (card_id, reversed) pairs
    the client revealed (in tap order) from a deck it already fetched via
    shuffle(). Trusted as-is — no server-side session/token guarding
    which cards were "really" dealt — but every id is re-looked-up
    against our own knowledge base here, so the meaning text in the
    result is always authoritative, never client-submitted."""
    positions = _load_spread(spread_type)["positions"]
    if len(picks) != len(positions):
        raise ValueError(f"ต้องเลือกไพ่ {len(positions)} ใบสำหรับเลย์เอาท์นี้")
    card_ids = [card_id for card_id, _ in picks]
    if len(set(card_ids)) != len(card_ids):
        raise ValueError("เลือกไพ่ใบซ้ำกัน")
    by_id = {card["id"]: card for card in _load_deck()}
    try:
        drawn = [(by_id[card_id], is_reversed) for card_id, is_reversed in picks]
    except KeyError as exc:
        raise ValueError(f"ไม่พบไพ่ id นี้ในสำรับ: {exc}") from exc
    return build_result(spread_type, drawn)


async def draw(spread_type: str = DEFAULT_SPREAD) -> EngineResult:
    """Convenience wrapper for a random (non-interactive) draw — used by
    tests and scripts. The real reading flow no longer calls this; it
    uses shuffle() + build_result_from_picks() instead, so the cards
    shown to the user really are the ones used in the reading."""
    deck = _load_deck()
    positions = _load_spread(spread_type)["positions"]
    drawn_cards = random.sample(deck, k=len(positions))
    drawn = [(card, random.choice([True, False])) for card in drawn_cards]
    return build_result(spread_type, drawn)
