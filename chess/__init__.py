# No cyclic dependencies
from .board import Board  # Uses [constants], move, [piece], [setup]
from .constants import PIECE_SIZE, THEME, TILE_SIZE
from .move import Position, get_valid_moves_rook  # Uses (board) and [piece]
from .piece import Piece

# Use other packages
from .root import Root  # Uses board, [constants], [piece]
from .setup import Setup

# from .setup import SETUP
# TODO: ADD ERROR CASES (EG. PIECE CANNOT MOVE BEYOND GRID LIMITS,
# KNIGHT, CANNOT JUMP OVER, KING CHECKS, COMPOSITE MOVEMENT?, EMPASSAT, CASTLING
# cannot capture own, must move on own turn

# Clean function to make more sense
# TODO: Add dot (circle) object on board to show moves
