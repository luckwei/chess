from __future__ import annotations
import chess

Position = tuple[int, int]

def get_valid_moves_rook(board: chess.Board, row:int, col:int)->list[Position]:
    ...