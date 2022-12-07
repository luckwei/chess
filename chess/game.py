from __future__ import annotations

from abc import ABC, abstractmethod
from collections import UserDict
from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from enum import Enum, StrEnum, auto
from itertools import chain, product
from random import choice
from typing import Callable, Iterable, Self, Type

import numpy as np

from .setup import Setup

Position = tuple[int, int]


def ib(pos: Position):
    return max(pos) <= 7 and min(pos) >= 0


def in_bounds(func: Callable[[Position], Iterable[Move]]):
    def filtered(pos: Position, *args):
        return (m for m in func(pos, *args) if ib(m))

    return filtered


class Color(StrEnum):
    NONE = auto()
    WHITE = auto()
    BLACK = auto()

    @property
    def dir(self) -> int:
        return {Color.WHITE: -1, Color.BLACK: 1}.get(self, 0)

    @property
    def other(self) -> Self:
        return {
            Color.WHITE: Color.BLACK,
            Color.BLACK: Color.WHITE,
        }.get(self, self.NONE)

    @property
    def back_rank(self) -> int:
        return {self.WHITE: 7, self.BLACK: 0}.get(self, -1)


# Chess Pieces and its subclasses
@dataclass(slots=True, frozen=True, eq=True)
class Piece(ABC):
    color: Color

    @abstractmethod
    def moves(self, board: Board, pos: Position) -> list[Move]:
        ...


# PieceTypeColor = tuple[Type[Piece], Color]


class Empty(Piece):
    def __init__(self, *_):
        super().__init__(Color.NONE)

    def __bool__(self):
        return False

    def moves(self, board: Board, pos: Position) -> list[Move]:
        return []


class Pawn(Piece):
    def moves(self, board: Board, pos: Position) -> list[Move]:
        color = self.color
        dir = color.dir
        enpassant_trgt = board.enpassant_trgt
        enemy_br = color.other.back_rank

        all_moves = []

        # Enpassant
        all_moves.extend(
            to
            for d in [(dir, 1), (dir, -1)]
            if enpassant_trgt == (pos[0], (to := Move(pos, Flag.ENPASSANT) + d)[1])
        )

        # Pincer
        all_moves.extend(
            Move(to, Flag.PROMOTION if to[0] == enemy_br else Flag.NONE)
            for d in [(dir, 1), (dir, -1)]
            if ib(to := Move(pos) + d) and board[to].color == color.other
        )

        # Front long
        front_long = Move(pos, Flag.ENPASSANT_TRGT) + (2 * dir, 0)
        if pos[0] == 6 if color == Color.WHITE else 1 and not board[front_long]:
            all_moves.append(front_long)

        # Front short
        front_short = Move(
            to := Move(pos) + (dir, 0),
            Flag.PROMOTION if to[0] == color.other.back_rank else Flag.NONE,
        )
        if not board[front_short]:
            all_moves.append(front_short)

        return [m for m in all_moves if final_checks(m, pos, board)]


class Rook(Piece):
    def moves(self, board: Board, pos: Position) -> list[Move]:
        return [
            Move(m, Flag.LOSE_ROOK_PRIV)
            for m in perp_m(pos)
            if final_checks(m, pos, board)
        ]


class Knight(Piece):
    def moves(self, board: Board, pos: Position) -> list[Move]:
        return [m for m in lshp_m(pos) if final_checks(m, pos, board)]


class Bishop(Piece):
    def moves(self, board: Board, pos: Position) -> list[Move]:
        return [m for m in diag_m(pos) if final_checks(m, pos, board)]


class Queen(Piece):
    def moves(self, board: Board, pos: Position) -> list[Move]:
        return [m for m in [*diag_m(pos), *perp_m(pos)] if final_checks(m, pos, board)]


class King(Piece):
    def moves(self, board: Board, pos: Position) -> list[Move]:
        color = self.color
        back_rank = color.back_rank
        castling_perm = board.castling_perm

        all_moves = []

        king_not_checked = not board.checked

        # King-side castle
        if (
            castling_perm[color, Flag.CASTLE_KSIDE]
            and king_not_checked
            and kingcheck_safe(board, (back_rank, 5))
            and not any(board[back_rank, col] for col in [5, 6])
        ):
            all_moves.append(Move(pos, Flag.CASTLE_KSIDE) + (0, 2))

        # Queen-side castle
        if (
            castling_perm[color, Flag.CASTLE_QSIDE]
            and king_not_checked
            and kingcheck_safe(board, (back_rank, 3))
            and not any(board[back_rank, col] for col in [1, 2, 3])
        ):
            all_moves.append(Move(pos, Flag.CASTLE_QSIDE) + (0, -2))

        # Normal moves
        all_moves.extend(
            Move(m, Flag.LOSE_KING_PRIV) for m in [*diag_m(pos, 1), *perp_m(pos, 1)]
        )

        return [m for m in all_moves if final_checks(m, pos, board)]


