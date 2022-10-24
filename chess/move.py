from __future__ import annotations

from itertools import product
from typing import Callable, Protocol

from .piece import COLOR_STR, Piece, PieceColor, PieceType

Position = tuple[int, int]


class Board(Protocol):
    @property
    def color_turn(self) -> PieceColor:
        ...

    def piece(self, row, col) -> Piece:
        ...


def in_grid(row: int, col: int) -> bool:
    return max(row, col) <= 7 and min(row, col) >= 0
    # own king does not get checked


def generate_moves_diagonal(row, col, n=7) -> list[Position]:
    all_moves = [(row + i, col - i) for i in range(-n, n)] + [
        (row + i, col + i) for i in range(-n, n)
    ]
    all_moves = [move for move in all_moves if in_grid(*move) and move != (row, col)]
    return all_moves


def generate_moves_perpendicular(row, col, n=7) -> list[Position]:
    all_moves = [(row + i, col) for i in range(-n, n)] + [
        (row, col + i) for i in range(-n, n)
    ]
    all_moves = [move for move in all_moves if in_grid(*move) and move != (row, col)]
    return all_moves


def generate_moves_lshape(row, col, n=7) -> list[Position]:
    all_moves = [
        (row + 2 * sign1, col + sign2) for sign1, sign2 in product((-1, 1), (-1, 1))
    ] + [(row + sign1, col + 2 * sign2) for sign1, sign2 in product((-1, 1), (-1, 1))]
    all_moves = [move for move in all_moves if in_grid(*move) and move != (row, col)]
    return all_moves


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
    valid_moves = [move for move in all_moves.values() if in_grid(*move)]

    print(
        f"{piece.type.value}\t{valid_moves=}"
        if valid_moves
        else f"!NO VALID {piece.type.value} MOVES!"
    )
    return valid_moves


def get_valid_moves_rook(board: Board, row: int, col: int) -> list[Position]:
    if board.piece(row, col).color != board.color_turn:
        print(f"!{COLOR_STR[board.color_turn]}'s TURN!")
        return []
    piece = board.piece(row, col)

    all_moves = {f"perp {move}": move for move in generate_moves_perpendicular(row, col)}
    valid_moves = [move for move in all_moves.values() if in_grid(row, col)]

    print(
        f"{piece.type.value}\t{valid_moves=}"
        if valid_moves
        else f"!NO VALID {piece.type.value} MOVES!"
    )
    return valid_moves


def get_valid_moves_knight(board: Board, row: int, col: int) -> list[Position]:
    if board.piece(row, col).color != board.color_turn:
        print(f"!{COLOR_STR[board.color_turn]}'s TURN!")
        return []
    piece = board.piece(row, col)

    all_moves = {f"lshp {move}": move for move in generate_moves_lshape(row, col)}
    valid_moves = [move for move in all_moves.values() if in_grid(row, col)]

    print(
        f"{piece.type.value}\t{valid_moves=}"
        if valid_moves
        else f"!NO VALID {piece.type.value} MOVES!"
    )
    return valid_moves


def get_valid_moves_bishop(board: Board, row: int, col: int) -> list[Position]:
    if board.piece(row, col).color != board.color_turn:
        print(f"!{COLOR_STR[board.color_turn]}'s TURN!")
        return []
    piece = board.piece(row, col)

    all_moves = {f"diag {move}": move for move in generate_moves_diagonal(row, col)}

    valid_moves = [move for move in all_moves.values() if in_grid(row, col)]

    print(
        f"{piece.type.value}\t{valid_moves=}"
        if valid_moves
        else f"!NO VALID {piece.type.value} MOVES!"
    )
    return valid_moves


def get_valid_moves_queen(board: Board, row: int, col: int) -> list[Position]:
    if board.piece(row, col).color != board.color_turn:
        print(f"!{COLOR_STR[board.color_turn]}'s TURN!")
        return []
    piece = board.piece(row, col)

    all_moves = {f"diag {move}": move for move in generate_moves_diagonal(row, col)} | {
        f"perp {move}": move for move in generate_moves_perpendicular(row, col)
    }
    valid_moves = [move for move in all_moves.values() if in_grid(row, col)]

    print(
        f"{piece.type.value}\t{valid_moves=}"
        if valid_moves
        else f"!NO VALID {piece.type.value} MOVES!"
    )
    return valid_moves


def get_valid_moves_king(board: Board, row: int, col: int) -> list[Position]:
    if board.piece(row, col).color != board.color_turn:
        print(f"!{COLOR_STR[board.color_turn]}'s TURN!")
        return []
    piece = board.piece(row, col)

    all_moves = {
        f"diag {move}": move for move in generate_moves_diagonal(row, col, 1)
    } | {f"perp {move}": move for move in generate_moves_perpendicular(row, col, 1)}
    valid_moves = [move for move in all_moves.values() if in_grid(row, col)]

    print(
        f"{piece.type.value}\t{valid_moves=}"
        if valid_moves
        else f"!NO VALID {piece.type.value} MOVES!"
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
