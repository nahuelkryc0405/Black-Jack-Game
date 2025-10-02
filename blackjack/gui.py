
from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pygame

from .cards import Card
from .game import BlackjackGame, Rules
from .theme import Theme, get_theme, theme_keys

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

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 860
MIN_WINDOW_WIDTH = 720
MIN_WINDOW_HEIGHT = 480
SIDE_PANEL_MIN_WIDTH = 280
SIDE_PANEL_MAX_WIDTH = 360
MAX_HISTORY = 6

ANIMATION_DURATION = 0.35
CHIP_FLASH_DURATION = 0.4
STATUS_VISIBILITY = 4.0
FOCUS_PULSE_SPEED = 5.2

FOCUS_PRIORITY = [
    "hit",
    "stand",
    "next",
    "reset",
    "exit",
    "toggle_panel",
    "cycle_theme",
    "toggle_help",
    "bet_minus",
    "bet_plus",
    "bet_clear",
    "bet_max",
]

RED_SUITS = {"♥", "♦"}


@dataclass
class Button:
    label: str
    action: str
    rect: pygame.Rect
    enabled: bool = True
    category: str = "action"
    hotkey: Optional[str] = None


@dataclass
class Chip:
    value: int
    center: Tuple[int, int]
    radius: int

    def contains(self, pos: Tuple[int, int]) -> bool:
        dx = pos[0] - self.center[0]
        dy = pos[1] - self.center[1]
        return dx * dx + dy * dy <= self.radius * self.radius


@dataclass
class HistoryEntry:
    label: str
    delta: float
    kind: str
    timestamp: float


def _format_value(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.1f}"


def _format_delta(value: float) -> str:
    sign = "+" if value > 0 else ""
    if float(value).is_integer():
        return f"{sign}{int(value)}"
    return f"{sign}{value:.1f}"


def ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3


def ease_out_back(t: float) -> float:
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def ease_in_out_quad(t: float) -> float:
    if t < 0.5:
        return 2 * t * t
    return 1 - (-2 * t + 2) ** 2 / 2


