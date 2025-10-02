from blackjack.game import BlackjackGame, Rules
from blackjack.cards import Deck, Card


class RiggedDeck(Deck):
    def __init__(self, sequence):
        self.cards = list(sequence)
        self.n_decks = 1

    def draw(self) -> Card:
        return self.cards.pop()


def test_player_blackjack_beats_dealer_20() -> None:
    sequence = [
        Card("10", "\u2660"),  # dealer 2nd
        Card("K", "\u2666"),   # player 2nd -> BJ
        Card("10", "\u2665"),  # dealer up
        Card("A", "\u2663"),   # player up
    ]
    game = BlackjackGame(deck=RiggedDeck(sequence), rules=Rules())
    game.deal_initial()
    outcome, payout = game.settle()
    assert outcome == "player_blackjack"
    assert payout == 1.5


def test_dealer_plays_to_17_or_more() -> None:
    sequence = [
        Card("9", "\u2666"),   # dealer draw -> last
        Card("2", "\u2663"),   # dealer draw
        Card("10", "\u2660"),  # dealer hole
        Card("6", "\u2666"),   # player 2nd
        Card("6", "\u2665"),   # dealer up
        Card("10", "\u2663"),  # player up
    ]
    game = BlackjackGame(deck=RiggedDeck(sequence), rules=Rules(dealer_hits_soft_17=False))
    game.deal_initial()
    game.dealer_play()
    assert game.dealer.total >= 17
