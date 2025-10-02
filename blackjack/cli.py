from __future__ import annotations

from typing import Callable, Iterable, List

from .cards import Card, Deck
from .game import BlackjackGame, Rules

CARD_WIDTH = 9
CARD_HEIGHT = 5



SUIT_RENDER = {
    "\u2660": "S",
    "\u2665": "H",
    "\u2666": "D",
    "\u2663": "C",
}

def prompt(prompt_text: str, input_fn: Callable[[str], str] = input) -> str:
    return input_fn(prompt_text)


def _format_rank_left(rank: str) -> str:
    return "10" if rank == "10" else f"{rank} "


def _format_rank_right(rank: str) -> str:
    return "10" if rank == "10" else f" {rank}"


def render_card(card: Card) -> List[str]:
    rank = card.rank
    suit = SUIT_RENDER.get(card.suit, card.suit)
    return [
        "+-------+",
        f"|{_format_rank_left(rank)}     |",
        f"|   {suit}   |",
        f"|     {_format_rank_right(rank)}|",
        "+-------+",
    ]


HIDDEN_CARD = [
    "+-------+",
    "|#######|",
    "|#######|",
    "|#######|",
    "+-------+",
]


def _stitch(cards: Iterable[List[str]]) -> str:
    rows = [list(card) for card in cards]
    if not rows:
        return "(sin cartas)"
    assembled = ["  ".join(row[i] for row in rows) for i in range(CARD_HEIGHT)]
    return "\n".join(assembled)


def render_hand(hand_cards: List[Card], hide_hole: bool = False) -> str:
    rendered: List[List[str]] = []
    for idx, card in enumerate(hand_cards):
        if hide_hole and idx == 1:
            rendered.append(HIDDEN_CARD)
        else:
            rendered.append(render_card(card))
    return _stitch(rendered)


def show_table(game: BlackjackGame, hide_dealer_hole: bool) -> None:
    print("\nCrupier:")
    print(render_hand(game.dealer.cards, hide_hole=hide_dealer_hole))
    if not hide_dealer_hole:
        print(f"Total crupier: {game.dealer.total}")
    print("\nJugador:")
    print(render_hand(game.player.cards))
    print(f"Total jugador: {game.player.total}")


def main() -> None:
    print("Blackjack CLI - Single deck, S17, BJ 3:2")
    game = BlackjackGame(deck=Deck(), rules=Rules(dealer_hits_soft_17=False, blackjack_pays=1.5))
    bankroll = 10  # simple session bankroll for demo
    while bankroll > 0:
        print(f"\nBankroll: {bankroll} | Apuesta fija: 1")
        game.deal_initial()
        show_table(game, hide_dealer_hole=True)

        # Check naturals
        if game.player.is_blackjack() or game.dealer.is_blackjack():
            game.dealer_play()  # reveal dealer hand (no extra cards if dealer BJ)
        else:
            # Player loop: hit/stand
            while True:
                choice = prompt("¿[H]it o [S]tand? ").strip().lower()
                if choice in ("h", "hit"):
                    card = game.deck.draw()
                    game.player.add(card)
                    show_table(game, hide_dealer_hole=True)
                    if game.player.is_bust():
                        break
                elif choice in ("s", "stand"):
                    break
                else:
                    print("Opción inválida. Usa H o S.")

            # Dealer plays if player no bust
            if not game.player.is_bust():
                game.dealer_play()
        show_table(game, hide_dealer_hole=False)

        outcome, payout = game.settle()
        bankroll += payout  # bet is always 1 unit in this demo
        pretty = {
            "player_blackjack": "¡Blackjack! +1.5",
            "player_win": "¡Ganaste! +1",
            "dealer_win": "Perdiste -1",
            "push": "Empate 0",
            "player_bust": "Te pasaste -1",
            "dealer_bust": "El crupier se pasó +1",
        }[outcome]
        print("Resultado:", pretty)

        again = prompt("¿Otra mano? [S/n] ").strip().lower()
        if again == "n":
            break
    print("\nGracias por jugar.")


if __name__ == "__main__":
    main()
