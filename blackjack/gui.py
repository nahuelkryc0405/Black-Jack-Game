
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import pygame

from .cards import Card
from .game import BlackjackGame, Rules

START_BANKROLL = 50.0
DEFAULT_BET = 5
MIN_BET = 1
BET_STEP = 1
BET_CHIPS = (1, 5, 10, 25)

OUTCOME_TEXT = {
    "player_blackjack": "Blackjack! +1.5",
    "player_win": "Ganaste +1",
    "dealer_win": "Perdiste -1",
    "push": "Empate 0",
    "player_bust": "Te pasaste -1",
    "dealer_bust": "Crupier se paso +1",
}

WINDOW_WIDTH = 1080
WINDOW_HEIGHT = 860
MIN_WINDOW_WIDTH = 960
MIN_WINDOW_HEIGHT = 780
CARD_WIDTH = 110
CARD_HEIGHT = 160
CARD_SPACING = 32

TABLE_TOP_COLOR = (22, 110, 80)
TABLE_BOTTOM_COLOR = (8, 60, 44)
HIGHLIGHT_COLOR = (120, 200, 160, 70)
TEXT_PRIMARY = (240, 240, 240)
TEXT_SECONDARY = (205, 205, 205)
CARD_BORDER = (16, 51, 34)
CARD_FACE = (250, 250, 250)
CARD_BACK = (72, 96, 138)
CARD_BACK_ACCENT = (126, 148, 198)
CARD_TEXT = (20, 20, 20)
CARD_RED = (195, 40, 40)
BUTTON_BG = (48, 128, 195)
BUTTON_HOVER = (72, 160, 228)
BUTTON_DISABLED = (85, 85, 85)
BUTTON_TEXT = (250, 250, 250)
BET_BUTTON_BG = (50, 70, 100)
BET_BUTTON_HOVER = (70, 100, 140)
BET_BUTTON_DISABLED = (65, 65, 65)
MESSAGE_TEXT = (245, 245, 245)
CHIP_LABEL_COLOR = (245, 245, 245)

CHIP_COLORS = {
    1: (60, 120, 210),
    5: (210, 85, 80),
    10: (70, 180, 110),
    25: (235, 195, 70),
}

RED_SUITS = {"\u2665", "\u2666"}

ANIMATION_DURATION = 0.35
CHIP_FLASH_DURATION = 0.4
SHADOW_ALPHA = 110


@dataclass
class Button:
    label: str
    action: str
    rect: pygame.Rect
    enabled: bool = True
    category: str = "action"


@dataclass
class Chip:
    value: int
    center: Tuple[int, int]
    radius: int

    def contains(self, pos: Tuple[int, int]) -> bool:
        dx = pos[0] - self.center[0]
        dy = pos[1] - self.center[1]
        return dx * dx + dy * dy <= self.radius * self.radius


def _format_value(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.1f}"


def _format_delta(value: float) -> str:
    sign = "+" if value > 0 else ""
    if float(value).is_integer():
        return f"{sign}{int(value)}"
    return f"{sign}{value:.1f}"


