# from typing import Literal, Sequence

# from chess.constants import Color
# from chess.piece import Bishop, King, Knight, Pawn, Queen, Rook

# BACKLINE = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
# FRONTLINE = [Pawn] * 8

# # An initial setup configuration
# SETUP: list[
#     tuple[
#         int,
#         Literal[Color.BLACK, Color.WHITE],
#         Sequence[type[Rook | Knight | Bishop | Queen | King | Pawn]],
#     ]
# ] = [
#     (0, Color.BLACK, BACKLINE),
#     (1, Color.BLACK, FRONTLINE),
#     (6, Color.WHITE, FRONTLINE),
#     (7, Color.WHITE, BACKLINE),
# ]
