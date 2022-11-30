from __future__ import annotations

from abc import ABC, abstractmethod
from collections import UserDict
from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from enum import Enum, StrEnum, auto
from itertools import product
from random import choice
from typing import Self, Type

import numpy as np

from .setup import Setup
from .types import Position


class Color(StrEnum):
    NONE = auto()
    WHITE = auto()
    BLACK = auto()

    @property
    def dir(self) -> int:
        return {self.WHITE: -1, self.BLACK: 1}.get(self, 0)

    @property
    def other(self) -> Self:
        return {
            self.WHITE: self.BLACK,
            self.BLACK: self.WHITE,
        }.get(self, self.NONE)

    @property
    def back_rank(self) -> int:
        return {self.WHITE: 7, self.BLACK: 0}.get(self, -1)


# Chess Pieces and its subclasses
@dataclass(slots=True, frozen=True, eq=True)
class Piece(ABC):
    color: Color
    _type: Type[Piece] = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "_type", type(self))

    @abstractmethod
    def moves(self, board: Board, pos: Position) -> list[Move]:
        ...


PieceTypeColor = tuple[Type[Piece], Color]


class Empty(Piece):
    def __init__(self, *_):
        super().__init__(Color.NONE)

    def __bool__(self):
        return False

    def moves(self, *args, **kwargs) -> list[Move]:
        return []


class Pawn(Piece):
    def moves(self, board: Board, pos: Position) -> list[Move]:
        color = self.color
        dir = color.dir
        pos_x, pos_y = pos
        enpassant_trgt = board.enpassant_trgt

        all_moves = []

        # Enpassant
        all_moves.extend(
            Move(m, Flag.ENPASSANT)
            for m in [(pos_x + dir, pos_y + 1), (pos_x + dir, pos_y - 1)]
            if enpassant_trgt == (pos_x, m[1])
        )

        # Pincer
        all_moves.extend(
            Move(m, Flag.PROMOTION if m[0] == color.other.back_rank else Flag.NONE)
            for m in [(pos_x + dir, pos_y + 1), (pos_x + dir, pos_y - 1)]
            if in_bounds(m) and board[m].color == color.other
        )

        # Front long
        if (
            pos_x == (pawn_rank := 6 if color == Color.WHITE else 1)
            and not board[(front_long := (pawn_rank + 2 * dir, pos_y))]
        ):
            all_moves.append(Move(front_long, Flag.ENPASSANT_TRGT))

        # Front short
        if not board[(front_short := (pos_x + dir, pos_y))]:
            all_moves.append(
                Move(
                    front_short,
                    Flag.PROMOTION
                    if front_short[0] == color.other.back_rank
                    else Flag.NONE,
                )
            )

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
        color = self.color
        return [m for m in diag_m(pos) if final_checks(m, pos, board)]


class Queen(Piece):
    def moves(self, board: Board, pos: Position) -> list[Move]:
        color = self.color
        return [
            m
            for m in [*diag_m(pos), *perp_m(pos)]
            if final_checks(m, pos, board)
        ]


class King(Piece):
    def moves(self, board: Board, pos: Position) -> list[Move]:
        color = self.color
        castling_perm = board.castling_perm
        pos_x, pos_y = pos

        all_moves = []

        king_not_checked = not board.checked
        back_rank = color.back_rank

        # King-side castle
        if (
            castling_perm[color, Flag.CASTLE_KSIDE]
            and king_not_checked
            and kingcheck_safe(board, (back_rank, 5), color)
            and not any(board[(back_rank, col)] for col in [5, 6])
        ):
            all_moves.append(Move((pos_x, pos_y + 2), Flag.CASTLE_KSIDE))

        # Queen-side castle
        if (
            castling_perm[color, Flag.CASTLE_QSIDE]
            and king_not_checked
            and kingcheck_safe(board, (back_rank, 3), color)
            and not any(board[(back_rank, col)] for col in [1, 2, 3])
        ):
            all_moves.append(Move((pos_x, pos_y - 2), Flag.CASTLE_QSIDE))

        # Normal moves
        all_moves.extend(
            Move(m, Flag.LOSE_KING_PRIV)
            for m in [*diag_m(pos, 1), *perp_m(pos, 1)]
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


def kingcheck_safe(board: Board, pos: Position, color: Color) -> bool:
    enemy_color = color.other
    pos_x, pos_y = pos

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
    if any(
        board[m] == King(enemy_color)
        for m in [*perp_m(pos, 1), *diag_m(pos, 1)]
    ):
        return False

    # check pincer for pawn
    return not any(
        in_bounds(m) and board[m] == Pawn(enemy_color)
        for m in [
            (pos_x + color.dir, pos_y + 1),
            (pos_x + color.dir, pos_y - 1),
        ]
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
    # enpassant_trgt = board.enpassant_trgt
    # color = board.color_move

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

class Delta(Position):
    def __new__(cls, x, y) -> Self:
        return tuple.__new__(cls, (x, y))

    def __add__(self, other: Position):
        return self[0] + other[0], self[1] + other[1]

    def __radd__(self, other: Position):
        return self.__add__(other)
    
    def __sub__(self, other: Position):
        return self[0] - other[0], self[1] - other[1]
    
    def __rsub__(self, other: Position):
        return other[0] - self[0], other[1] - other[0]
    
class Move(Delta):
    flag: Flag

    def __new__(cls, pos: Position, flag=Flag.NONE) -> Self:
        self = tuple.__new__(cls, pos)
        setattr(self, "flag", flag)
        return self


def in_bounds(pos: Position) -> bool:
    return max(pos) <= 7 and min(pos) >= 0


def diag_m(pos: Position, n=7) -> filter[Move]:
    pos_x, pos_y = pos

    moves = []
    for i in range(1, n + 1):
        NE = (pos_x + i, pos_y + i)
        NW = (pos_x + i, pos_y - i)
        SE = (pos_x - i, pos_y + i)
        SW = (pos_x - i, pos_y - i)
        moves.extend(Move(m) for m in [NE, NW, SE, SW])
    return filter(in_bounds, moves)


def perp_m(pos: Position, n=7) -> filter[Move]:
    pos_x, pos_y = pos

    moves = []
    for i in range(1, n + 1):
        N = (pos_x + i, pos_y)
        S = (pos_x - i, pos_y)
        E = (pos_x, pos_y + i)
        W = (pos_x, pos_y - i)
        moves.extend(Move(m) for m in [N, S, E, W])
    return filter(in_bounds, moves)


def lshp_m(pos: Position) -> filter[Move]:
    pos_x, pos_y = pos

    moves = []
    quadrant = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    magnitude = [(1, 2), (2, 1)]
    for q, m in product(quadrant, magnitude):
        x, y = np.multiply(q, m)
        moves.append(Move((pos_x + x, pos_y + y)))
    return filter(in_bounds, moves)


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

    def toggle_color_move(self) -> None:
        self.color_move = self.color_move.other

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
        if color is None:
            color = self.color_move
        all_moves = {}
        for pos, piece in self.items():
            if piece.color == color and (moves := piece.moves(self, pos)):
                all_moves[pos] = moves
        self.all_moves = all_moves

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

        self.toggle_color_move()
        self.recompute_all_moves()
