from __future__ import annotations

from abc import ABC, abstractmethod
from collections import UserDict
from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from enum import Enum, StrEnum, auto
from itertools import product
from tkinter.messagebox import showinfo
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
        return {Color.WHITE: -1, Color.BLACK: 1}.get(self, 0)

    @property
    def other(self) -> Self:
        return {
            Color.WHITE: Color.BLACK,
            Color.BLACK: Color.WHITE,
        }.get(self, Color.NONE)

    @property
    def back_rank(self) -> int:
        return {Color.WHITE: 7, Color.BLACK: 0}.get(self, -1)


# Chess Pieces and it's subclass
@dataclass
class Piece(ABC):
    color: Color

    @classmethod
    @property
    def type(cls) -> Type[Piece]:
        return cls

    @property
    def type_color(self) -> PieceTypeColor:
        return self.type, self.color

    @property
    def dir(self) -> int:
        return self.color.dir

    @abstractmethod
    def get_moves(
        self,
        board: Board,
        pos: Position,
        /,
        enpassant_target: Position | None,
        castling_flags: CastlingFlags,
    ) -> list[Move]:
        ...


PieceTypeColor = tuple[Type[Piece], Color]


@dataclass
class Empty(Piece):
    color: Color = Color.NONE

    def __bool__(self):
        return False

    def get_moves(self, *args, **kwargs) -> list[Move]:
        return []


@dataclass
class Pawn(Piece):
    def get_moves(
        self,
        board: Board,
        pos: Position,
        /,
        enpassant_target: Position | None,
        **kwargs,
    ) -> list[Move]:
        color = self.color
        dir = color.dir

        all_moves = []

        # Enpassant
        all_moves.extend(
            Move(m, Flag.ENPASSANT)
            for m in [(pos[0] + dir, pos[1] + 1), (pos[0] + dir, pos[1] - 1)]
            if enpassant_target == (pos[0], m[1])
        )

        # Pincer
        all_moves.extend(
            Move(m, Flag.PROMOTION if m[0] == color.other.back_rank else Flag.NONE)
            for m in [(pos[0] + dir, pos[1] + 1), (pos[0] + dir, pos[1] - 1)]
            if in_bounds(m) and board[m].color == color.other
        )

        # Front long
        if (
            pos[0] == (pawn_rank := 6 if color == Color.WHITE else 1)
            and not board[(front_long := (pawn_rank + 2 * dir, pos[1]))]
        ):
            all_moves.append(Move(front_long, Flag.ENPASSANT_TRGT))

        # Front short
        if not board[(front_short := (pos[0] + dir, pos[1]))]:
            all_moves.append(
                Move(
                    front_short,
                    Flag.PROMOTION
                    if front_short[0] == color.other.back_rank
                    else Flag.NONE,
                )
            )

        return [
            m for m in all_moves if final_checks(m, pos, board, color, enpassant_target)
        ]


@dataclass
class Rook(Piece):
    def get_moves(self, board: Board, pos: Position, **kwargs) -> list[Move]:
        color = self.color
        return [
            Move(m, Flag.LOSE_ROOK_PRIV)
            for m in perp_moves(pos)
            if final_checks(m, pos, board, color)
        ]


@dataclass
class Knight(Piece):
    def get_moves(self, board: Board, pos: Position, **kwargs) -> list[Move]:
        color = self.color
        return [m for m in l_moves(pos) if final_checks(m, pos, board, color)]


@dataclass
class Bishop(Piece):
    def get_moves(self, board: Board, pos: Position, **kwargs) -> list[Move]:
        color = self.color
        return [m for m in diag_moves(pos) if final_checks(m, pos, board, color)]


@dataclass
class Queen(Piece):
    def get_moves(self, board: Board, pos: Position, **kwargs) -> list[Move]:
        color = self.color
        return [
            m
            for m in [*diag_moves(pos), *perp_moves(pos)]
            if final_checks(m, pos, board, color)
        ]


