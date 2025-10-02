# Blackjack (Python)

Pequeno juego de Blackjack pensado para portfolio y practicar Python:
- Programacion orientada a objetos (cartas, manos, reglas, flujo del juego)
- Logica del negocio (manejo de As, crupier S17/H17, payouts)
- CLI con cartas renderizadas en texto
- Interfaz grafica simple con PySimpleGUI
- Tests automatizados con `pytest`

## Requisitos
```
python >= 3.10
pip install -r requirements.txt
```

## Como jugar
- CLI interactiva:
  ```
  py play_blackjack.py
  ```
  (alternativa: `python -m blackjack.cli`)
- GUI (ventana tradicional):
  ```
  py play_blackjack_gui.py
  ```

Ambas variantes usan un bankroll de prueba de 10 unidades, apuesta fija de 1 y reglas S17 con pago 3:2 para Blackjack.

## Tests
```
pytest -q
```

## Estructura
```
blackjack/
  __init__.py
  cards.py
  hand.py
  game.py
  cli.py
  gui.py
play_blackjack.py
play_blackjack_gui.py
README.md
requirements.txt
tests/
  test_hand.py
  test_game.py
  test_cli.py
```
