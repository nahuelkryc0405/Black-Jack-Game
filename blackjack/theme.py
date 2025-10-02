from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

Color = Tuple[int, int, int]
ColorA = Tuple[int, int, int, int]


@dataclass(frozen=True)
class FontSpec:
    family: str
    size: int
    bold: bool = False
    italic: bool = False


@dataclass(frozen=True)
class Theme:
    name: str
    colors: Dict[str, Color | ColorA]
    fonts: Dict[str, FontSpec]
    chip_colors: Dict[int, Color]
    status_colors: Dict[str, Color]
    card_size: Tuple[int, int] = (110, 160)
    card_spacing: int = 32
    button_radius: int = 10
    panel_radius: int = 18
    shadow_alpha: int = 110
    focus_glow: ColorA = (255, 255, 255, 110)


_THEMES: Dict[str, Theme] = {
    "modern": Theme(
        name="Modern",
        colors={
            "table_top": (26, 120, 88),
            "table_bottom": (8, 45, 36),
            "highlight": (120, 200, 160, 70),
            "text_primary": (240, 240, 240),
            "text_secondary": (205, 205, 205),
            "card_border": (16, 51, 34),
            "card_face": (250, 250, 250),
            "card_back": (64, 98, 148),
            "card_back_accent": (150, 175, 220),
            "card_text": (20, 20, 20),
            "card_red": (210, 60, 60),
            "button_bg": (42, 124, 200),
            "button_hover": (82, 164, 232),
            "button_disabled": (90, 90, 90),
            "button_text": (250, 250, 250),
            "panel_bg": (15, 40, 35, 210),
            "panel_border": (38, 120, 100),
            "panel_shadow": (0, 0, 0, 110),
            "toggle_bg": (52, 70, 105),
            "toggle_hover": (84, 110, 158),
            "toggle_disabled": (70, 70, 70),
            "chip_label": (250, 250, 250),
            "hud_badge_bg": (38, 100, 82),
            "hud_badge_text": (230, 230, 230),
            "overlay": (5, 20, 14, 170),
            "focus_outline": (255, 255, 255),
        },
        fonts={
            "title": FontSpec("bahnschrift", 52, bold=True),
            "label": FontSpec("bahnschrift", 34, bold=True),
            "text": FontSpec("segoe ui", 26),
            "bankroll": FontSpec("segoe ui", 28, bold=True),
            "hint": FontSpec("segoe ui", 20),
            "button": FontSpec("bahnschrift", 28, bold=True),
            "chip": FontSpec("bahnschrift", 20, bold=True),
            "small": FontSpec("segoe ui", 18),
            "card_rank": FontSpec("bahnschrift", 34, bold=True),
            "card_suit": FontSpec("segoe ui symbol", 46),
        },
        chip_colors={
            1: (70, 140, 230),
            5: (232, 90, 92),
            10: (76, 188, 132),
            25: (240, 196, 80),
        },
        status_colors={
            "info": (66, 135, 245),
            "win": (76, 175, 80),
            "loss": (226, 95, 85),
            "push": (195, 165, 52),
        },
        card_size=(118, 168),
        card_spacing=36,
        button_radius=12,
        panel_radius=22,
        shadow_alpha=120,
        focus_glow=(255, 255, 255, 140),
    ),
    "nocturne": Theme(
        name="Nocturne",
        colors={
            "table_top": (18, 40, 58),
            "table_bottom": (6, 18, 30),
            "highlight": (70, 120, 200, 60),
            "text_primary": (230, 236, 255),
            "text_secondary": (170, 190, 215),
            "card_border": (10, 35, 50),
            "card_face": (238, 240, 250),
            "card_back": (92, 74, 158),
            "card_back_accent": (142, 110, 210),
            "card_text": (25, 32, 45),
            "card_red": (225, 90, 120),
            "button_bg": (88, 115, 210),
            "button_hover": (118, 145, 240),
            "button_disabled": (80, 80, 115),
            "button_text": (240, 244, 252),
            "panel_bg": (14, 20, 34, 220),
            "panel_border": (90, 120, 200),
            "panel_shadow": (0, 0, 0, 150),
            "toggle_bg": (70, 80, 130),
            "toggle_hover": (98, 110, 170),
            "toggle_disabled": (68, 68, 110),
            "chip_label": (240, 242, 255),
            "hud_badge_bg": (70, 90, 165),
            "hud_badge_text": (220, 225, 255),
            "overlay": (10, 15, 30, 190),
            "focus_outline": (170, 205, 255),
        },
        fonts={
            "title": FontSpec("bahnschrift", 50, bold=True),
            "label": FontSpec("bahnschrift", 32, bold=True),
            "text": FontSpec("segoe ui", 26),
            "bankroll": FontSpec("segoe ui", 28, bold=True),
            "hint": FontSpec("segoe ui", 20),
            "button": FontSpec("bahnschrift", 26, bold=True),
            "chip": FontSpec("bahnschrift", 20, bold=True),
            "small": FontSpec("segoe ui", 18),
            "card_rank": FontSpec("bahnschrift", 34, bold=True),
            "card_suit": FontSpec("segoe ui symbol", 46),
        },
        chip_colors={
            1: (94, 140, 255),
            5: (220, 110, 160),
            10: (96, 210, 180),
            25: (252, 212, 96),
        },
        status_colors={
            "info": (110, 155, 255),
            "win": (96, 200, 155),
            "loss": (232, 120, 140),
            "push": (210, 180, 120),
        },
        card_size=(118, 168),
        card_spacing=36,
        button_radius=12,
        panel_radius=24,
        shadow_alpha=135,
        focus_glow=(210, 225, 255, 150),
    ),
}


def get_theme(name: str | None = None) -> Theme:
    """Return the configured theme (defaults to "modern")."""
    if name is None:
        key = "modern"
    else:
        key = name.strip().lower()
    if key not in _THEMES:
        raise ValueError(f"Theme '{name}' not found. Available: {', '.join(sorted(_THEMES))}")
    return _THEMES[key]


def list_themes() -> List[str]:
    return [theme.name for theme in _THEMES.values()]


def theme_keys() -> List[str]:
    """Expose internal keys for debugging or cycling themes."""
    return list(_THEMES.keys())