@dataclass
class King(Piece):
    def get_moves(
        self, board: Board, pos: Position, /, castling_flags: CastlingFlags, **kwargs
    ) -> list[Move]:
        color = self.color
        all_moves = []

        king_not_checked = not board.checked
        back_rank = color.back_rank

        # King-side castle
        if (
            castling_flags[color, Flag.CASTLE_KSIDE]
            and king_not_checked
            and kingcheck_safe(board, (back_rank, 5), color)
            and not any(board[(back_rank, col)] for col in [5, 6])
        ):
            all_moves.append(Move((pos[0], pos[1] + 2), Flag.CASTLE_KSIDE))

        # Queen-side castle
        if (
            castling_flags[color, Flag.CASTLE_QSIDE]
            and king_not_checked
            and kingcheck_safe(board, (back_rank, 3), color)
            and not any(board[(back_rank, col)] for col in [1, 2, 3])
        ):
            all_moves.append(Move((pos[0], pos[1] - 2), Flag.CASTLE_QSIDE))

        # Normal moves
        all_moves.extend(
            Move(m, Flag.LOSE_KING_PRIV)
            for m in [*diag_moves(pos, 1), *perp_moves(pos, 1)]
        )

        return [m for m in all_moves if final_checks(m, pos, board, color)]


FEN_MAP: dict[str, PieceTypeColor] = {
    "p": (Pawn, Color.BLACK),
    "n": (Knight, Color.BLACK),
    "b": (Bishop, Color.BLACK),
    "r": (Rook, Color.BLACK),
    "q": (Queen, Color.BLACK),
    "k": (King, Color.BLACK),
    "P": (Pawn, Color.WHITE),
    "N": (Knight, Color.WHITE),
    "B": (Bishop, Color.WHITE),
    "R": (Rook, Color.WHITE),
    "Q": (Queen, Color.WHITE),
    "K": (King, Color.WHITE),
    " ": (Empty, Color.NONE),
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


class CastlingFlags(UserDict[tuple[Color, Flag], bool]):
    FEN_CASTLING_DICT = {
        (Color.WHITE, Flag.CASTLE_KSIDE): "K",
        (Color.WHITE, Flag.CASTLE_QSIDE): "Q",
        (Color.BLACK, Flag.CASTLE_KSIDE): "k",
        (Color.BLACK, Flag.CASTLE_QSIDE): "q",
    }

    def __init__(self, fen_substring: str = "KQkq") -> None:
        self.data = {
            color_side: i in fen_substring
            for color_side, i in self.FEN_CASTLING_DICT.items()
        }

    def falsify(self, color: Color, flag: Flag = Flag.NONE) -> None:
        if flag:
            self[color, flag] = False
            return
        self[color, Flag.CASTLE_QSIDE] = False
        self[color, Flag.CASTLE_KSIDE] = False


def kingcheck_safe(board: Board, pos: Position, color: Color) -> bool:
    enemy_color = color.other

    if any(
        board[m].type == Knight and board[m].color == enemy_color for m in l_moves(pos)
    ):
        return False

    # check perpendiculars
    if any(
        board[m].type in (Queen, Rook)
        and board[m].color == enemy_color
        and no_obstruction(board, pos, m)
        for m in perp_moves(pos)
    ):
        return False

    # check diagonals
    if any(
        board[m].type in (Queen, Bishop)
        and board[m].color == enemy_color
        and no_obstruction(board, pos, m)
        for m in diag_moves(pos)
    ):
        return False

    # check adjacent for king
    if any(
        board[m].type == King and board[m].color == enemy_color
        for m in [*perp_moves(pos, 1), *diag_moves(pos, 1)]
    ):
        return False

    # check pincer for pawn
    return not any(
        in_bounds(m) and board[m].type == Pawn and board[m].color == enemy_color
        for m in [
            (pos[0] + color.dir, pos[1] + 1),
            (pos[0] + color.dir, pos[1] - 1),
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
    color: Color,
    enpassant_target: Position | None = None,
) -> bool:

    # From pos is color
    if board[pos].color != color:
        return False

    # To pos is not color
    if board[move].color == color:
        return False

    # Move should not have obstruction
    if not no_obstruction(board, pos, move):
        return False

    to, flag = move, move.flag
    end_game = deepcopy(board)
    # simulate move
    end_game.simple_move(pos, to)
    if flag == Flag.ENPASSANT and enpassant_target:
        end_game[enpassant_target] = Empty()

    return not end_game.checked


class Move(Position):
    def __new__(cls, pos: Position, flag=Flag.NONE) -> Self:
        return super().__new__(cls, pos)

    def __init__(self, pos: Position, flag=Flag.NONE):
        self.flag = flag


def in_bounds(pos: Position) -> bool:
    return max(pos) <= 7 and min(pos) >= 0


def diag_moves(pos: Position, n=7) -> filter[Move]:
    moves = []
    for i in range(1, n + 1):
        NE = (pos[0] + i, pos[1] + i)
        NW = (pos[0] + i, pos[1] - i)
        SE = (pos[0] - i, pos[1] + i)
        SW = (pos[0] - i, pos[1] - i)
        moves.extend(Move(m) for m in [NE, NW, SE, SW])
    return filter(in_bounds, moves)


def perp_moves(pos: Position, n=7) -> filter[Move]:
    moves = []
    for i in range(1, n + 1):
        N = (pos[0] + i, pos[1])
        S = (pos[0] - i, pos[1])
        E = (pos[0], pos[1] + i)
        W = (pos[0], pos[1] - i)
        moves.extend(Move(m) for m in [N, S, E, W])
    return filter(in_bounds, moves)


def l_moves(pos: Position) -> filter[Move]:
    moves = []
    quadrant = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    magnitude = [(1, 2), (2, 1)]
    for q, m in product(quadrant, magnitude):
        x, y = np.multiply(q, m)
        moves.append(Move((pos[0] + x, pos[1] + y)))
    return filter(in_bounds, moves)


@dataclass
class Board(UserDict[Position, Piece]):
    fen_string: InitVar[str | None] = Setup.START

    color_move: Color = field(init=False)
    castling_flags: CastlingFlags = field(init=False)
    enpassant_target: Position | None = field(init=False)
    all_moves: dict[Position, list[Move]] = field(init=False)

    def __post_init__(self, fen_string):
        self.set_from_fen(fen_string)

    def set_from_fen(self, fen_string: str = Setup.START) -> None:
        (
            board_configuration,
            color_move,
            castling_flags,
            enpassant_trgt,
            *_,
        ) = fen_string.replace("/", "").split(" ")

        self.color_move = Color.WHITE if color_move == "w" else Color.BLACK

        self.castling_flags = CastlingFlags(castling_flags)

        if enpassant_trgt == "-":
            self.enpassant_target = None
        else:
            col, row = enpassant_trgt
            self.enpassant_target = 8 - int(row), "abcdefgh".index(col)

        for i in "12345678":
            board_configuration = board_configuration.replace(i, " " * int(i))

        board = {}
        for i, p in enumerate(board_configuration):
            PieceType, color = FEN_MAP[p]
            row, col = divmod(i, 8)
            board[row, col] = PieceType(color)
        self.data = board
        self.recompute_all_moves()

    def king_pos(self, color: Color) -> Position:
        return next(
            pos
            for pos, piece in self.items()
            if piece.color == color and piece.type == King
        )

    def toggle_color_move(self) -> None:
        self.color_move = self.color_move.other

    @property
    def checked(self) -> bool:
        return not kingcheck_safe(self, self.king_pos(self.color_move), self.color_move)

    @property
    def checkmated(self) -> bool:
        return not self.all_moves and self.checked

    @property
    def stalemated(self, color: Color | None = None) -> bool:
        return not self.all_moves and not self.checked

    def recompute_all_moves(self, color: Color | None = None) -> None:
        if color is None:
            color = self.color_move
        et, cf = self.enpassant_target, self.castling_flags
        all_moves = {}
        for pos, piece in self.items():
            if piece.color == color and (
                moves := piece.get_moves(
                    self,
                    pos,
                    enpassant_target=et,
                    castling_flags=cf,
                )
            ):
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
        castling_flags = self.castling_flags
        back_rank = color.back_rank

        if flag == Flag.CASTLE_QSIDE:
            self.simple_move((back_rank, 0), (back_rank, 3))
            castling_flags.falsify(color)

        if flag == Flag.CASTLE_KSIDE:
            self.simple_move((back_rank, 7), (back_rank, 5))
            castling_flags.falsify(color)

        if flag == Flag.LOSE_KING_PRIV:
            castling_flags.falsify(color)

        if flag == Flag.LOSE_ROOK_PRIV:
            if pos == (back_rank, 0):
                castling_flags.falsify(color, Flag.CASTLE_QSIDE)
            else:
                castling_flags.falsify(color, Flag.CASTLE_KSIDE)
                

        if flag == Flag.ENPASSANT and self.enpassant_target:
            del self[self.enpassant_target]

        self.enpassant_target = move if flag == Flag.ENPASSANT_TRGT else None

        self.simple_move(pos, move)
        
        if flag == Flag.PROMOTION:
            self[move] = Queen(color)

        self.toggle_color_move()
        self.recompute_all_moves()
