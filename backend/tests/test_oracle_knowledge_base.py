"""Tests for the real "lanla_original" oracle deck (Phase 3 — replaces the
Phase 1 mock). Keep test_engine_contracts.py's schema check separate;
this file checks the actual knowledge-base content and draw behavior.
"""

from __future__ import annotations

import pytest

from app.modules.oracle.engine import DEFAULT_DECK, _load_deck_cards, draw


def test_deck_has_sixty_unique_cards():
    cards = _load_deck_cards(DEFAULT_DECK)
    assert len(cards) == 60

    ids = [card["id"] for card in cards]
    assert len(ids) == len(set(ids))


def test_deck_covers_all_three_categories():
    cards = _load_deck_cards(DEFAULT_DECK)
    categories = {card["category"] for card in cards}
    assert categories == {"guardian", "animal", "flower"}


@pytest.mark.asyncio
async def test_draw_returns_real_card_content():
    result = await draw()
    assert result.engine == "oracle"
    assert "mock" not in result.summary.lower()
    assert len(result.raw_findings) == 1


@pytest.mark.asyncio
async def test_draw_multiple_cards_are_distinct():
    result = await draw(count=3)
    labels = [finding.label for finding in result.raw_findings]
    assert len(labels) == 3
    assert len(set(labels)) == 3
