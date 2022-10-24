from __future__ import annotations
from .piece import PieceColor
import chess

Position = tuple[int, int]


def get_valid_moves_empty(board: chess.Board, row: int, col: int) -> list[Position]:
    return []


def get_valid_moves_pawn(board: chess.Board, row: int, col: int) -> list[Position]:
    if board.piece(row, col).color != board.color_turn:
        return []

    piece = board.piece(row, col)

    valid_moves = []

    valid_moves.append((row + piece.dir, col))
    valid_moves.append((row + piece.dir * 2, col))
    valid_moves.append((row + piece.dir, col + 1))
    valid_moves.append((row + piece.dir, col - 1))
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
