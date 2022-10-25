from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from typing import Callable, Self

import numpy as np

from .constants import THEME_RED
from .piece import COLOR_STR, FEN_MAP, Piece, PieceColor, PieceType
from .setup import Setup
from .types import ColorPair, Position

_Grid = dict[Position, Piece]


def empty_board() -> _Grid:
    return {pos: Piece(pos) for pos in product(range(8), repeat=2)}


@dataclass
class Board:
    theme: ColorPair = THEME_RED
    pieces: _Grid = field(init=False, default_factory=empty_board)
    color_turn: PieceColor = field(init=False, default=PieceColor.WHITE)
    empassat_target: Position | None = field(init=False, default=None)
    fifty_move_counter: int = field(init=False, default=0)
    # REcord down 50 move rule

    def __post_init__(self):
        self.update_from_fen(Setup.START)

    def toggle_color_turn(self):
        self.color_turn = (
            PieceColor.WHITE
            if self.color_turn == PieceColor.BLACK
            else PieceColor.BLACK
        )

    def update_from_fen(self, fen: str = Setup.START):
        config, color_turn, *_ = fen.replace("/", "").split(" ")
        self.color_turn = PieceColor.WHITE if color_turn == "w" else PieceColor.BLACK

        for digit in "12345678":
            config = config.replace(digit, " " * int(digit))

        for i, p in enumerate(config):
            if p == " ":
                continue
            self.place(Piece(divmod(i, 8), *FEN_MAP[p]))

    def find_king(self, color: PieceColor) -> Piece:
        return next(
            (
                piece
                for piece in self.pieces.values()
                if piece.type == PieceType.KING and piece.color == color
            )
        )

    def get_valid_moves(self, pos: Position) -> list[Move]:
        return MOVE_CALCULATORS[self.piece(pos).type](self, pos)

    def __str__(self) -> str:
        pieces_str = [str(piece) for piece in self.pieces.values()]
        rows = ["".join(pieces_str[i * 8 : (i + 1) * 8]) for i in range(8)]
        return "\n".join(rows)

    def place(self, piece: Piece) -> None:
        self.pieces[piece.pos] = piece

    def remove(self, pos: Position) -> None:
        self.place(Piece(pos))

    def piece(self, pos: Position) -> Piece:
        return self.pieces[pos]

    def empty(self, pos: Position) -> bool:
        return self.piece(pos).type == PieceType.EMPTY


@dataclass
class Move:
    board: Board
    move_from: Position
    move_to: Position
    capture_at: Position | None = None
    empassat_target: Position | None = None

    @classmethod
    def diag(cls, board: Board, move_from: Position, n=7) -> list[Self]:
        row, col = move_from
        move_obj_list = []
        for i in range(1, n + 1):
            NE = cls(board, move_from, move_to := (row + i, col + i), move_to)
            NW = cls(board, move_from, move_to := (row + i, col - i), move_to)
            SE = cls(board, move_from, move_to := (row - i, col + i), move_to)
            SW = cls(board, move_from, move_to := (row - i, col - i), move_to)
            move_obj_list.extend([NE, NW, SE, SW])
        # TODO:validation should not be done in the whole class, move into these factory class methods later

        return move_obj_list

    @classmethod
    def perp(cls, board: Board, move_from: Position, n=7) -> list[Self]:
        row, col = move_from
        move_obj_list = []
        for i in range(1, n + 1):
            N = cls(board, move_from, move_to := (row + i, col), move_to)
            S = cls(board, move_from, move_to := (row - i, col), move_to)
            E = cls(board, move_from, move_to := (row, col + i), move_to)
            W = cls(board, move_from, move_to := (row, col - i), move_to)
            move_obj_list.extend([N, S, E, W])
        # TODO:validation should not be done in the whole class, move into these factory class methods later

        return move_obj_list

    @classmethod
    def lshapes(cls, board: Board, move_from: Position) -> list[Self]:
        row, col = move_from
        direction = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        magnitude = [(1, 2), (2, 1)]
        vec = [np.multiply(*dm) for dm in product(direction, magnitude)]
        move_obj_list = [
            cls(board, move_from, move_to := (row + x, col + y), move_to)
            for x, y in vec
        ]
        return move_obj_list

    @classmethod
    def pincer(cls, board: Board, move_from: Position) -> list[Self]:
        row, col = move_from
        dir = board.piece(move_from).dir
        L = cls(board, move_from, move_to := (row + dir, col + 1), move_to)
        R = cls(board, move_from, move_to := (row + dir, col - 1), move_to)

        return [L, R]

    @classmethod
    def empassant(cls, board: Board, move_from: Position) -> list[Self]:
        row, col = move_from
        dir = board.piece(move_from).dir
        # implement board last move to check whether it was a jump long jump
        # maybe also implement piece last move to check if pawn at the side was a long jump
        L = cls(board, move_from, (row + dir, col + 1), (row, col + 1))
        R = cls(board, move_from, (row + dir, col - 1), (row, col - 1))

        return [L, R]

    @classmethod
    def front_short(cls, board: Board, move_from: Position) -> list[Self]:
        # does not allow capture
        # put condition here
        row, col = move_from
        dir = board.piece(move_from).dir

        F1 = cls(board, move_from, (row + dir, col), None)
        return [F1]

    @classmethod
    def front_long(cls, board, move_from: Position) -> list[Self]:
        # does not allow capture
        row, col = move_from
        dir = board.piece(move_from).dir

        F2 = cls(
            board, move_from, move_to := (row + 2 * dir, col), empassat_target=move_to
        )
        return [F2]

    # Valid should not be part of piece as property, either external or part of class methods
    @property
    def valid(self) -> bool:
        return (
            Checks.in_grid(self.move_to)
            and Checks.not_own_color(self.board, self.move_to)
            and Checks.king_not_checked(self.board)
            # either king not checked or king will not be checked, create OR condition TODO
        )


