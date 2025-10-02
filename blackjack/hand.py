from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .cards import Card, VALUES


@dataclass
class Hand:
    cards: List[Card] = field(default_factory=list)

    def add(self, card: Card) -> None:
        self.cards.append(card)

    @property
    def total(self) -> int:
        """Return best total where Aces can be 11 or 1."""
        total = sum(VALUES[c.rank] for c in self.cards)
        aces = sum(1 for c in self.cards if c.rank == "A")
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    def is_blackjack(self) -> bool:
        return len(self.cards) == 2 and self.total == 21

    def is_bust(self) -> bool:
        return self.total > 21

    def is_soft(self) -> bool:
        """Soft if there is an Ace counted as 11."""
        raw = sum(VALUES[c.rank] for c in self.cards)
        return any(c.rank == "A" for c in self.cards) and raw <= 21

    def __str__(self) -> str:
        return " ".join(str(c) for c in self.cards) + f"  ({self.total})"
