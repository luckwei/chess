from __future__ import annotations

import chess

Position = tuple[int, int]


def get_valid_moves_pawn(board: chess.Board, row: int, col: int) -> list[Position]:
    ...


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