def print_valid_moves(moves: list[Move], piece: Piece):
    valid_moves = [move.move_to for move in moves]
    print(
        f"{piece.type}\t{valid_moves=}"
        if valid_moves
        else f"!NO VALID {piece.type} MOVES!"
    )


def get_valid_moves_empty(*args, **kwargs) -> list[Move]:
    print("!EMPTY!")
    return []


def get_valid_moves_pawn(board: Board, pos: Position) -> list[Move]:
    if board.piece(pos).color != board.color_turn:
        print(f"!{COLOR_STR[board.color_turn]}'s TURN!")
        return []

    all_moves = (
        Move.pincer(board, pos)
        + Move.empassant(board, pos)
        + Move.front_short(board, pos)
        + Move.front_long(board, pos)
    )
    valid_moves = [move for move in all_moves if move.valid]

    print_valid_moves(valid_moves, board.piece(pos))
    return valid_moves


def get_valid_moves_rook(board: Board, pos: Position) -> list[Move]:
    if board.piece(pos).color != board.color_turn:
        print(f"!{COLOR_STR[board.color_turn]}'s TURN!")
        return []

    all_moves = Move.perp(board, pos)
    valid_moves = [move for move in Move.perp(board, pos) if move.valid]

    print_valid_moves(valid_moves, board.piece(pos))
    return valid_moves


## TODO: Root remove mechanism, hence all these return list[Move], use Move information to do UI change
def get_valid_moves_knight(board: Board, pos: Position) -> list[Move]:
    if board.piece(pos).color != board.color_turn:
        print(f"!{COLOR_STR[board.color_turn]}'s TURN!")
        return []
    all_moves = Move.lshapes(board, pos)
    valid_moves = [move for move in all_moves if move.valid]

    print_valid_moves(valid_moves, board.piece(pos))
    return valid_moves


def get_valid_moves_bishop(board: Board, pos: Position) -> list[Move]:
    if board.piece(pos).color != board.color_turn:
        print(f"!{COLOR_STR[board.color_turn]}'s TURN!")
        return []

    all_moves = Move.diag(board, pos)
    valid_moves = [move for move in all_moves if move.valid]

    print_valid_moves(valid_moves, board.piece(pos))
    return valid_moves


def get_valid_moves_queen(board: Board, pos: Position) -> list[Move]:
    if board.piece(pos).color != board.color_turn:
        print(f"!{COLOR_STR[board.color_turn]}'s TURN!")
        return []

    all_moves = Move.diag(board, pos) + Move.perp(board, pos)
    valid_moves = [move for move in all_moves if move.valid]

    print_valid_moves(valid_moves, board.piece(pos))
    return valid_moves


def get_valid_moves_king(board: Board, pos: Position) -> list[Move]:
    if board.piece(pos).color != board.color_turn:
        print(f"!{COLOR_STR[board.color_turn]}'s TURN!")
        return []

    all_moves = Move.diag(board, pos, 1) + Move.perp(board, pos, 1)
    valid_moves = [move for move in all_moves if move.valid]

    print_valid_moves(valid_moves, board.piece(pos))
    return valid_moves


ValidMoveCalculator = Callable[[Board, Position], list[Move]]

MOVE_CALCULATORS: dict[PieceType, ValidMoveCalculator] = {
    PieceType.EMPTY: get_valid_moves_empty,
    PieceType.ROOK: get_valid_moves_rook,
    PieceType.BISHOP: get_valid_moves_bishop,
    PieceType.KNIGHT: get_valid_moves_knight,
    PieceType.QUEEN: get_valid_moves_queen,
    PieceType.KING: get_valid_moves_king,
    PieceType.PAWN: get_valid_moves_pawn,
}

from .types import Position


class Checks:
    @staticmethod
    def in_grid(pos: Position) -> bool:
        return max(pos) <= 7 and min(pos) >= 0

    @staticmethod
    def not_own_color(board: Board, pos: Position) -> bool:
        return board.piece(pos).color != board.color_turn

    @staticmethod
    def king_not_checked(board: Board) -> bool:
        # check for enemy fire in king's current psotion
        king = board.find_king(board.color_turn)
        return not_targetted(board, king.pos)

    @staticmethod
    def no_obstruction(board: Board, move_from: Position, move_to: Position) -> bool:
        ...


def not_targetted(board: Board, pos: Position) -> bool:
    # check for enemy fire
    # bishops and queens on the diag, rook on the verts,
    # pawns on the near diags
    # knights on the Ls
    return True