FEN_MAP: dict[str, Piece] = {
    "p": Pawn(Color.BLACK),
    "n": Knight(Color.BLACK),
    "b": Bishop(Color.BLACK),
    "r": Rook(Color.BLACK),
    "q": Queen(Color.BLACK),
    "k": King(Color.BLACK),
    "P": Pawn(Color.WHITE),
    "N": Knight(Color.WHITE),
    "B": Bishop(Color.WHITE),
    "R": Rook(Color.WHITE),
    "Q": Queen(Color.WHITE),
    "K": King(Color.WHITE),
    " ": Empty(Color.NONE),
}


class Flag(Enum):
    NONE = auto()
    ENPASSANT_TRGT = auto()
    ENPASSANT = auto()
    CASTLE_QSIDE = auto()
    CASTLE_KSIDE = auto()
    LOSE_KING_PRIV = auto()
    LOSE_ROOK_PRIV = auto()
    PROMOTION = auto()

    def __bool__(self):
        return self != Flag.NONE


class CastlingPerm(UserDict[tuple[Color, Flag], bool]):
    __slots__ = ("data",)
    FEN_CASTLING = {
        (Color.WHITE, Flag.CASTLE_KSIDE): "K",
        (Color.WHITE, Flag.CASTLE_QSIDE): "Q",
        (Color.BLACK, Flag.CASTLE_KSIDE): "k",
        (Color.BLACK, Flag.CASTLE_QSIDE): "q",
    }

    def __init__(self, fen_substring: str = "KQkq") -> None:
        self.data = {
            color_side: i in fen_substring
            for color_side, i in self.FEN_CASTLING.items()
        }

    def falsify(self, color: Color, flag: Flag = Flag.LOSE_KING_PRIV) -> None:
        if Flag.LOSE_KING_PRIV:
            self[color, Flag.CASTLE_QSIDE] = False
            self[color, Flag.CASTLE_KSIDE] = False
            return
        self[color, flag] = False


def kingcheck_safe(board: Board, pos: Position, color: Color | None = None) -> bool:
    if color is None:
        color = board.color_move
    enemy_color = color.other

    if any(board[m] == Knight(enemy_color) for m in lshp_m(pos)):
        return False

    # check perpendiculars
    if any(
        board[m] in (Queen(enemy_color), Rook(enemy_color))
        and no_obstruction(board, pos, m)
        for m in perp_m(pos)
    ):
        return False

    # check diagonals
    if any(
        board[m] in (Queen(enemy_color), Bishop(enemy_color))
        and no_obstruction(board, pos, m)
        for m in diag_m(pos)
    ):
        return False

    # check adjacent for king
    if any(board[m] == King(enemy_color) for m in [*perp_m(pos, 1), *diag_m(pos, 1)]):
        return False

    # check pincer for pawn
    return not any(
        ib(m := Move(pos) + d) and board[m] == Pawn(enemy_color)
        for d in [(color.dir, 1), (color.dir, -1)]
    )


def no_obstruction(board: Board, pos: Position, move: Move) -> bool:

    pos_x, pos_y = pos
    to_x, to_y = move

    X = range(pos_x, to_x, 1 if to_x > pos_x else -1)
    Y = range(pos_y, to_y, 1 if to_y > pos_y else -1)

    # short moves and knights have no obstruction
    if min(len(X), len(Y)) == 1:
        return True

    # If both exist, diag move
    if X and Y:
        return not any(xy != pos and board[xy] for xy in zip(X, Y))

    # If x exists, perp col, same column
    if X:
        return not any((x, pos_y) != pos and board[x, pos_y] for x in X)

    # Else y exists, perp col, same row
    return not any((pos_x, y) != pos and board[pos_x, y] for y in Y)


def final_checks(
    move: Move,
    pos: Position,
    board: Board,
) -> bool:
    # From pos is color
    if board[pos].color != board.color_move:
        return False

    # To pos is not color
    if board[move].color == board.color_move:
        return False

    # Move should not have obstruction
    if not no_obstruction(board, pos, move):
        return False

    end_game = deepcopy(board)
    # simulate move
    end_game.simple_move(pos, move)
    if move.flag == Flag.ENPASSANT and board.enpassant_trgt:
        del end_game[board.enpassant_trgt]

    return not end_game.checked


class Move(Position):
    flag: Flag

    def __new__(cls, pos: Position, flag=Flag.NONE) -> Self:
        self = super().__new__(cls, pos)
        setattr(self, "flag", flag)
        return self

    def __add__(self, other: Position):
        return Move((self[0] + other[0], self[1] + other[1]), self.flag)

    def __radd__(self, other: Position):
        return self.__add__(other)

    def delta(self, delta: Position) -> Self:
        return Move((self[0] + delta[0], self[1] + delta[1]), self.flag)


