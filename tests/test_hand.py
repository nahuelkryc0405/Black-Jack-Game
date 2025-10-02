import pytest

from blackjack.hand import Hand
from blackjack.cards import Card


def test_totals_with_aces() -> None:
    hand = Hand([Card("A", "\u2660"), Card("9", "\u2666")])
    assert hand.total == 20
    hand.add(Card("A", "\u2665"))
    assert hand.total == 21
    hand.add(Card("9", "\u2663"))
    assert hand.total == 20


def test_blackjack_detection() -> None:
    assert Hand([Card("A", "\u2660"), Card("K", "\u2666")]).is_blackjack() is True
    assert Hand([Card("A", "\u2660"), Card("9", "\u2666"), Card("A", "\u2665")]).is_blackjack() is False


def test_bust_detection() -> None:
    hand = Hand([Card("K", "\u2660"), Card("Q", "\u2666"), Card("2", "\u2665")])
    assert hand.is_bust() is True
