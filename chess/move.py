from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from typing import Callable, Protocol, Self

from .piece import COLOR_STR, Piece, PieceColor, PieceType

Position = tuple[int, int]


class Board(Protocol):
    @property
    def color_turn(self) -> PieceColor:
        ...

    def piece(self, row, col) -> Piece:
        ...

    def find_king(self, color: PieceColor) -> Piece:
        ...

#### TO DEPRECIATE
def generate_moves_lshape(row, col, n=7) -> list[Position]:
    all_moves = [
        (row + 2 * sign1, col + sign2) for sign1, sign2 in product((-1, 1), (-1, 1))
    ] + [(row + sign1, col + 2 * sign2) for sign1, sign2 in product((-1, 1), (-1, 1))]
    return all_moves

@dataclass
class Move:
    board: Board
    move_from: Position
    move_to: Position
    capture_at: Position  # = field(init=False)

    @classmethod
    def create_diag_list(
        cls, board: Board, move_from: Position, n=7, front_only=False
    ) -> list[Self]:
        row, col = move_from
        move_to_list = []
        for i in range(1, n+1):
            move_to_list.append((row + i, col + i))  # NE
            move_to_list.append((row + i, col - i))  # NW
            if front_only:
                continue
            move_to_list.append((row - i, col + i))  # SE
            move_to_list.append((row - i, col - i))  # SW

        move_obj_list = [
            cls(board, move_from, move_to, move_to) for move_to in move_to_list
        ]
        #TODO:validation should not be done in the whole class, move into these factory class methods later

        return move_obj_list

    @classmethod
    def create_perp_list(cls, board: Board, move_from: Position, n=7) -> list[Self]:
        row, col = move_from
        move_to_list = []
        for i in range(1, n+1):
            move_to_list.append((row + i, col))  # N
            move_to_list.append((row - i, col))  # S
            move_to_list.append((row, col + i))  # E
            move_to_list.append((row, col - i))  # W

        move_obj_list = [
            cls(board, move_from, move_to, move_to) for move_to in move_to_list
        ]
        #TODO:validation should not be done in the whole class, move into these factory class methods later

        return move_obj_list

    @classmethod
    def create_lshape_list(cls, board, move_from) -> list[Self]:
        # to be rethought
        ...

    @classmethod
    def empassant(cls, board, move_from) -> list[Self]:
        # captures but different from when landed
        ...

    @classmethod
    def front_short(cls, board, move_from) -> list[Self]:
        # does not allow capture
        ...

    @classmethod
    def front_long(cls, board, move_from) -> list[Self]:
        # does not allow capture
        ...

    @property
    def valid(self) -> bool:
        return valid(self.board, *self.move_to)


def targetted_square(board: Board, row: int, col: int) -> bool:
    # check for enemy fire
    # bishops and queens on the diag, rook on the verts,
    # pawns on the near diags
    # knights on the Ls
    king = board.find_king(board.color_turn)
    return True


def king_in_check(board: Board) -> bool:
    # check for enemy fire in king's current psotion
    king = board.find_king(board.color_turn)
    return targetted_square(board, king.row, king.col)
    ...


def no_piece_in_line(board: Board, row: int, col: int) -> bool:
    return True
    ...


def enemy(board: Board, row: int, col: int) -> bool:
    return board.piece(row, col).color != board.color_turn


def in_grid(row: int, col: int) -> bool:
    return max(row, col) <= 7 and min(row, col) >= 0


def valid(board: Board, row: int, col: int) -> bool:
    return in_grid(row, col) and enemy(board, row, col) and king_in_check(board)



def get_valid_moves_empty(board: Board, row: int, col: int) -> list[Position]:
    print("!EMPTY!")
    return []

#### TO REFACTOR
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
    valid_moves = [move for move in all_moves.values() if valid(board, *move)]

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

    valid_moves = [move.move_to for move in Move.create_perp_list(board, (row, col)) if move.valid]

    print(
        f"{piece.type.value}\t{valid_moves=}"
        if valid_moves
        else f"!NO VALID {piece.type.value} MOVES!"
    )
    return valid_moves

#### TO REFACTOR
def get_valid_moves_knight(board: Board, row: int, col: int) -> list[Position]:
    if board.piece(row, col).color != board.color_turn:
        print(f"!{COLOR_STR[board.color_turn]}'s TURN!")
        return []
    piece = board.piece(row, col)

    all_moves = {f"lshp {move}": move for move in generate_moves_lshape(row, col)}
    valid_moves = [move for move in all_moves.values() if valid(board, *move)]

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

    valid_moves = [move.move_to for move in Move.create_diag_list(board, (row, col)) if move.valid]

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

    valid_moves = [move.move_to for move in Move.create_diag_list(board, (row, col)) + Move.create_perp_list(board, (row, col)) if move.valid]

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

    valid_moves = [move.move_to for move in Move.create_diag_list(board, (row, col), 1) + Move.create_perp_list(board, (row, col), 1) if move.valid]

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
