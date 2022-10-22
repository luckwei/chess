from enum import Enum, auto

# Sizing of
TILE_SIZE = 60
PIECE_SIZE = 53

class Color(Enum):
    WHITE = "white"
    BLACK = "black"

LIGHT = "#ffd1f6"
DARK = "#9e0842"

THEME = (LIGHT, DARK)
