from .board import Board
from .constants import PIECE_SIZE, THEME, TILE_SIZE
from .move import Position, get_valid_moves_rook
from .piece import Piece
from .root import Root

# from .setup import SETUP
# TODO: ADD ERROR CASES (EG. PIECE CANNOT MOVE BEYOND GRID LIMITS, 
# KNIGHT, CANNOT JUMP OVER, KING CHECKS, COMPOSITE MOVEMENT?, EMPASSAT, CASTLING
# cannot capture own, must move on own turn

# Clean function to make more sense
# TODO: Add dot (circle) object on board to show moves
