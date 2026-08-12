"""Tests for the real 78-card tarot deck (Phase 3 — replaces the Phase 1
mock). Keep test_engine_contracts.py's schema check separate; this file
checks the actual knowledge-base content and draw behavior.
"""

from __future__ import annotations

import pytest

from app.modules.tarot.engine import _load_deck, _load_spread, draw


def test_deck_has_seventy_eight_unique_cards():
    cards = _load_deck()
    assert len(cards) == 78

    ids = [card["id"] for card in cards]
    assert len(ids) == len(set(ids))


def test_deck_has_every_card_orientation():
    cards = _load_deck()
    for card in cards:
        assert card["meaning_upright"]
        assert card["meaning_reversed"]
        assert card["keywords_upright"]
        assert card["keywords_reversed"]


def test_both_spreads_are_defined():
    single = _load_spread("single_card")
    assert len(single["positions"]) == 1

    three = _load_spread("three_card")
    assert [p["id"] for p in three["positions"]] == ["past", "present", "future"]


@pytest.mark.asyncio
async def test_default_draw_uses_three_card_spread():
    result = await draw()
    assert result.engine == "tarot"
    assert len(result.raw_findings) == 3
    assert "mock" not in result.summary.lower()


@pytest.mark.asyncio
async def test_single_card_draw():
    result = await draw(spread_type="single_card")
    assert len(result.raw_findings) == 1


@pytest.mark.asyncio
async def test_drawn_cards_within_a_spread_are_distinct():
    result = await draw()
    card_names = [finding.label.split(" (")[0] for finding in result.raw_findings]
    assert len(card_names) == len(set(card_names))


@pytest.mark.asyncio
async def test_finding_labels_show_orientation_and_position():
    result = await draw()
    for finding in result.raw_findings:
        assert "ตั้งตรง" in finding.label or "กลับหัว" in finding.label
        assert "—" in finding.label
