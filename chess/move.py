from __future__ import annotations
from .piece import PieceColor
import chess

Position = tuple[int, int]


def get_valid_moves_pawn(board: chess.Board, row: int, col: int) -> list[Position]:
    valid_moves = []
    piece = board.piece(row, col)
    direction = -1 if piece.color == PieceColor.WHITE else 1
    
    valid_moves.append((row+direction, col))
    valid_moves.append((row+direction*2, col))
    valid_moves.append((row+direction, col+1))
    valid_moves.append((row+direction, col-1))
    print(valid_moves)
    return valid_moves


def get_valid_moves_rook(board: chess.Board, row: int, col: int) -> list[Position]:
    ...


def get_valid_moves_knight(board: chess.Board, row: int, col: int) -> list[Position]:
    ...


def get_valid_moves_bishop(board: chess.Board, row: int, col: int) -> list[Position]:
    ...


def get_valid_moves_queen(board: chess.Board, row: int, col: int) -> list[Position]:
    ...


def get_valid_moves_king(board: chess.Board, row: int, col: int) -> list[Position]:
    ...