@in_bounds
def diag_m(pos: Position, n=7) -> Iterable[Move]:
    quads = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    magnitude = zip((mag := range(1, n + 1)), mag)
    deltas = (np.multiply(*qm) for qm in product(quads, magnitude))

    return (Move(pos) + tuple(d) for d in deltas)


@in_bounds
def perp_m(pos: Position, n=7) -> Iterable[Move]:
    sides = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    magnitude = zip((mag := range(1, n + 1)), mag)
    deltas = (np.multiply(*sm) for sm in product(sides, magnitude))

    return (Move(pos) + tuple(d) for d in deltas)


@in_bounds
def lshp_m(pos: Position) -> Iterable[Move]:
    quads = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    magnitude = [(1, 2), (2, 1)]
    deltas = (np.multiply(*qm) for qm in product(quads, magnitude))

    return (Move(pos) + tuple(d) for d in deltas)


@dataclass(slots=True)
class Board(UserDict[Position, Piece]):
    fen_string: InitVar[str | None] = Setup.START

    color_move: Color = field(init=False)
    castling_perm: CastlingPerm = field(init=False)
    enpassant_trgt: Position | None = field(init=False)
    all_moves: dict[Position, list[Move]] = field(init=False)

    def __post_init__(self, fen_string):
        self.set_fen(fen_string)

    def set_fen(self, fen_string: str = Setup.START, random=False) -> None:

        if random:
            fen_string = choice(
                [
                    "1N3B2/5R2/3pP3/R6n/4P3/5prP/1K3PB1/4kq2 w - - 0 1",
                    "6k1/Np2P2R/p6B/K1P2Np1/1p3P2/P2p4/8/3n3R w - - 0 1",
                    "8/1p1r2p1/5P2/R6p/rN4P1/1kN1n3/1P1P3P/6K1 w - - 0 1",
                    "1q5B/1pp4p/PP6/1r6/R3B3/4P2k/p2N4/5Kb1 w - - 0 1",
                ]
            )

        (
            board_config,
            color_move,
            castling_perm,
            enpassant_trgt,
            *_,
        ) = fen_string.replace("/", "").split(" ")

        self.color_move = Color.WHITE if color_move == "w" else Color.BLACK

        self.castling_perm = CastlingPerm(castling_perm)

        if enpassant_trgt == "-":
            self.enpassant_trgt = None
        else:
            col, row = enpassant_trgt
            self.enpassant_trgt = 8 - int(row), "abcdefgh".index(col)

        for i in "12345678":
            board_config = board_config.replace(i, " " * int(i))

        self.data = {divmod(i, 8): FEN_MAP[p] for i, p in enumerate(board_config)}
        self.recompute_all_moves()

    def find_king(self, color: Color | None = None) -> Position:
        if color is None:
            color = self.color_move
        return next(
            pos
            for pos, piece in self.items()
            if piece.color == color and type(piece) == King
        )

    @property
    def checked(self) -> bool:
        return not kingcheck_safe(
            self, self.find_king(self.color_move), self.color_move
        )

    @property
    def checkmated(self) -> bool:
        return not self.all_moves and self.checked

    @property
    def stalemated(self, color: Color | None = None) -> bool:
        return not self.all_moves and not self.checked

    def recompute_all_moves(self, color: Color | None = None) -> None:
        color = self.color_move if color is None else color

        self.all_moves = {
            pos: moves
            for pos, piece in self.items()
            if piece.color == color and (moves := piece.moves(self, pos))
        }

    def __delitem__(self, pos: Position) -> None:
        self[pos] = Empty()

    def simple_move(self, frm: Position, to: Position) -> None:
        self[to] = self[frm]
        del self[frm]

    def execute_move(self, pos: Position, move: Move) -> None:
        flag = move.flag
        color = self.color_move
        castling_perm = self.castling_perm
        back_rank = color.back_rank

        if flag == Flag.CASTLE_QSIDE:
            self.simple_move((back_rank, 0), (back_rank, 3))
            castling_perm.falsify(color)

        if flag == Flag.CASTLE_KSIDE:
            self.simple_move((back_rank, 7), (back_rank, 5))
            castling_perm.falsify(color)

        if flag == Flag.LOSE_KING_PRIV:
            castling_perm.falsify(color)

        if flag == Flag.LOSE_ROOK_PRIV:
            castling_perm.falsify(
                color, Flag.CASTLE_QSIDE if pos == (back_rank, 0) else Flag.CASTLE_KSIDE
            )

        if flag == Flag.ENPASSANT and self.enpassant_trgt:
            del self[self.enpassant_trgt]

        self.enpassant_trgt = move if flag == Flag.ENPASSANT_TRGT else None

        self.simple_move(pos, move)

        if flag == Flag.PROMOTION:
            self[move] = Queen(color)

        self.color_move = self.color_move.other
        self.recompute_all_moves()
