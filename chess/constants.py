from __future__ import annotations

from enum import StrEnum

TILE_SIZE = 60
PIECE_SIZE = 53


class Color(StrEnum):
    LIGHT_RED = "#ffd1f6"
    DARK_RED = "#9e0842"
    RED = "#f54842"
    LIGHT_BLUE = "#98e2fa"
    DARK_BLUE = "#2a7cf7"
    WHITE = "#FFFFFF"


_ColorPair = tuple[Color, Color]


class THEME(StrEnum):
    LIGHT_TILES = Color.LIGHT_RED
    DARK_TILES = Color.DARK_RED
    ACTIVE_BG = Color.WHITE
    VALID_HIGHLIGHT = Color.WHITE
    INVALID_TILE = Color.RED
