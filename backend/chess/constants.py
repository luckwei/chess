from __future__ import annotations

from enum import IntEnum, StrEnum


class SIZE(IntEnum):
    TILE = 60
    PIECE = 53


class Color(StrEnum):
    LIGHT_RED = "#ffd1f6"
    DARK_RED = "#9e0842"
    RED = "#f54842"
    LIGHT_BLUE = "#98e2fa"
    DARK_BLUE = "#2a7cf7"
    WHITE = "#FFFFFF"
    # YELLOW = "#f2cf1f"
    BABY_BLUE = "#a3e8ff"
    LIGHT_ORANGE = "#ffc2a3"
    GREY_ORANGE = "#80726b"
    VERY_DARK_RED = "#910303"
    LIGHTER_RED = "#ff8f8f"
    MUTED_GOLD = "#876604"
    LIGHT_YELLOW = "#ffe28c"
    YELLOW = "#fcd705"
    PALE_YELLOW = "#fffdb3"
    PALE_GREEN = "#c7fff2"
    DARK_GREEN = "#023614"
    GRAY = "#616161"
    PINK = "#b50061"
    LIGHT_PINK = "#fca2d2"


class THEME(StrEnum):
    LIGHT_TILES = Color.LIGHT_RED
    DARK_TILES = Color.DARK_RED
    ACTIVE_BG = Color.WHITE
    VALID_HIGHLIGHT_LIGHT = Color.LIGHT_PINK
    VALID_HIGHLIGHT_DARK = Color.PINK
    VALID_CAPTURE = Color.RED
    INVALID_TILE = Color.GRAY
    # SELECTED_TILE = Color.GREY_ORANGE
    CANDIDATE_TILE = Color.LIGHT_ORANGE
