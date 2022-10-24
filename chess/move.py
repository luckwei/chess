from __future__ import annotations

from typing import Callable, Protocol

from .piece import COLOR_STR, Piece, PieceColor, PieceType

Position = tuple[int, int]


class Board(Protocol):
    @property
    def color_turn(self) -> PieceColor:
        ...

    def piece(self, row, col) -> Piece:
        ...


def valid(move) -> bool:
    return max(move) <= 7 and min(move) >= 0


def get_valid_moves_empty(board: Board, row: int, col: int) -> list[Position]:
    print("!EMPTY!")
    return []


def get_valid_moves_pawn(board: Board, row: int, col: int) -> list[Position]:
    if board.piece(row, col).color != board.color_turn:
        print(f"!{COLOR_STR[board.color_turn]}'s TURN!")
        return []

    piece = board.piece(row, col)

    all_moves = {
        "move fwd 1": (row + piece.dir, col),
        "move fwd 2": (row + piece.dir * 2, col),
        "capture left": (row + piece.dir, col - 1),
        "capture right": (row + piece.dir, col + 1),
    }
    valid_moves = [move for move in all_moves.values() if valid(move)]

    print(
        f"{piece.type.value}\t{valid_moves=}\t{'!NO VALID MOVES!' if len(valid_moves)==0 else ''}"
    )
    return valid_moves


def get_valid_moves_rook(board: Board, row: int, col: int) -> list[Position]:
    if board.piece(row, col).color != board.color_turn:
        print(f"!{COLOR_STR[board.color_turn]}'s TURN!")
        return []
    piece = board.piece(row, col)

    all_moves = {}
    valid_moves = [move for move in all_moves.values() if valid(move)]

    print(
        f"{piece.type.value}\t{valid_moves=}\t{'!NO VALID MOVES!' if len(valid_moves)==0 else ''}"
    )
    return valid_moves


def get_valid_moves_knight(board: Board, row: int, col: int) -> list[Position]:
    if board.piece(row, col).color != board.color_turn:
        print(f"!{COLOR_STR[board.color_turn]}'s TURN!")
        return []
    piece = board.piece(row, col)

    all_moves = {}
    valid_moves = [move for move in all_moves.values() if valid(move)]

    print(
        f"{piece.type.value}\t{valid_moves=}\t{'!NO VALID MOVES!' if len(valid_moves)==0 else ''}"
    )
    return valid_moves


def get_valid_moves_bishop(board: Board, row: int, col: int) -> list[Position]:
    if board.piece(row, col).color != board.color_turn:
        print(f"!{COLOR_STR[board.color_turn]}'s TURN!")
        return []
    piece = board.piece(row, col)

    all_moves = {}
    valid_moves = [move for move in all_moves.values() if valid(move)]

    print(
        f"{piece.type.value}\t{valid_moves=}\t{'!NO VALID MOVES!' if len(valid_moves)==0 else ''}"
    )
    return valid_moves


def get_valid_moves_queen(board: Board, row: int, col: int) -> list[Position]:
    if board.piece(row, col).color != board.color_turn:
        print(f"!{COLOR_STR[board.color_turn]}'s TURN!")
        return []
    piece = board.piece(row, col)

    all_moves = {}
    valid_moves = [move for move in all_moves.values() if valid(move)]

    print(
        f"{piece.type.value}\t{valid_moves=}\t{'!NO VALID MOVES!' if len(valid_moves)==0 else ''}"
    )
    return valid_moves


def get_valid_moves_king(board: Board, row: int, col: int) -> list[Position]:
    if board.piece(row, col).color != board.color_turn:
        print(f"!{COLOR_STR[board.color_turn]}'s TURN!")
        return []
    piece = board.piece(row, col)

    all_moves = {}
    valid_moves = [move for move in all_moves.values() if valid(move)]

    print(
        f"{piece.type.value}\t{valid_moves=}\t{'!NO VALID MOVES!' if len(valid_moves)==0 else ''}"
    )
    return valid_moves


ValidMoveCalculator = Callable[[Board, int, int], list[Position]]

MOVE_CALCULATORS: dict[PieceType, ValidMoveCalculator] = {
    PieceType.EMPTY: get_valid_moves_empty,
    PieceType.ROOK: get_valid_moves_rook,
    PieceType.BISHOP: get_valid_moves_bishop,
    PieceType.KNIGHT: get_valid_moves_knight,
    PieceType.QUEEN: get_valid_moves_queen,
    PieceType.KING: get_valid_moves_king,
    PieceType.PAWN: get_valid_moves_pawn,
}
