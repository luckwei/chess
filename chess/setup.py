from .constants import BLACK, WHITE
from .piece import Bishop, King, Knight, Pawn, Piece, Queen, Rook

BACKLINE = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
FRONTLINE = [Pawn] * 8

SETUP = [
    (0, BLACK, BACKLINE),
    (1, BLACK, FRONTLINE),
    (6, WHITE, FRONTLINE),
    (7, WHITE, BACKLINE),
]
