from typing import Sequence

from chess.constants import BLACK, WHITE
from chess.piece import Bishop, King, Knight, Pawn, Queen, Rook

BACKLINE = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
FRONTLINE = [Pawn] * 8

# An initial setup configuration
SETUP: list[
    tuple[int, bool, Sequence[type[Rook | Knight | Bishop | Queen | King | Pawn]]]
] = [
    (0, BLACK, BACKLINE),
    (1, BLACK, FRONTLINE),
    (6, WHITE, FRONTLINE),
    (7, WHITE, BACKLINE),
]