def adjust_color(color: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
    return tuple(max(0, min(255, int(c * factor))) for c in color)


def blend_color(a: Tuple[int, int, int], b: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
    factor = max(0.0, min(1.0, factor))
    return (
        int(a[0] * (1 - factor) + b[0] * factor),
        int(a[1] * (1 - factor) + b[1] * factor),
        int(a[2] * (1 - factor) + b[2] * factor),
    )





def compute_layout(theme: Theme, width: int, height: int, show_controls: bool) -> Dict[str, float]:
    width = max(width, MIN_WINDOW_WIDTH)
    height = max(height, MIN_WINDOW_HEIGHT)

    margin = max(24, width // 48)
    base_card_w, base_card_h = theme.card_size

    if width >= 1280:
        mode = "wide"
        panel_width = min(SIDE_PANEL_MAX_WIDTH, max(SIDE_PANEL_MIN_WIDTH, width // 4))
        scoreboard_width = max(420, width - panel_width - margin * 3)
        scoreboard_height = 168 if show_controls else 138
        score_rect = (
            margin,
            margin,
            scoreboard_width,
            scoreboard_height,
        )
        panel_rect = (
            score_rect[0] + scoreboard_width + margin,
            margin,
            panel_width,
            height - margin * 2,
        )
        card_scale = 1.0
        row_padding = 110
    elif width >= 980:
        mode = "medium"
        panel_width = min(SIDE_PANEL_MAX_WIDTH - 30, max(SIDE_PANEL_MIN_WIDTH - 10, width // 3))
        scoreboard_width = max(380, width - panel_width - margin * 3)
        scoreboard_height = 160 if show_controls else 134
        score_rect = (
            margin,
            margin,
            scoreboard_width,
            scoreboard_height,
        )
        panel_rect = (
            score_rect[0] + scoreboard_width + margin,
            margin,
            panel_width,
            height - margin * 2,
        )
        card_scale = 0.92
        row_padding = 100
    else:
        mode = "compact"
        scoreboard_width = width - margin * 2
        scoreboard_height = 148 if show_controls else 124
        score_rect = (
            margin,
            margin,
            scoreboard_width,
            scoreboard_height,
        )
        panel_height = max(160, min(240, height // 3 + 40))
        panel_rect = (
            margin,
            height - margin - panel_height,
            scoreboard_width,
            panel_height,
        )
        card_scale = 0.78
        row_padding = 80

    panel_padding = 24 if mode != "compact" else 18

    if show_controls:
        chip_radius = max(18, min(34, width // 32)) if mode != "compact" else max(16, min(26, width // 40))
        chip_row_y = score_rect[1] + score_rect[3] + 24 + chip_radius
        bet_buttons_y = chip_row_y + chip_radius + 40
        table_top = bet_buttons_y + 60
    else:
        chip_radius = 0
        chip_row_y = score_rect[1] + score_rect[3] + 12
        bet_buttons_y = chip_row_y
        table_top = score_rect[1] + score_rect[3] + 24

    if mode != "compact":
        table_width = score_rect[2]
        table_left = score_rect[0]
        table_height = max(320, height - margin - table_top)
        button_row_y = min(height - 90, table_top + int(base_card_h * card_scale * 2) + row_padding + 110)
    else:
        table_width = score_rect[2]
        table_left = score_rect[0]
        button_row_y = panel_rect[1] - 90
        table_bottom = button_row_y - 30
        table_height = max(240, table_bottom - table_top)
        available = max(160, table_bottom - table_top)
        max_scale = (available - row_padding) / (base_card_h * 2) if available > row_padding else 0.0
        if max_scale <= 0:
            max_scale = 0.6
        card_scale = max(0.6, min(card_scale, max_scale))

    card_height = int(base_card_h * card_scale)
    card_spacing = int(theme.card_spacing * card_scale)

    dealer_y = table_top + 40
    player_gap = row_padding
    if mode == "compact":
        table_bottom = button_row_y - 30
        available = max(150, table_bottom - table_top)
        min_gap = 56
        player_gap = max(min_gap, min(row_padding, available - card_height * 2))
        total_needed = card_height * 2 + player_gap
        offset = max(12, (available - total_needed) // 2 + 12)
        dealer_y = table_top + offset
    player_y = dealer_y + card_height + player_gap

    ellipse_width = int(table_width * (1.1 if mode != "compact" else 0.95))
    ellipse_height = max(240, card_height * 2 + 180)
    ellipse_center_y = dealer_y + card_height // 2

    chip_spacing = (
        max(chip_radius * 2 + 32, min(170, table_width // 5)) if mode != "compact" else
        max(chip_radius * 2 + 26, min(150, table_width // 4))
    ) if show_controls and chip_radius else 0
    total_chip_width = chip_spacing * (len(BET_CHIPS) - 1) if show_controls else 0
    table_center_x = table_left + table_width // 2
    chip_start_x = table_center_x - total_chip_width // 2 if show_controls else 0

    bet_button_specs = [
        ("-1", "bet_minus", 76),
        ("+1", "bet_plus", 76),
        ("Reset", "bet_clear", 114),
        ("Max", "bet_max", 96),
    ]
    total_bet_width = (
        sum(spec[2] for spec in bet_button_specs) + (len(bet_button_specs) - 1) * 18
        if show_controls
        else 0
    )
    bet_button_start_x = table_center_x - total_bet_width // 2 if show_controls else 0
    if show_controls:
        min_start = table_left
        max_start = table_left + table_width - total_bet_width
        bet_button_start_x = max(min_start, min(bet_button_start_x, max_start))

    chip_centers = [
        (int(chip_start_x + idx * chip_spacing), int(chip_row_y))
        for idx in range(len(BET_CHIPS))
    ] if show_controls and chip_radius else []

    bank_pos = (score_rect[0] + 24, score_rect[1] + 24)
    bet_info_pos = (score_rect[0] + 24, bank_pos[1] + 38)
    bet_hint_pos = (score_rect[0] + 24, bet_info_pos[1] + 26)
    status_offset = 30 if show_controls else 16
    status_pos = (bank_pos[0], bet_hint_pos[1] + status_offset)

    return {
        "width": width,
        "height": height,
        "margin": margin,
        "mode": mode,
        "card_scale": card_scale,
        "card_spacing_px": card_spacing,
        "title_y": margin,
        "score_rect": score_rect,
        "panel_rect": panel_rect,
        "panel_padding": panel_padding,
        "table_rect": (
            table_left,
            table_top,
            table_width,
            table_height,
        ),
        "table_center_x": table_center_x,
        "bankroll_pos": bank_pos,
        "bet_info_pos": bet_info_pos,
        "bet_hint_pos": bet_hint_pos,
        "status_pos": status_pos,
        "chip_radius": chip_radius,
        "chip_centers": chip_centers,
        "bet_button_specs": bet_button_specs,
        "bet_button_start_x": bet_button_start_x,
        "bet_button_spacing": 18,
        "bet_buttons_y": bet_buttons_y,
        "dealer_y": dealer_y,
        "player_y": player_y,
        "button_row_y": button_row_y,
        "ellipse_size": (ellipse_width, ellipse_height),
        "ellipse_center_y": ellipse_center_y,
    }


def create_action_buttons(theme: Theme, layout: Dict[str, float]) -> List[Button]:
    mode = layout.get("mode", "wide")
    if mode == "compact":
        specs = [
            ("Pedir", "hit", 140, "H / Espacio"),
            ("Plantarse", "stand", 150, "S"),
            ("Repartir", "next", 160, "N"),
            ("Reiniciar", "reset", 160, "R"),
            ("Salir", "exit", 134, "Esc"),
        ]
        spacing = 16
        row_height = 54
    elif mode == "medium":
        specs = [
            ("Pedir", "hit", 144, "H / Espacio"),
            ("Plantarse", "stand", 156, "S"),
            ("Repartir", "next", 168, "N"),
            ("Reiniciar", "reset", 168, "R"),
            ("Salir", "exit", 136, "Esc"),
        ]
        spacing = 20
        row_height = 58
    else:
        specs = [
            ("Pedir", "hit", 150, "H / Espacio"),
            ("Plantarse", "stand", 170, "S"),
            ("Repartir", "next", 180, "N"),
            ("Reiniciar", "reset", 180, "R"),
            ("Salir", "exit", 140, "Esc"),
        ]
        spacing = 24
        row_height = 60

    table_rect = pygame.Rect(layout["table_rect"])
    buttons: List[Button] = []
    total_width = sum(width for _, _, width, _ in specs) + spacing * (len(specs) - 1)

    use_two_rows = mode == "compact" or total_width > table_rect.width
    if use_two_rows:
        rows = [specs[:3], specs[3:]]
        row_y = int(layout["button_row_y"])
        row_spacing = 18
        for row in rows:
            if not row:
                continue
            row_total = sum(width for _, _, width, _ in row) + spacing * (len(row) - 1)
            start_x = table_rect.centerx - row_total // 2
            offset = 0
            for label, action, width, hotkey in row:
                rect = pygame.Rect(int(start_x + offset), row_y, width, row_height)
                buttons.append(Button(label, action, rect, hotkey=hotkey))
                offset += width + spacing
            row_y += row_height + row_spacing
    else:
        start_x = table_rect.centerx - total_width // 2
        y = int(layout["button_row_y"])
        offset = 0
        for label, action, width, hotkey in specs:
            rect = pygame.Rect(int(start_x + offset), y, width, row_height)
            buttons.append(Button(label, action, rect, hotkey=hotkey))
            offset += width + spacing
    return buttons


def create_bet_buttons(theme: Theme, layout: Dict[str, float]) -> List[Button]:
    buttons: List[Button] = []
    x = int(layout["bet_button_start_x"])
    y = int(layout["bet_buttons_y"])
    spacing = int(layout.get("bet_button_spacing", 18))
    mode = layout.get("mode", "wide")
    button_height = 46 if mode == "compact" else 50
    for label, action, width in layout["bet_button_specs"]:
        rect = pygame.Rect(x, y, width, button_height)
        hint = None
        if action == "bet_minus":
            hint = "Flecha Izquierda"
        elif action == "bet_plus":
            hint = "Flecha Derecha"
        elif action == "bet_clear":
            hint = "Del"
        elif action == "bet_max":
            hint = "End"
        buttons.append(Button(label, action, rect, category="bet", hotkey=hint))
        x += width + spacing
    return buttons


def create_chips(theme: Theme, layout: Dict[str, float]) -> List[Chip]:
    radius = int(layout["chip_radius"])
    if radius <= 0:
        return []
    return [
        Chip(value, (int(cx), int(cy)), radius)
        for value, (cx, cy) in zip(BET_CHIPS, layout["chip_centers"])
    ]

def build_background(theme: Theme, size: Tuple[int, int], layout: Dict[str, float]) -> pygame.Surface:
    width, height = size
    surface = pygame.Surface(size)
    top = theme.colors["table_top"]
    bottom = theme.colors["table_bottom"]
    for y in range(height):
        blend = y / max(1, height - 1)
        color = (
            int(top[0] * (1 - blend) + bottom[0] * blend),
            int(top[1] * (1 - blend) + bottom[1] * blend),
            int(top[2] * (1 - blend) + bottom[2] * blend),
        )
        pygame.draw.line(surface, color, (0, y), (width, y))

    ellipse_width, ellipse_height = layout["ellipse_size"]
    if ellipse_width > 0 and ellipse_height > 0:
        highlight = pygame.Surface((ellipse_width, ellipse_height), pygame.SRCALPHA)
        pygame.draw.ellipse(highlight, theme.colors["highlight"], highlight.get_rect())
        table_rect = pygame.Rect(layout["table_rect"])
        ellipse_rect = highlight.get_rect(center=(table_rect.centerx, int(layout["ellipse_center_y"])))
        surface.blit(highlight, ellipse_rect)

    panel_rect = pygame.Rect(layout["panel_rect"])
    if panel_rect.width > 0 and panel_rect.height > 0:
        shadow = pygame.Surface((panel_rect.width + 20, panel_rect.height + 20), pygame.SRCALPHA)
        pygame.draw.rect(
            shadow,
            theme.colors["panel_shadow"],
            shadow.get_rect(),
            border_radius=theme.panel_radius + 6,
        )
        surface.blit(shadow, (panel_rect.x - 10, panel_rect.y - 10))
    return surface


def load_fonts(theme: Theme) -> Dict[str, pygame.font.Font]:
    fonts: Dict[str, pygame.font.Font] = {}
    for key, spec in theme.fonts.items():
        fonts[key] = pygame.font.SysFont(spec.family, spec.size, bold=spec.bold, italic=spec.italic)
    return fonts


class VisualAssets:
    def __init__(self, theme: Theme, fonts: Dict[str, pygame.font.Font]) -> None:
        self.theme = theme
        self.fonts = fonts
        self._card_face_cache: Dict[Tuple[str, str], pygame.Surface] = {}
        self._hidden_card: Optional[pygame.Surface] = None
        self._chip_cache: Dict[Tuple[int, int], pygame.Surface] = {}
        self._card_face_template = self._build_card_face_template()
        self._card_back_template = self._build_card_back_template()

    def _build_card_face_template(self) -> pygame.Surface:
        width, height = self.theme.card_size
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(
            surface,
            self.theme.colors["card_border"],
            surface.get_rect(),
            border_radius=self.theme.button_radius + 8,
        )
        inner = surface.get_rect().inflate(-8, -8)
        gradient = pygame.Surface(inner.size, pygame.SRCALPHA)
        top = self.theme.colors["card_face"]
        bottom = blend_color(self.theme.colors["card_face"], (255, 255, 255), 0.12)
        for y in range(inner.height):
            blend = y / max(1, inner.height - 1)
            color = (
                int(top[0] * (1 - blend) + bottom[0] * blend),
                int(top[1] * (1 - blend) + bottom[1] * blend),
                int(top[2] * (1 - blend) + bottom[2] * blend),
            )
            pygame.draw.line(gradient, color, (0, y), (inner.width, y))
        surface.blit(gradient, inner)
        highlight = pygame.Surface((inner.width, max(12, inner.height // 3)), pygame.SRCALPHA)
        pygame.draw.ellipse(highlight, (255, 255, 255, 42), highlight.get_rect())
        surface.blit(highlight, (inner.left, inner.top + 4))
        return surface

    def _build_card_back_template(self) -> pygame.Surface:
        width, height = self.theme.card_size
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(
            surface,
            self.theme.colors["card_border"],
            surface.get_rect(),
            border_radius=self.theme.button_radius + 8,
        )
        inner = surface.get_rect().inflate(-8, -8)
        gradient = pygame.Surface(inner.size, pygame.SRCALPHA)
        top = self.theme.colors["card_back"]
        bottom = blend_color(self.theme.colors["card_back"], (30, 44, 70), 0.3)
        for y in range(inner.height):
            blend = y / max(1, inner.height - 1)
            color = (
                int(top[0] * (1 - blend) + bottom[0] * blend),
                int(top[1] * (1 - blend) + bottom[1] * blend),
                int(top[2] * (1 - blend) + bottom[2] * blend),
            )
            pygame.draw.line(gradient, color, (0, y), (inner.width, y))
        surface.blit(gradient, inner)
        accent = self.theme.colors["card_back_accent"]
        pattern = pygame.Surface(inner.size, pygame.SRCALPHA)
        spacing = 14
        for x in range(-inner.height, inner.width + inner.height, spacing):
            pygame.draw.line(pattern, (*accent, 70), (x, 0), (x + inner.height, inner.height), 4)
        pattern = pygame.transform.rotate(pattern, 45)
        surface.blit(pattern, pattern.get_rect(center=inner.center))
        emblem = pygame.Surface((inner.width // 2, inner.height // 2), pygame.SRCALPHA)
        pygame.draw.polygon(
            emblem,
            (*accent, 160),
            [
                (emblem.get_width() // 2, 0),
                (emblem.get_width(), emblem.get_height() // 2),
                (emblem.get_width() // 2, emblem.get_height()),
                (0, emblem.get_height() // 2),
            ],
        )
        surface.blit(emblem, emblem.get_rect(center=inner.center))
        return surface

    def get_card_surface(self, card: Card, hidden: bool) -> pygame.Surface:
        if hidden:
            if self._hidden_card is None:
                self._hidden_card = self._card_back_template.copy()
            return self._hidden_card
        key = (card.rank, card.suit)
        if key not in self._card_face_cache:
            surface = self._card_face_template.copy()
            inner = surface.get_rect().inflate(-12, -12)
            rank_color = self.theme.colors["card_red"] if card.suit in RED_SUITS else self.theme.colors["card_text"]
            rank_surface = self.fonts["card_rank"].render(card.rank, True, rank_color)
            surface.blit(rank_surface, (inner.left, inner.top))
            surface.blit(
                rank_surface,
                (inner.right - rank_surface.get_width(), inner.bottom - rank_surface.get_height()),
            )
            suit_surface = self.fonts["card_suit"].render(card.suit, True, rank_color)
            surface.blit(suit_surface, suit_surface.get_rect(center=inner.center))
            self._card_face_cache[key] = surface
        return self._card_face_cache[key]

    def render_chip(
        self,
        value: int,
        radius: int,
        enabled: bool,
        hovered: bool,
        pulse: Optional[float],
    ) -> pygame.Surface:
        cache_key = (value, radius)
        base = self._chip_cache.get(cache_key)
        if base is None:
            base = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            center = radius
            chip_color = self.theme.chip_colors.get(value, (150, 150, 150))
            pygame.draw.circle(base, adjust_color(chip_color, 0.5), (center, center), radius)
            pygame.draw.circle(base, chip_color, (center, center), radius - 3)
            ring_color = blend_color(chip_color, (255, 255, 255), 0.35)
            pygame.draw.circle(base, ring_color, (center, center), radius - 8, width=4)
            stripe = pygame.Surface((max(3, radius // 2), radius * 2), pygame.SRCALPHA)
            pygame.draw.rect(stripe, (240, 240, 240, 210), stripe.get_rect(), border_radius=max(1, radius // 3))
            for angle in range(0, 360, 30):
                rotated = pygame.transform.rotate(stripe, angle)
                base.blit(rotated, rotated.get_rect(center=(center, center)))
            inner_radius = max(10, radius - 12)
            pygame.draw.circle(base, adjust_color(chip_color, 1.1), (center, center), inner_radius)
            self._chip_cache[cache_key] = base
        surface = base.copy()
        overlay_alpha = 0
        if not enabled:
            overlay_alpha = 150
        else:
            if hovered:
                overlay_alpha += 80
            if pulse is not None:
                progress = min(1.0, pulse / CHIP_FLASH_DURATION)
                overlay_alpha += int(140 * (1 - progress))
        if overlay_alpha:
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, overlay_alpha))
            surface.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        label_color = self.theme.colors["chip_label"] if enabled else adjust_color(self.theme.colors["chip_label"], 0.6)
        text_surface = self.fonts["chip"].render(str(value), True, label_color)
        surface.blit(text_surface, text_surface.get_rect(center=(radius, radius)))
        return surface

def run_gui(initial_theme: Optional[str] = None) -> None:
    pygame.init()
    try:
        themes = theme_keys()
        if not themes:
            themes = ["modern"]
        theme_index = 0
        if initial_theme:
            key = initial_theme.strip().lower()
            if key in themes:
                theme_index = themes.index(key)
        theme = get_theme(themes[theme_index])
        fonts = load_fonts(theme)
        assets = VisualAssets(theme, fonts)

        show_bet_panel = False
        show_help = False
        status_text = ""
        status_effect: Optional[Dict[str, object]] = None
        outcome_history: List[HistoryEntry] = []
        focused_action: Optional[str] = None
        focus_timer = 0.0

        layout = compute_layout(theme, WINDOW_WIDTH, WINDOW_HEIGHT, show_bet_panel)
        screen = pygame.display.set_mode((layout["width"], layout["height"]), pygame.RESIZABLE)
        pygame.display.set_caption("Blackjack")
        clock = pygame.time.Clock()

        background = build_background(theme, (layout["width"], layout["height"]), layout)
        card_width = theme.card_size[0]
        card_height = theme.card_size[1]
        card_spacing = theme.card_spacing

        action_buttons: List[Button] = []
        bet_buttons: List[Button] = []
        chips: List[Chip] = []
        toggle_button = Button("Mostrar apuesta", "toggle_panel", pygame.Rect(0, 0, 0, 0), category="misc", hotkey="B")
        theme_button = Button(f"Tema: {theme.name}", "cycle_theme", pygame.Rect(0, 0, 0, 0), category="misc", hotkey="T")
        help_button = Button("Ver ayuda (F1)", "toggle_help", pygame.Rect(0, 0, 0, 0), category="misc", hotkey="F1")
        misc_buttons = [toggle_button, theme_button, help_button]

        button_map: Dict[str, Button] = {}
        card_animations: Dict[Tuple[str, int], float] = {}
        chip_highlights: Dict[int, float] = {}

        rules = Rules(dealer_hits_soft_17=False, blackjack_pays=1.5)
        game = BlackjackGame(rules=rules)
        bankroll = START_BANKROLL
        current_bet = min(max(DEFAULT_BET, MIN_BET), int(bankroll))
        round_active = False
        hide_dealer = True

        def update_misc_labels() -> None:
            toggle_button.label = "Ocultar apuesta" if show_bet_panel else "Mostrar apuesta"
            theme_button.label = f"Tema: {theme.name}"
            help_button.label = "Cerrar ayuda" if show_help else "Ver ayuda (F1)"

        def position_misc_buttons() -> None:
            panel_rect = pygame.Rect(layout["panel_rect"])
            pad = layout["panel_padding"]
            mode = layout.get("mode", "wide")
            btn_height = 48 if mode != "compact" else 44
            if mode == "compact":
                available = panel_rect.width - pad * 2
                spacing = pad
                btn_width = max(120, (available - spacing * 2) // 3)
                start_x = panel_rect.x + pad + max(0, (available - (btn_width * 3 + spacing * 2)) // 2)
                toggle_button.rect = pygame.Rect(start_x, panel_rect.y + pad, btn_width, btn_height)
                theme_button.rect = pygame.Rect(toggle_button.rect.right + spacing, toggle_button.rect.y, btn_width, btn_height)
                help_button.rect = pygame.Rect(theme_button.rect.right + spacing, toggle_button.rect.y, btn_width, btn_height)
                layout["panel_content_top"] = toggle_button.rect.bottom + pad
            else:
                btn_width = max(140, (panel_rect.width - pad * 3) // 2)
                toggle_button.rect = pygame.Rect(panel_rect.x + pad, panel_rect.y + pad, btn_width, btn_height)
                theme_button.rect = pygame.Rect(toggle_button.rect.right + pad, toggle_button.rect.y, panel_rect.width - pad * 2 - btn_width, btn_height)
                help_button.rect = pygame.Rect(panel_rect.x + pad, toggle_button.rect.bottom + pad, panel_rect.width - pad * 2, btn_height)
                layout["panel_content_top"] = help_button.rect.bottom + pad

        def rebuild_button_map() -> None:
            button_map.clear()
            for button in action_buttons:
                button_map[button.action] = button
            for button in bet_buttons:
                button_map[button.action] = button
            for button in misc_buttons:
                button_map[button.action] = button

        def rebuild_ui(
            new_width: Optional[int] = None,
            new_height: Optional[int] = None,
            new_theme: Optional[Theme] = None,
        ) -> None:
            nonlocal layout, background, action_buttons, bet_buttons, chips, theme, fonts, assets, card_width, card_height, card_spacing, screen
            if new_theme is not None:
                theme = new_theme
                fonts = load_fonts(theme)
                assets = VisualAssets(theme, fonts)
            width = new_width or screen.get_width()
            height = new_height or screen.get_height()
            layout = compute_layout(theme, width, height, show_bet_panel)
            screen = pygame.display.set_mode((layout["width"], layout["height"]), pygame.RESIZABLE)
            card_scale = layout.get("card_scale", 1.0)
            card_width = max(60, int(theme.card_size[0] * card_scale))
            card_height = max(80, int(theme.card_size[1] * card_scale))
            card_spacing = max(16, int(theme.card_spacing * card_scale))
            background = build_background(theme, (layout["width"], layout["height"]), layout)
            action_buttons[:] = create_action_buttons(theme, layout)
            bet_buttons[:] = create_bet_buttons(theme, layout) if show_bet_panel else []
            chips[:] = create_chips(theme, layout) if show_bet_panel else []
            position_misc_buttons()
            rebuild_button_map()

        update_misc_labels()
        rebuild_ui(layout["width"], layout["height"])

        def set_status_effect(message: str, kind: str = "info") -> None:
            nonlocal status_effect
            status_effect = {"message": message, "kind": kind, "timer": 0.0}

        def register_history(label: str, delta: float, kind: str) -> None:
            outcome_history.append(HistoryEntry(label, delta, kind, time.time()))
            if len(outcome_history) > MAX_HISTORY:
                del outcome_history[0]

        def get_focusable_actions() -> List[str]:
            available = [action for action, button in button_map.items() if button.enabled]
            ordered = [action for action in FOCUS_PRIORITY if action in available]
            leftovers = [action for action in available if action not in ordered]
            return ordered + leftovers

        def ensure_focus_valid() -> None:
            nonlocal focused_action
            actions = get_focusable_actions()
            if not actions:
                focused_action = None
            elif focused_action not in actions:
                focused_action = actions[0]

        def focus_next(direction: int) -> None:
            nonlocal focused_action, focus_timer
            actions = get_focusable_actions()
            if not actions:
                focused_action = None
                return
            if focused_action not in actions:
                focused_action = actions[0]
            else:
                idx = actions.index(focused_action)
                focused_action = actions[(idx + direction) % len(actions)]
            focus_timer = 0.0
        def draw_focus_glow(target_rect: pygame.Rect) -> None:
            alpha = 90 + int(50 * (0.5 + 0.5 * math.sin(focus_timer * FOCUS_PULSE_SPEED)))
            glow_surface = pygame.Surface((target_rect.width + 12, target_rect.height + 12), pygame.SRCALPHA)
            glow_color = (*theme.focus_glow[:3], min(255, alpha))
            pygame.draw.rect(glow_surface, glow_color, glow_surface.get_rect(), border_radius=target_rect.height // 2)
            glow_rect = glow_surface.get_rect(center=target_rect.center)
            screen.blit(glow_surface, glow_rect)

        def paint_panel(rect: pygame.Rect) -> None:
            surface = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(surface, theme.colors["panel_bg"], surface.get_rect(), border_radius=theme.panel_radius)
            pygame.draw.rect(surface, theme.colors["panel_border"], surface.get_rect(), width=2, border_radius=theme.panel_radius)
            screen.blit(surface, rect)

        def draw_chip(chip: Chip, enabled: bool, timer: Optional[float], mouse_pos: Tuple[int, int]) -> None:
            pulse = timer if timer is not None else None
            hovered = chip.contains(mouse_pos)
            surface_chip = assets.render_chip(chip.value, chip.radius, enabled, hovered, pulse)
            screen.blit(surface_chip, surface_chip.get_rect(center=chip.center))

        def draw_bet_buttons(mouse_pos: Tuple[int, int]) -> None:
            mode = layout.get("mode", "wide")
            for button in bet_buttons:
                hovered = button.rect.collidepoint(mouse_pos)
                if not button.enabled:
                    color = theme.colors["button_disabled"]
                else:
                    color = theme.colors["button_hover"] if hovered or button.action == focused_action else theme.colors["button_bg"]
                pygame.draw.rect(screen, color, button.rect, border_radius=theme.button_radius)
                pygame.draw.rect(screen, theme.colors["card_border"], button.rect, width=2, border_radius=theme.button_radius)
                label_surface = fonts["button"].render(button.label, True, theme.colors["button_text"])
                screen.blit(label_surface, label_surface.get_rect(center=button.rect.center))
                if button.hotkey and mode != "compact":
                    hint_surface = fonts["hint"].render(button.hotkey, True, theme.colors["text_secondary"])
                    hint_rect = hint_surface.get_rect(midtop=(button.rect.centerx, button.rect.bottom + 4))
                    screen.blit(hint_surface, hint_rect)
                if button.enabled and button.action == focused_action:
                    draw_focus_glow(button.rect)

        def draw_action_buttons(mouse_pos: Tuple[int, int]) -> None:
            for button in action_buttons:
                hovered = button.rect.collidepoint(mouse_pos)
                if not button.enabled:
                    color = theme.colors["button_disabled"]
                else:
                    color = theme.colors["button_hover"] if hovered or button.action == focused_action else theme.colors["button_bg"]
                pygame.draw.rect(screen, color, button.rect, border_radius=theme.button_radius)
                pygame.draw.rect(screen, theme.colors["card_border"], button.rect, width=2, border_radius=theme.button_radius)
                label_surface = fonts["button"].render(button.label, True, theme.colors["button_text"])
                screen.blit(label_surface, label_surface.get_rect(center=button.rect.center))
                if button.hotkey:
                    hint_surface = fonts["hint"].render(button.hotkey, True, theme.colors["text_secondary"])
                    hint_rect = hint_surface.get_rect(midtop=(button.rect.centerx, button.rect.bottom + 6))
                    screen.blit(hint_surface, hint_rect)
                if button.enabled and button.action == focused_action:
                    draw_focus_glow(button.rect)

        def draw_misc_buttons(mouse_pos: Tuple[int, int]) -> None:
            for button in misc_buttons:
                hovered = button.rect.collidepoint(mouse_pos)
                if not button.enabled:
                    color = theme.colors["toggle_disabled"]
                else:
                    color = theme.colors["toggle_hover"] if hovered or button.action == focused_action else theme.colors["toggle_bg"]
                pygame.draw.rect(screen, color, button.rect, border_radius=theme.button_radius)
                pygame.draw.rect(screen, theme.colors["card_border"], button.rect, width=2, border_radius=theme.button_radius)
                label_surface = fonts["button"].render(button.label, True, theme.colors["button_text"])
                screen.blit(label_surface, label_surface.get_rect(center=button.rect.center))
                if button.hotkey:
                    hint_surface = fonts["hint"].render(button.hotkey, True, theme.colors["text_secondary"])
                    hint_rect = hint_surface.get_rect(midtop=(button.rect.centerx, button.rect.bottom + 4))
                    screen.blit(hint_surface, hint_rect)
                if button.enabled and button.action == focused_action:
                    draw_focus_glow(button.rect)

        def draw_bet_panel(mouse_pos: Tuple[int, int]) -> None:
            score_rect = pygame.Rect(layout["score_rect"])
            paint_panel(score_rect)
            bankroll_surface = fonts["bankroll"].render(f"Bankroll: {_format_value(bankroll)}", True, theme.colors["text_primary"])
            screen.blit(bankroll_surface, (score_rect.x + 24, score_rect.y + 24))
            bet_surface = fonts["bankroll"].render(f"Apuesta actual: {_format_value(current_bet)}", True, theme.colors["text_primary"])
            screen.blit(bet_surface, (score_rect.x + 24, score_rect.y + 56))

            progress_rect = pygame.Rect(score_rect.x + 24, score_rect.y + 94, score_rect.width - 48, 18)
            pygame.draw.rect(screen, adjust_color(theme.colors["panel_border"], 0.6), progress_rect, border_radius=9)
            if bankroll > 0 and current_bet > 0:
                fill_ratio = min(1.0, current_bet / max(1, bankroll))
                fill_width = max(6, int(progress_rect.width * fill_ratio))
                filled = pygame.Rect(progress_rect.x, progress_rect.y, fill_width, progress_rect.height)
                pygame.draw.rect(screen, theme.status_colors["info"], filled, border_radius=9)

            if status_text:
                status_surface = fonts["text"].render(status_text, True, theme.colors["text_primary"])
                screen.blit(status_surface, layout["status_pos"])

            if show_bet_panel:
                hint_surface = fonts["hint"].render("Usa fichas o botones para ajustar la apuesta.", True, theme.colors["text_secondary"])
                screen.blit(hint_surface, layout["bet_hint_pos"])
                for chip in chips:
                    chip_enabled = (
                        (not round_active)
                        and bankroll >= MIN_BET
                        and (current_bet + (chip.value if current_bet else chip.value)) <= bankroll
                    )
                    timer = chip_highlights.get(chip.value)
                    draw_chip(chip, chip_enabled, timer, mouse_pos)
                draw_bet_buttons(mouse_pos)

        def draw_side_panel(mouse_pos: Tuple[int, int]) -> None:
            panel_rect = pygame.Rect(layout["panel_rect"])
            paint_panel(panel_rect)
            content_x = panel_rect.x + layout["panel_padding"]
            y = layout.get("panel_content_top", panel_rect.y + layout["panel_padding"])
            mode = layout.get("mode", "wide")
            theme_label = fonts["hint"].render(f"Tema activo: {theme.name}", True, theme.colors["text_secondary"])
            screen.blit(theme_label, (content_x, y))
            y += theme_label.get_height() + 16
            history_title = fonts["label"].render("Ultimos resultados", True, theme.colors["text_primary"])
            screen.blit(history_title, (content_x, y))
            y += history_title.get_height() + 8
            max_items = 6 if mode != "compact" else 3
            items = list(reversed(outcome_history[-max_items:]))
            if items:
                for entry in items:
                    badge_rect = pygame.Rect(
                        content_x,
                        y,
                        panel_rect.width - layout["panel_padding"] * 2,
                        36,
                    )
                    badge_surface = pygame.Surface(badge_rect.size, pygame.SRCALPHA)
                    base_color = theme.status_colors.get(entry.kind, theme.status_colors["info"])
                    pygame.draw.rect(badge_surface, (*base_color, 130), badge_surface.get_rect(), border_radius=14)
                    pygame.draw.rect(badge_surface, (*base_color, 210), badge_surface.get_rect(), width=2, border_radius=14)
                    screen.blit(badge_surface, badge_rect)
                    label_surface = fonts["text"].render(entry.label, True, theme.colors["text_primary"])
                    screen.blit(label_surface, (badge_rect.x + 10, badge_rect.y + 6))
                    delta_surface = fonts["text"].render(_format_delta(entry.delta), True, theme.colors["text_primary"])
                    screen.blit(delta_surface, delta_surface.get_rect(midright=(badge_rect.right - 10, badge_rect.centery)))
                    y += badge_rect.height + 6
            else:
                empty = fonts["hint"].render("Juega una ronda para ver el historial.", True, theme.colors["text_secondary"])
                screen.blit(empty, (content_x, y))
                y += empty.get_height() + 6

            y += 12
            tips_title = fonts["label"].render("Atajos rapidos", True, theme.colors["text_primary"])
            screen.blit(tips_title, (content_x, y))
            y += tips_title.get_height() + 6
            tips = [
                "H o Espacio: Pedir carta",
                "S: Plantarse",
                "N: Repartir / Nueva ronda",
                "R: Reiniciar sesion",
                "T: Cambiar tema",
                "F1: Mostrar ayuda",
            ]
            if mode == "compact":
                tips = tips[:4] + ["B: Mostrar apuesta"]
            for tip in tips:
                tip_surface = fonts["hint"].render(tip, True, theme.colors["text_secondary"])
                screen.blit(tip_surface, (content_x, y))
                y += tip_surface.get_height() + 4

        def draw_status_banner() -> None:
            if not status_effect:
                return
            timer = status_effect["timer"]
            if timer > STATUS_VISIBILITY:
                return
            fade = 1.0
            if timer > STATUS_VISIBILITY * 0.7:
                fade = max(0.0, 1.0 - (timer - STATUS_VISIBILITY * 0.7) / (STATUS_VISIBILITY * 0.3))
            base_color = theme.status_colors.get(status_effect["kind"], theme.status_colors["info"])
            text_surface = fonts["text"].render(str(status_effect["message"]), True, theme.colors["button_text"])
            padding_x = 28
            padding_y = 16
            banner_surface = pygame.Surface((text_surface.get_width() + padding_x * 2, text_surface.get_height() + padding_y), pygame.SRCALPHA)
            pygame.draw.rect(
                banner_surface,
                (*base_color, int(220 * fade)),
                banner_surface.get_rect(),
                border_radius=theme.panel_radius,
            )
            pygame.draw.rect(
                banner_surface,
                (*base_color, 255),
                banner_surface.get_rect(),
                width=2,
                border_radius=theme.panel_radius,
            )
            banner_surface.blit(text_surface, text_surface.get_rect(center=banner_surface.get_rect().center))
            banner_rect = banner_surface.get_rect(midtop=(screen.get_width() // 2, layout["title_y"] - 12))
            screen.blit(banner_surface, banner_rect)

        def draw_help_overlay() -> None:
            overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
            overlay.fill(theme.colors["overlay"])
            screen.blit(overlay, (0, 0))
            panel_width = min(screen.get_width() - 140, 720)
            panel_height = min(screen.get_height() - 140, 520)
            panel_rect = pygame.Rect(
                (screen.get_width() - panel_width) // 2,
                (screen.get_height() - panel_height) // 2,
                panel_width,
                panel_height,
            )
            surface = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(surface, theme.colors["panel_bg"], surface.get_rect(), border_radius=theme.panel_radius)
            pygame.draw.rect(surface, theme.colors["panel_border"], surface.get_rect(), width=2, border_radius=theme.panel_radius)
            title_surface = fonts["title"].render("Guia rapida", True, theme.colors["text_primary"])
            surface.blit(title_surface, (32, 32))
            lines = [
                "Objetivo: acercate a 21 sin pasarte. El crupier debe llegar al menos a 17.",
                "1. Ajusta tu apuesta con fichas, botones o teclado.",
                "2. Pulsa Repartir para iniciar la ronda.",
                "3. Pide carta o plantate para resolver la mano.",
                "4. Consulta la barra lateral para resultados y tips.",
                "Teclas: H/Espacio, S, N, R, T, B, F1, Esc.",
            ]
            y = 32 + title_surface.get_height() + 18
            for line in lines:
                line_surface = fonts["text"].render(line, True, theme.colors["text_secondary"])
                surface.blit(line_surface, (32, y))
                y += line_surface.get_height() + 12
            footer = fonts["hint"].render("Pulsa F1 o Enter para cerrar.", True, theme.colors["text_secondary"])
            surface.blit(footer, (32, panel_rect.height - 48))
            screen.blit(surface, panel_rect)
        def draw_card(surface: pygame.Surface, rect: pygame.Rect, card: Card, hidden: bool, hand_key: str, idx: int) -> None:
            elapsed = card_animations.get((hand_key, idx), ANIMATION_DURATION)
            progress = min(elapsed / ANIMATION_DURATION, 1.0)
            eased = ease_out_cubic(progress)
            base_surface = assets.get_card_surface(card, hidden)
            if base_surface.get_size() != (card_width, card_height):
                target_surface = pygame.transform.smoothscale(base_surface, (card_width, card_height))
            else:
                target_surface = base_surface
            if eased < 1.0:
                scale = 0.86 + 0.14 * eased
                scaled_size = (int(card_width * scale), int(card_height * scale))
                card_surface = pygame.transform.smoothscale(target_surface, scaled_size)
            else:
                scaled_size = (card_width, card_height)
                card_surface = target_surface
            offset_y = int((1.0 - eased) * 36)
            draw_rect = card_surface.get_rect(center=(rect.centerx, rect.centery - offset_y))
            shadow_surface = pygame.Surface((int(scaled_size[0] * 0.92), max(18, int(scaled_size[1] * 0.28))), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surface, (0, 0, 0, int(theme.shadow_alpha * eased)), shadow_surface.get_rect())
            shadow_rect = shadow_surface.get_rect(center=(rect.centerx, rect.bottom + 10))
            surface.blit(shadow_surface, shadow_rect)
            surface.blit(card_surface, draw_rect)

        def draw_hand(title: str, hand, y: int, hide_hole: bool, hand_key: str) -> None:
            table_rect = pygame.Rect(layout["table_rect"])
            score_text = "??" if hide_hole and len(hand.cards) > 1 else str(hand.total)
            title_surface = fonts["label"].render(f"{title}: {score_text}", True, theme.colors["text_primary"])
            screen.blit(title_surface, title_surface.get_rect(midtop=(table_rect.centerx, y)))
            cards = hand.cards
            card_top = y + 58
            if not cards:
                empty_surface = fonts["text"].render("(sin cartas)", True, theme.colors["text_secondary"])
                screen.blit(empty_surface, empty_surface.get_rect(midtop=(table_rect.centerx, card_top + 18)))
                return
            count = len(cards)
            total_width = count * card_width + (count - 1) * card_spacing
            start_x = table_rect.centerx - total_width // 2
            for idx, card in enumerate(cards):
                rect = pygame.Rect(start_x + idx * (card_width + card_spacing), card_top, card_width, card_height)
                hidden = hide_hole and idx == 1
                draw_card(screen, rect, card, hidden, hand_key, idx)

        def refresh_screen() -> None:
            screen.blit(background, (0, 0))
            title_surface = fonts["title"].render("Blackjack", True, theme.colors["text_primary"])
            screen.blit(title_surface, title_surface.get_rect(midtop=(screen.get_width() // 2, layout["title_y"])))
            mouse_pos = pygame.mouse.get_pos()
            draw_bet_panel(mouse_pos)
            draw_side_panel(mouse_pos)
            draw_misc_buttons(mouse_pos)
            draw_hand("Crupier", game.dealer, int(layout["dealer_y"]), hide_dealer, "dealer")
            draw_hand("Jugador", game.player, int(layout["player_y"]), False, "player")
            draw_action_buttons(mouse_pos)
            draw_status_banner()
            if show_help:
                draw_help_overlay()

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
            nonlocal focus_timer, status_effect
            focus_timer += dt
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
            if status_effect:
                status_effect["timer"] = status_effect.get("timer", 0.0) + dt
                if status_effect["timer"] > STATUS_VISIBILITY:
                    status_effect = None

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
                    enabled = not round_active and show_bet_panel
                    if action == "bet_minus":
                        enabled &= current_bet > 0
                    elif action == "bet_plus":
                        enabled &= bankroll >= MIN_BET and current_bet < bankroll
                    elif action == "bet_clear":
                        enabled &= current_bet > 0
                    elif action == "bet_max":
                        enabled &= bankroll >= MIN_BET
                    button_map[action].enabled = enabled
            if "cycle_theme" in button_map:
                button_map["cycle_theme"].enabled = True
            if "toggle_help" in button_map:
                button_map["toggle_help"].enabled = True
            ensure_focus_valid()

        def finish_round() -> None:
            nonlocal bankroll, round_active, hide_dealer, status_text
            hide_dealer = False
            outcome, payout = game.settle()
            net = payout * current_bet
            bankroll += net
            round_active = False
            ensure_bet_within_bankroll()
            update_buttons()
            status_text = OUTCOME_TEXT[outcome]
            kind = "push"
            if net > 0:
                kind = "win"
            elif net < 0:
                kind = "loss"
            set_status_effect(f"{OUTCOME_TEXT[outcome]} ({_format_delta(net)})", kind)
            register_history(OUTCOME_TEXT[outcome], net, kind)
            if bankroll <= 0:
                status_text += " | Sin bankroll. Pulsa Reiniciar."

        def begin_round() -> None:
            nonlocal round_active, hide_dealer, status_text, show_bet_panel
            ensure_bet_within_bankroll()
            if bankroll < MIN_BET:
                status_text = "Sin bankroll. Pulsa Reiniciar."
                set_status_effect(status_text, "info")
                round_active = False
                hide_dealer = False
                update_buttons()
                return
            if current_bet < MIN_BET:
                status_text = "Selecciona una apuesta valida."
                set_status_effect(status_text, "info")
                update_buttons()
                return
            if show_bet_panel:
                show_bet_panel = False
                update_misc_labels()
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
            nonlocal bankroll, game, round_active, hide_dealer, status_text, current_bet, show_bet_panel, outcome_history
            bankroll = START_BANKROLL
            game = BlackjackGame(rules=rules)
            round_active = False
            hide_dealer = True
            show_bet_panel = False
            outcome_history = []
            status_text = ""
            current_bet = clamp_bet(DEFAULT_BET)
            card_animations.clear()
            chip_highlights.clear()
            update_misc_labels()
            rebuild_ui()
            update_buttons()
            set_status_effect("Sesion reiniciada", "info")

        def handle_action(action: str) -> bool:
            nonlocal status_text, current_bet, round_active, show_bet_panel, show_help, theme_index, theme, fonts, assets
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
            elif action == "bet_minus" and not round_active and show_bet_panel:
                current_bet = clamp_bet(current_bet - BET_STEP if current_bet else 0)
                status_text = ""
                update_buttons()
            elif action == "bet_plus" and not round_active and show_bet_panel:
                base = current_bet if current_bet else 0
                new_value = base + BET_STEP if base else MIN_BET
                current_bet = clamp_bet(new_value)
                status_text = ""
                update_buttons()
            elif action == "bet_clear" and not round_active and show_bet_panel:
                current_bet = 0
                status_text = ""
                update_buttons()
            elif action == "bet_max" and not round_active and show_bet_panel:
                current_bet = clamp_bet(int(bankroll))
                status_text = ""
                update_buttons()
            elif action == "toggle_panel" and not round_active:
                show_bet_panel = not show_bet_panel
                if not show_bet_panel:
                    chip_highlights.clear()
                update_misc_labels()
                rebuild_ui()
                update_buttons()
            elif action == "cycle_theme":
                if themes:
                    theme_index = (theme_index + 1) % len(themes)
                    new_theme = get_theme(themes[theme_index])
                    rebuild_ui(new_theme=new_theme)
                    update_misc_labels()
                    update_buttons()
                    set_status_effect(f"Tema: {new_theme.name}", "info")
            elif action == "toggle_help":
                show_help = not show_help
                update_misc_labels()
                set_status_effect("Ayuda activa" if show_help else "Ayuda cerrada", "info")
            return True

        def handle_chip_click(chip: Chip) -> bool:
            nonlocal current_bet, status_text
            if round_active or not show_bet_panel or bankroll < MIN_BET:
                return False
            proposed = current_bet + chip.value if current_bet else chip.value
            if proposed > bankroll:
                status_text = "Bankroll insuficiente para esa ficha."
                set_status_effect(status_text, "loss")
                return True
            current_bet = clamp_bet(int(proposed))
            chip_highlights[chip.value] = 0.0
            status_text = ""
            set_status_effect(f"Apuesta: {_format_value(current_bet)}", "info")
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
                        handle_action("toggle_panel")
                        continue
                    if theme_button.enabled and theme_button.rect.collidepoint(event.pos):
                        handle_action("cycle_theme")
                        continue
                    if help_button.enabled and help_button.rect.collidepoint(event.pos):
                        handle_action("toggle_help")
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
                    elif event.key == pygame.K_t:
                        handle_action("cycle_theme")
                    elif event.key == pygame.K_F1:
                        handle_action("toggle_help")
                    elif event.key == pygame.K_b:
                        handle_action("toggle_panel")
                    elif event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_RIGHT):
                        handle_action("bet_plus")
                    elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS, pygame.K_LEFT):
                        handle_action("bet_minus")
                    elif event.key == pygame.K_DELETE:
                        handle_action("bet_clear")
                    elif event.key == pygame.K_END:
                        handle_action("bet_max")
                    elif event.key == pygame.K_TAB:
                        direction = -1 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 1
                        focus_next(direction)
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        if focused_action and not handle_action(focused_action):
                            running = False
                elif event.type == pygame.KEYUP and event.key == pygame.K_F1 and show_help:
                    pass

            update_animation_state(dt)
            refresh_screen()
            pygame.display.flip()
    finally:
        pygame.quit()


if __name__ == "__main__":
    run_gui()
