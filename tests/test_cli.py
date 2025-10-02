from collections.abc import Iterable

import pytest

from blackjack import cli
from blackjack.cards import Card


class StubDeck:
    def __init__(self, cards: Iterable[Card]):
        self.cards = list(cards)

    def draw(self) -> Card:
        return self.cards.pop()


def test_cli_runs_one_round(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    inputs = iter(["s", "n"])  # stand immediately, then salir
    monkeypatch.setattr(cli, "prompt", lambda text, input_fn=None: next(inputs))

    sequence = [
        Card("5", "\u2660"),   # dealer draw if needed
        Card("6", "\u2666"),   # dealer hole
        Card("7", "\u2665"),   # player second
        Card("9", "\u2663"),   # dealer up
        Card("10", "\u2660"),  # player up
    ]
    monkeypatch.setattr(cli, "Deck", lambda: StubDeck(sequence))

    cli.main()
    stdout = capsys.readouterr().out
    assert "+-------+" in stdout  # cartas ASCII (algo gráfico)
    assert "Gracias por jugar" in stdout