def compute_layout(width: int, height: int, show_controls: bool) -> Dict[str, float]:
    width = max(width, MIN_WINDOW_WIDTH)
    height = max(height, MIN_WINDOW_HEIGHT)

    margin = max(36, width // 32)
    title_y = margin
    scoreboard_top = title_y + 72
    bankroll_pos = (margin, scoreboard_top)
    bet_info_pos = (margin, scoreboard_top + 36)
    bet_hint_pos = (margin, bet_info_pos[1] + 28)
    status_offset = 30 if show_controls else 6
    status_pos = (margin, bet_hint_pos[1] + status_offset)

    chip_row_y = status_pos[1] + 70 if show_controls else status_pos[1]
    chip_radius = max(22, min(34, width // 32)) if show_controls else 0
    chip_spacing = max(chip_radius * 2 + 36, min(170, width // 8)) if show_controls else 0
    total_chip_width = chip_spacing * (len(BET_CHIPS) - 1) if show_controls else 0
    chip_start_x = width // 2 - total_chip_width // 2 if show_controls else 0
    chip_centers = [
        (chip_start_x + idx * chip_spacing, chip_row_y)
        for idx in range(len(BET_CHIPS))
    ] if show_controls else []

    bet_button_specs = [
        ("-", "bet_minus", 60),
        ("+", "bet_plus", 60),
        ("Reset", "bet_clear", 110),
        ("Max", "bet_max", 90),
    ]
    bet_buttons_y = chip_row_y + chip_radius + 48 if show_controls else chip_row_y
    bet_button_spacing = 18
    total_bet_width = sum(spec[2] for spec in bet_button_specs) + bet_button_spacing * (len(bet_button_specs) - 1)
    bet_button_start_x = width // 2 - total_bet_width // 2

    dealer_y = (bet_buttons_y + 120) if show_controls else status_pos[1] + 90
    player_y = dealer_y + CARD_HEIGHT + 140
    button_row_y = min(height - 90, player_y + CARD_HEIGHT + 110)

    if show_controls:
        ellipse_width = int(width * 0.56)
        ellipse_height = max(220, dealer_y - chip_row_y + 160)
        ellipse_center_y = (chip_row_y + dealer_y) // 2
    else:
        ellipse_width = int(width * 0.4)
        ellipse_height = 160
        ellipse_center_y = status_pos[1] + 60

    return {
        "width": width,
        "height": height,
        "margin": margin,
        "show_controls": show_controls,
        "title_y": title_y,
        "bankroll_pos": bankroll_pos,
        "bet_info_pos": bet_info_pos,
        "bet_hint_pos": bet_hint_pos,
        "status_pos": status_pos,
        "chip_radius": chip_radius,
        "chip_centers": chip_centers,
        "bet_button_specs": bet_button_specs,
        "bet_button_start_x": bet_button_start_x,
        "bet_button_spacing": bet_button_spacing,
        "bet_buttons_y": bet_buttons_y,
        "dealer_y": dealer_y,
        "player_y": player_y,
        "button_row_y": button_row_y,
        "ellipse_size": (ellipse_width, ellipse_height),
        "ellipse_center_y": ellipse_center_y,
    }


def create_action_buttons(layout: Dict[str, float]) -> list[Button]:
    specs = [
        ("Hit", "hit", 130),
        ("Stand", "stand", 130),
        ("Repartir", "next", 170),
        ("Reiniciar", "reset", 150),
        ("Salir", "exit", 130),
    ]
    spacing = 22
    total_width = sum(width for _, _, width in specs) + spacing * (len(specs) - 1)
    start_x = layout["width"] // 2 - total_width // 2
    buttons: list[Button] = []
    offset = 0
    for label, action, width in specs:
        rect = pygame.Rect(int(start_x + offset), int(layout["button_row_y"]), width, 58)
        buttons.append(Button(label, action, rect))
        offset += width + spacing
    return buttons


def create_bet_buttons(layout: Dict[str, float]) -> list[Button]:
    buttons: list[Button] = []
    x = layout["bet_button_start_x"]
    y = layout["bet_buttons_y"]
    for label, action, width in layout["bet_button_specs"]:
        rect = pygame.Rect(int(x), int(y), width, 48)
        buttons.append(Button(label, action, rect, category="bet"))
        x += width + layout["bet_button_spacing"]
    return buttons


def create_chips(layout: Dict[str, float]) -> list[Chip]:
    radius = int(layout["chip_radius"])
    return [
        Chip(value, (int(cx), int(cy)), radius)
        for value, (cx, cy) in zip(BET_CHIPS, layout["chip_centers"])
    ]

def build_background(size: Tuple[int, int], layout: Dict[str, float]) -> pygame.Surface:
    width, height = size
    surface = pygame.Surface(size)
    for y in range(height):
        blend = y / height
        color = (
            int(TABLE_TOP_COLOR[0] * (1 - blend) + TABLE_BOTTOM_COLOR[0] * blend),
            int(TABLE_TOP_COLOR[1] * (1 - blend) + TABLE_BOTTOM_COLOR[1] * blend),
            int(TABLE_TOP_COLOR[2] * (1 - blend) + TABLE_BOTTOM_COLOR[2] * blend),
        )
        pygame.draw.line(surface, color, (0, y), (width, y))
    if layout["ellipse_size"][0] > 0 and layout["ellipse_size"][1] > 0:
        highlight = pygame.Surface(size, pygame.SRCALPHA)
        ellipse_width, ellipse_height = layout["ellipse_size"]
        ellipse_rect = pygame.Rect(0, 0, ellipse_width, ellipse_height)
        ellipse_rect.center = (width // 2, int(layout["ellipse_center_y"]))
        pygame.draw.ellipse(highlight, HIGHLIGHT_COLOR, ellipse_rect)
        surface.blit(highlight, (0, 0))
    return surface


def adjust_color(color: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
    return tuple(max(0, min(255, int(c * factor))) for c in color)


def run_gui() -> None:
    pygame.init()
    try:
        status_text = ""
        show_bet_panel = False

        title_font = pygame.font.SysFont("arial", 46, bold=True)
        label_font = pygame.font.SysFont("arial", 32, bold=True)
        text_font = pygame.font.SysFont("arial", 26)
        bankroll_font = pygame.font.SysFont("arial", 28)
        hint_font = pygame.font.SysFont("arial", 20)
        card_rank_font = pygame.font.SysFont("arial", 30, bold=True)
        card_suit_font = pygame.font.SysFont("arial", 44)
        button_font = pygame.font.SysFont("arial", 26, bold=True)
        chip_font = pygame.font.SysFont("arial", 20, bold=True)

        layout = compute_layout(WINDOW_WIDTH, WINDOW_HEIGHT, show_bet_panel)
        screen = pygame.display.set_mode((layout["width"], layout["height"]), pygame.RESIZABLE)
        pygame.display.set_caption("Blackjack")
        clock = pygame.time.Clock()

        background = build_background((layout["width"], layout["height"]), layout)
        action_buttons: list[Button] = []
        bet_buttons: list[Button] = []
        chips: list[Chip] = []
        toggle_button = Button("Mostrar apuesta", "toggle_panel", pygame.Rect(0, 0, 0, 0), category="misc")
        button_map: Dict[str, Button] = {}

        def rebuild_ui(new_width: int | None = None, new_height: int | None = None) -> None:
            nonlocal layout, screen, background, action_buttons, bet_buttons, chips, toggle_button
            width = new_width or screen.get_width()
            height = new_height or screen.get_height()
            layout = compute_layout(width, height, show_bet_panel)
            screen = pygame.display.set_mode((layout["width"], layout["height"]), pygame.RESIZABLE)
            background = build_background((layout["width"], layout["height"]), layout)
            action_buttons = create_action_buttons(layout)
            bet_buttons = create_bet_buttons(layout) if show_bet_panel else []
            chips = create_chips(layout) if show_bet_panel else []
            toggle_label = "Ocultar apuesta" if show_bet_panel else "Mostrar apuesta"
            toggle_rect = pygame.Rect(
                layout["width"] - layout["margin"] - 180,
                int(layout["bankroll_pos"][1]),
                170,
                46,
            )
            toggle_button = Button(toggle_label, "toggle_panel", toggle_rect, category="misc")
            button_map.clear()
            for btn in action_buttons:
                button_map[btn.action] = btn
            for btn in bet_buttons:
                button_map[btn.action] = btn

        rebuild_ui(layout["width"], layout["height"])

        card_surface_cache: Dict[Tuple[str, str], pygame.Surface] = {}
        hidden_card_surface: pygame.Surface | None = None
        card_animations: Dict[Tuple[str, int], float] = {}
        chip_highlights: Dict[int, float] = {}

        rules = Rules(dealer_hits_soft_17=False, blackjack_pays=1.5)
        game = BlackjackGame(rules=rules)
        bankroll = START_BANKROLL
        current_bet = min(max(DEFAULT_BET, MIN_BET), int(bankroll))
        round_active = False
        hide_dealer = True

        def get_card_surface(card: Card, hidden: bool) -> pygame.Surface:
            nonlocal hidden_card_surface
            if hidden:
                if hidden_card_surface is None:
                    hidden_card_surface = pygame.Surface((CARD_WIDTH, CARD_HEIGHT), pygame.SRCALPHA)
                    pygame.draw.rect(hidden_card_surface, CARD_BORDER, hidden_card_surface.get_rect(), border_radius=14)
                    inner = hidden_card_surface.get_rect().inflate(-10, -10)
                    pygame.draw.rect(hidden_card_surface, CARD_BACK, inner, border_radius=12)
                    stripe = pygame.Rect(inner.left + 16, inner.centery - 6, inner.width - 32, 12)
                    pygame.draw.rect(hidden_card_surface, CARD_BACK_ACCENT, stripe, border_radius=6)
                    question = card_rank_font.render("??", True, MESSAGE_TEXT)
                    hidden_card_surface.blit(question, question.get_rect(center=inner.center))
                return hidden_card_surface
            key = (card.rank, card.suit)
            if key not in card_surface_cache:
                surface = pygame.Surface((CARD_WIDTH, CARD_HEIGHT), pygame.SRCALPHA)
                pygame.draw.rect(surface, CARD_BORDER, surface.get_rect(), border_radius=14)
                inner = surface.get_rect().inflate(-10, -10)
                pygame.draw.rect(surface, CARD_FACE, inner, border_radius=12)
                suit_color = CARD_RED if card.suit in RED_SUITS else CARD_TEXT
                rank_surface = card_rank_font.render(card.rank, True, suit_color)
                surface.blit(rank_surface, (inner.left + 12, inner.top + 12))
                surface.blit(
                    rank_surface,
                    (inner.right - rank_surface.get_width() - 12, inner.bottom - rank_surface.get_height() - 12),
                )
                suit_surface = card_suit_font.render(card.suit, True, suit_color)
                surface.blit(suit_surface, suit_surface.get_rect(center=inner.center))
                card_surface_cache[key] = surface
            return card_surface_cache[key]

        def draw_card(surface: pygame.Surface, rect: pygame.Rect, card: Card, hidden: bool, hand_key: str, idx: int) -> None:
            elapsed = card_animations.get((hand_key, idx), ANIMATION_DURATION)
            progress = min(elapsed / ANIMATION_DURATION, 1.0)
            card_surface = get_card_surface(card, hidden)
            scale = 0.85 + 0.15 * progress
            scaled_size = (int(CARD_WIDTH * scale), int(CARD_HEIGHT * scale))
            if scale != 1.0:
                card_surface_scaled = pygame.transform.smoothscale(card_surface, scaled_size)
            else:
                card_surface_scaled = card_surface
            offset_y = int((1.0 - progress) * 48)
            draw_rect = card_surface_scaled.get_rect(center=(rect.centerx, rect.centery - offset_y))
            shadow_width = int(scaled_size[0] * 0.9)
            shadow_height = max(16, int(scaled_size[1] * 0.25))
            shadow_surface = pygame.Surface((shadow_width, shadow_height), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surface, (0, 0, 0, int(SHADOW_ALPHA * progress)), shadow_surface.get_rect())
            shadow_rect = shadow_surface.get_rect(center=(rect.centerx, rect.bottom + 10))
            surface.blit(shadow_surface, shadow_rect)
            surface.blit(card_surface_scaled, draw_rect)

        def draw_hand(title: str, hand, y: int, hide_hole: bool, hand_key: str) -> None:
            width = screen.get_width()
            score_text = "??" if hide_hole and len(hand.cards) > 1 else str(hand.total)
            title_surface = label_font.render(f"{title}: {score_text}", True, TEXT_PRIMARY)
            screen.blit(title_surface, title_surface.get_rect(midtop=(width // 2, y)))

            cards = hand.cards
            card_top = y + 56
            if not cards:
                empty_surface = text_font.render("(sin cartas)", True, TEXT_SECONDARY)
                screen.blit(empty_surface, empty_surface.get_rect(midtop=(width // 2, card_top + 18)))
                return

            count = len(cards)
            total_width = count * CARD_WIDTH + (count - 1) * CARD_SPACING
            start_x = (width - total_width) // 2
            for idx, card in enumerate(cards):
                rect = pygame.Rect(
                    start_x + idx * (CARD_WIDTH + CARD_SPACING),
                    card_top,
                    CARD_WIDTH,
                    CARD_HEIGHT,
                )
                hidden = hide_hole and idx == 1
                draw_card(screen, rect, card, hidden, hand_key, idx)

        def draw_chip(chip: Chip, enabled: bool, timer: float | None, mouse_pos: Tuple[int, int]) -> None:
            base_color = CHIP_COLORS.get(chip.value, (150, 150, 150))
            if not enabled:
                fill_color = adjust_color(base_color, 0.55)
            elif chip.contains(mouse_pos):
                fill_color = adjust_color(base_color, 1.2)
            else:
                fill_color = base_color

            radius = chip.radius
            chip_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            center = radius

            pygame.draw.circle(chip_surface, adjust_color(fill_color, 0.65), (center, center), radius)
            pygame.draw.circle(chip_surface, fill_color, (center, center), radius - 3)

            stripe_width = max(4, radius // 4)
            stripe_length = max(12, int(radius * 1.2))
            stripe_surface = pygame.Surface((stripe_width, stripe_length), pygame.SRCALPHA)
            pygame.draw.rect(stripe_surface, (238, 238, 238), stripe_surface.get_rect(), border_radius=stripe_width // 2)
            for angle in range(0, 360, 30):
                rotated = pygame.transform.rotate(stripe_surface, angle)
                rect = rotated.get_rect(center=(center, center))
                chip_surface.blit(rotated, rect)

            inner_ring_radius = max(6, radius - 10)
            white_ring_radius = max(4, inner_ring_radius - 5)
            core_radius = max(3, white_ring_radius - 4)
            pygame.draw.circle(chip_surface, adjust_color(fill_color, 0.8), (center, center), inner_ring_radius)
            pygame.draw.circle(chip_surface, (240, 240, 240), (center, center), white_ring_radius)
            pygame.draw.circle(chip_surface, fill_color, (center, center), core_radius)

            if timer is not None:
                progress = min(timer / CHIP_FLASH_DURATION, 1.0)
                flash_radius = int(radius + 12 * (1.0 - progress))
                flash_alpha = int(140 * (1.0 - progress))
                flash_surface = pygame.Surface((flash_radius * 2, flash_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(flash_surface, (255, 255, 255, flash_alpha), (flash_radius, flash_radius), flash_radius)
                screen.blit(flash_surface, (chip.center[0] - flash_radius, chip.center[1] - flash_radius))

            screen.blit(chip_surface, chip_surface.get_rect(center=chip.center))
            label = chip_font.render(str(chip.value), True, CHIP_LABEL_COLOR)
            screen.blit(label, label.get_rect(center=chip.center))

        def draw_bet_buttons(mouse_pos: Tuple[int, int]) -> None:
            for button in bet_buttons:
                if not button.enabled:
                    color = BET_BUTTON_DISABLED
                else:
                    color = BET_BUTTON_HOVER if button.rect.collidepoint(mouse_pos) else BET_BUTTON_BG
                pygame.draw.rect(screen, color, button.rect, border_radius=8)
                pygame.draw.rect(screen, CARD_BORDER, button.rect, width=2, border_radius=8)
                label_surface = button_font.render(button.label, True, BUTTON_TEXT)
                screen.blit(label_surface, label_surface.get_rect(center=button.rect.center))

        def draw_toggle_button(mouse_pos: Tuple[int, int]) -> None:
            color = BUTTON_DISABLED if not toggle_button.enabled else (
                BUTTON_HOVER if toggle_button.rect.collidepoint(mouse_pos) else BUTTON_BG
            )
            pygame.draw.rect(screen, color, toggle_button.rect, border_radius=8)
            pygame.draw.rect(screen, CARD_BORDER, toggle_button.rect, width=2, border_radius=8)
            label_surface = button_font.render(toggle_button.label, True, BUTTON_TEXT)
            screen.blit(label_surface, label_surface.get_rect(center=toggle_button.rect.center))

        def draw_bet_panel(mouse_pos: Tuple[int, int]) -> None:
            bet_surface = bankroll_font.render(
                f"Apuesta actual: {_format_value(current_bet)}",
                True,
                TEXT_PRIMARY,
            )
            screen.blit(bet_surface, layout["bet_info_pos"])

            if show_bet_panel:
                hint_surface = hint_font.render("Elige fichas para ajustar la apuesta.", True, TEXT_SECONDARY)
                screen.blit(hint_surface, layout["bet_hint_pos"])

            if status_text:
                status_surface = text_font.render(status_text, True, TEXT_PRIMARY)
                screen.blit(status_surface, layout["status_pos"])

            if show_bet_panel:
                for chip in chips:
                    chip_enabled = (
                        (not round_active)
                        and bankroll >= MIN_BET
                        and (current_bet + chip.value <= bankroll)
                    )
                    timer = chip_highlights.get(chip.value)
                    draw_chip(chip, chip_enabled, timer, mouse_pos)
                draw_bet_buttons(mouse_pos)

        def draw_action_buttons(mouse_pos: Tuple[int, int]) -> None:
            for button in action_buttons:
                if not button.enabled:
                    color = BUTTON_DISABLED
                else:
                    color = BUTTON_HOVER if button.rect.collidepoint(mouse_pos) else BUTTON_BG
                pygame.draw.rect(screen, color, button.rect, border_radius=8)
                pygame.draw.rect(screen, CARD_BORDER, button.rect, width=2, border_radius=8)
                label_surface = button_font.render(button.label, True, BUTTON_TEXT)
                screen.blit(label_surface, label_surface.get_rect(center=button.rect.center))

        def refresh_screen() -> None:
            screen.blit(background, (0, 0))
            title_surface = title_font.render("Blackjack", True, TEXT_PRIMARY)
            screen.blit(title_surface, title_surface.get_rect(midtop=(screen.get_width() // 2, layout["title_y"])))
            bankroll_surface = bankroll_font.render(f"Bankroll: {_format_value(bankroll)}", True, TEXT_PRIMARY)
            screen.blit(bankroll_surface, layout["bankroll_pos"])
            mouse_pos = pygame.mouse.get_pos()
            draw_bet_panel(mouse_pos)
            draw_toggle_button(mouse_pos)
            draw_hand("Crupier", game.dealer, int(layout["dealer_y"]), hide_dealer, "dealer")
            draw_hand("Jugador", game.player, int(layout["player_y"]), False, "player")
            draw_action_buttons(mouse_pos)

        def clamp_bet(raw_value: int) -> int:
            if raw_value <= 0:
                return 0
            max_bet = int(bankroll)
            if max_bet < MIN_BET:
                return 0
            return max(MIN_BET, min(raw_value, max_bet))

        def ensure_bet_within_bankroll() -> None:
            nonlocal current_bet
            current_bet = clamp_bet(int(current_bet))

        def reset_hand_animation(hand_key: str) -> None:
            for key in [k for k in card_animations if k[0] == hand_key]:
                del card_animations[key]

        def register_new_cards(hand_key: str, start_index: int, end_len: int) -> None:
            for idx in range(start_index, end_len):
                card_animations[(hand_key, idx)] = 0.0

        def update_animation_state(dt: float) -> None:
            for key in list(card_animations):
                elapsed = card_animations[key] + dt
                if elapsed >= ANIMATION_DURATION:
                    del card_animations[key]
                else:
                    card_animations[key] = elapsed
            for value in list(chip_highlights):
                elapsed = chip_highlights[value] + dt
                if elapsed >= CHIP_FLASH_DURATION:
                    del chip_highlights[value]
                else:
                    chip_highlights[value] = elapsed

        def update_buttons() -> None:
            toggle_button.enabled = not round_active
            if "hit" in button_map:
                button_map["hit"].enabled = round_active
            if "stand" in button_map:
                button_map["stand"].enabled = round_active
            can_deal = (
                (not round_active)
                and bankroll >= MIN_BET
                and current_bet >= MIN_BET
                and current_bet <= bankroll
            )
            if "next" in button_map:
                button_map["next"].enabled = can_deal
            if "reset" in button_map:
                button_map["reset"].enabled = True
            if "exit" in button_map:
                button_map["exit"].enabled = True
            for action in ("bet_minus", "bet_plus", "bet_clear", "bet_max"):
                if action in button_map:
                    enabled = (not round_active)
                    if action == "bet_minus":
                        enabled &= current_bet > 0
                    elif action == "bet_plus":
                        enabled &= bankroll >= MIN_BET and current_bet < bankroll
                    elif action == "bet_clear":
                        enabled &= current_bet > 0
                    elif action == "bet_max":
                        enabled &= bankroll >= MIN_BET
                    button_map[action].enabled = enabled

        def finish_round() -> None:
            nonlocal bankroll, round_active, hide_dealer, status_text
            hide_dealer = False
            outcome, payout = game.settle()
            net = payout * current_bet
            bankroll += net
            round_active = False
            status_text = f"{OUTCOME_TEXT[outcome]} ({_format_delta(net)})"
            if bankroll <= 0:
                status_text += " | Sin bankroll. Pulsa Reiniciar."
            ensure_bet_within_bankroll()
            update_buttons()

        def begin_round() -> None:
            nonlocal round_active, hide_dealer, status_text, show_bet_panel
            ensure_bet_within_bankroll()
            if bankroll < MIN_BET:
                status_text = "Sin bankroll. Pulsa Reiniciar."
                round_active = False
                hide_dealer = False
                update_buttons()
                return
            if current_bet < MIN_BET:
                status_text = "Selecciona una apuesta valida."
                update_buttons()
                return
            if show_bet_panel:
                show_bet_panel = False
                rebuild_ui()
            game.deal_initial()
            reset_hand_animation("player")
            reset_hand_animation("dealer")
            register_new_cards("player", 0, len(game.player.cards))
            register_new_cards("dealer", 0, len(game.dealer.cards))
            hide_dealer = True
            round_active = True
            status_text = ""
            update_buttons()
            if game.player.is_blackjack() or game.dealer.is_blackjack():
                dealer_before = len(game.dealer.cards)
                game.dealer_play()
                register_new_cards("dealer", dealer_before, len(game.dealer.cards))
                finish_round()

        def reset_session() -> None:
            nonlocal bankroll, game, round_active, hide_dealer, status_text, current_bet, show_bet_panel
            bankroll = START_BANKROLL
            game = BlackjackGame(rules=rules)
            round_active = False
            hide_dealer = True
            show_bet_panel = False
            rebuild_ui()
            status_text = ""
            current_bet = clamp_bet(DEFAULT_BET)
            card_animations.clear()
            chip_highlights.clear()
            update_buttons()

        def handle_action(action: str) -> bool:
            nonlocal status_text, current_bet, round_active, show_bet_panel
            if action == "exit":
                return False
            if action == "hit" and round_active:
                prev_len = len(game.player.cards)
                game.player.add(game.deck.draw())
                register_new_cards("player", prev_len, len(game.player.cards))
                if game.player.is_bust():
                    finish_round()
                elif game.player.total == 21:
                    dealer_before = len(game.dealer.cards)
                    game.dealer_play()
                    register_new_cards("dealer", dealer_before, len(game.dealer.cards))
                    finish_round()
                else:
                    status_text = ""
            elif action == "stand" and round_active:
                dealer_before = len(game.dealer.cards)
                game.dealer_play()
                register_new_cards("dealer", dealer_before, len(game.dealer.cards))
                finish_round()
            elif action == "next" and not round_active:
                begin_round()
            elif action == "reset":
                reset_session()
            elif action == "bet_minus" and not round_active:
                if current_bet <= MIN_BET:
                    current_bet = 0
                else:
                    current_bet = clamp_bet(current_bet - BET_STEP)
                status_text = ""
                update_buttons()
            elif action == "bet_plus" and not round_active:
                base = current_bet if current_bet else 0
                new_value = base + BET_STEP if base else MIN_BET
                current_bet = clamp_bet(new_value)
                status_text = ""
                update_buttons()
            elif action == "bet_clear" and not round_active:
                current_bet = 0
                status_text = ""
                update_buttons()
            elif action == "bet_max" and not round_active:
                current_bet = clamp_bet(int(bankroll))
                status_text = ""
                update_buttons()
            return True

        def handle_chip_click(chip: Chip) -> bool:
            nonlocal current_bet, status_text
            if round_active or not show_bet_panel or bankroll < MIN_BET:
                return False
            proposed = current_bet + chip.value if current_bet else chip.value
            if proposed > bankroll:
                status_text = "Bankroll insuficiente para esa ficha."
                return True
            current_bet = clamp_bet(int(proposed))
            chip_highlights[chip.value] = 0.0
            status_text = ""
            update_buttons()
            return True

        ensure_bet_within_bankroll()
        update_buttons()
        refresh_screen()
        pygame.display.flip()

        running = True
        while running:
            dt = clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    new_width = max(event.w, MIN_WINDOW_WIDTH)
                    new_height = max(event.h, MIN_WINDOW_HEIGHT)
                    rebuild_ui(new_width, new_height)
                    update_buttons()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if toggle_button.enabled and toggle_button.rect.collidepoint(event.pos):
                        if not round_active:
                            show_bet_panel = not show_bet_panel
                            if not show_bet_panel:
                                chip_highlights.clear()
                            rebuild_ui()
                            update_buttons()
                        continue
                    handled = False
                    if show_bet_panel and not round_active:
                        for chip in chips:
                            if chip.contains(event.pos):
                                handled = handle_chip_click(chip)
                                if handled:
                                    break
                    if handled:
                        continue
                    for button in list(button_map.values()):
                        if button.enabled and button.rect.collidepoint(event.pos):
                            if not handle_action(button.action):
                                running = False
                            break
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key in (pygame.K_h, pygame.K_SPACE):
                        if not handle_action("hit"):
                            running = False
                    elif event.key == pygame.K_s:
                        if not handle_action("stand"):
                            running = False
                    elif event.key == pygame.K_n:
                        if not handle_action("next"):
                            running = False
                    elif event.key == pygame.K_r:
                        if not handle_action("reset"):
                            running = False
                    elif event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                        if not handle_action("bet_plus"):
                            running = False
                    elif event.key == pygame.K_MINUS:
                        if not handle_action("bet_minus"):
                            running = False
            update_animation_state(dt)
            refresh_screen()
            pygame.display.flip()
    finally:
        pygame.quit()


if __name__ == "__main__":
    run_gui()

