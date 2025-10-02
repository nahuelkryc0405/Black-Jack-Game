from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Tuple

from .cards import Deck
from .hand import Hand

Outcome = Literal[
    "player_blackjack",
    "player_win",
    "dealer_win",
    "push",
    "player_bust",
    "dealer_bust",
]


@dataclass
class Rules:
    dealer_hits_soft_17: bool = False  # H17=False -> dealer stands on soft 17 (S17)
    blackjack_pays: float = 1.5        # 3:2 payout


class BlackjackGame:
    def __init__(self, deck: Deck | None = None, rules: Rules | None = None) -> None:
        self.deck = deck or Deck()
        self.rules = rules or Rules()
        self.player = Hand()
        self.dealer = Hand()

    def deal_initial(self) -> None:
        self.player = Hand()
        self.dealer = Hand()
        for _ in range(2):
            self.player.add(self.deck.draw())
            self.dealer.add(self.deck.draw())

    def dealer_play(self) -> None:
        # Dealer must hit until 17 or more. If H17, hits soft 17 as well.
        while True:
            total = self.dealer.total
            soft17 = total == 17 and self.dealer.is_soft()
            if total < 17 or (soft17 and self.rules.dealer_hits_soft_17):
                self.dealer.add(self.deck.draw())
            else:
                break

    def settle(self) -> Tuple[Outcome, float]:
        """Return outcome and player payout (bet=1 as baseline)."""
        # Natural blackjacks
        if self.player.is_blackjack() and self.dealer.is_blackjack():
            return "push", 0.0
        if self.player.is_blackjack():
            return "player_blackjack", self.rules.blackjack_pays
        if self.dealer.is_blackjack():
            return "dealer_win", -1.0

        # Busts
        if self.player.is_bust():
            return "player_bust", -1.0
        if self.dealer.is_bust():
            return "dealer_bust", 1.0

        # Compare totals
        if self.player.total > self.dealer.total:
            return "player_win", 1.0
        if self.player.total < self.dealer.total:
            return "dealer_win", -1.0
        return "push", 0.0
