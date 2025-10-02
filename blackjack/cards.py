from __future__ import annotations

from dataclasses import dataclass
import random
from typing import List

SUITS = ("\u2660", "\u2665", "\u2666", "\u2663")
RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
VALUES = {**{str(i): i for i in range(2, 11)}, "J": 10, "Q": 10, "K": 10, "A": 11}


@dataclass(frozen=True)
class Card:
    rank: str
    suit: str

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"


class Deck:
    """Single 52-card deck. Shuffle on init; reshuffle automatically if low."""

    def __init__(self, n_decks: int = 1, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()
        self.n_decks = max(1, n_decks)
        self.cards: List[Card] = []
        self._build_and_shuffle()

    def _build_and_shuffle(self) -> None:
        self.cards = [Card(r, s) for _ in range(self.n_decks) for s in SUITS for r in RANKS]
        self._rng.shuffle(self.cards)

    def draw(self) -> Card:
        if len(self.cards) == 0:
            self._build_and_shuffle()
        # auto-reshuffle if penetration > 75%
        if len(self.cards) < self.n_decks * 52 * 0.25:
            self._build_and_shuffle()
        return self.cards.pop()
