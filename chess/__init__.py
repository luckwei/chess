from .board import Board  # Uses [constants], move, [piece], [setup]
from .constants import PIECE_SIZE, THEME, TILE_SIZE
from .move import Position, get_valid_moves_rook  # Uses (board), [piece]
from .piece import Piece
from .root import Root  # Uses board, [constants], [piece], -move-
from .setup import Setup

# from .setup import SETUP
# TODO: METACLASSES, OVERLOAD, SUPERCLASSESSSSSSS

# Clean function to make more sense
# TODO: Add dot (circle) object on board to show moves
