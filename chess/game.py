from __future__ import annotations

from abc import ABC, abstractmethod
from collections import UserDict
from copy import deepcopy
from dataclasses import dataclass, field
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
            Move(m)
            for m in [(pos[0] + dir, pos[1] + 1), (pos[0] + dir, pos[1] - 1)]
            if in_bounds(m) and board[m].color == color.other
        )

        # Front long
        if (
            pos[0] == (pawn_rank := 6 if color == Color.WHITE else 1)
            and not board[(front_long := (pawn_rank + 2 * dir, pos[1]))]
        ):
            all_moves.append(Move(front_long, Flag.ENPASSANT_TRGT))

        if not board[(front_short := (pos[0] + dir, pos[1]))]:
            all_moves.append(Move(front_short))

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

        king_not_checked = board.checked(color)
        back_rank = color.back_rank

        # Short castle
        if (
            castling_flags[color, Flag.CASTLE_SHORT]
            and king_not_checked
            and kingcheck_safe(board, (back_rank, 5), color)
            and not any(board[(back_rank, col)] for col in [5, 6])
        ):
            all_moves.append(Move((pos[0], pos[1] + 2), Flag.CASTLE_SHORT))

        # Long castle
        if (
            castling_flags[color, Flag.CASTLE_LONG]
            and king_not_checked
            and kingcheck_safe(board, (back_rank, 3), color)
            and not any(board[(back_rank, col)] for col in [1, 2, 3])
        ):
            all_moves.append(Move((pos[0], pos[1] - 2), Flag.CASTLE_LONG))

        # Normal moves
        all_moves.extend(
            Move(m, Flag.LOSE_KING_PRIV)
            for m in [*diag_moves(pos, 1), *perp_moves(pos, 1)]
        )

        return [m for m in all_moves if final_checks(m, pos, board, color)]


FEN_MAP: dict[str, tuple[Color, Type[Piece]]] = {
    "p": (Color.BLACK, Pawn),
    "n": (Color.BLACK, Knight),
    "b": (Color.BLACK, Bishop),
    "r": (Color.BLACK, Rook),
    "q": (Color.BLACK, Queen),
    "k": (Color.BLACK, King),
    "P": (Color.WHITE, Pawn),
    "N": (Color.WHITE, Knight),
    "B": (Color.WHITE, Bishop),
    "R": (Color.WHITE, Rook),
    "Q": (Color.WHITE, Queen),
    "K": (Color.WHITE, King),
    " ": (Color.NONE, Empty),
}


class Flag(Enum):
    NONE = auto()
    ENPASSANT_TRGT = auto()
    ENPASSANT = auto()
    CASTLE_LONG = auto()
    CASTLE_SHORT = auto()
    LOSE_KING_PRIV = auto()
    LOSE_ROOK_PRIV = auto()


class CastlingFlags(UserDict[tuple[Color, Flag], bool]):
    def __init__(self) -> None:
        self.data = {
            (Color.WHITE, Flag.CASTLE_SHORT): True,
            (Color.WHITE, Flag.CASTLE_LONG): True,
            (Color.BLACK, Flag.CASTLE_SHORT): True,
            (Color.BLACK, Flag.CASTLE_LONG): True,
        }

    def falsify(self, color: Color, flag: Flag = Flag.NONE) -> None:
        if flag:
            self[color, flag] = False
            return
        self[color, Flag.CASTLE_LONG] = False
        self[color, Flag.CASTLE_SHORT] = False


def kingcheck_safe(board: Board, pos: Position, color: Color) -> bool:
    enemy_color = color.other
    

    if any(
        type(board[m]) == Knight and board[m].color == enemy_color for m in l_moves(pos)
    ):
        return False

    # check perpendiculars
    if any(
        type(board[m]) in (Queen, Rook)
        and board[m].color == enemy_color
        and no_obstruction(board, pos, m)
        for m in perp_moves(pos)
    ):
        return False

    # check diagonals
    if any(
        type(board[m]) in (Queen, Bishop)
        and board[m].color == enemy_color
        and no_obstruction(board, pos, m)
        for m in diag_moves(pos)
    ):
        return False

    # check adjacent for king
    if any(
        type(board[m]) == King and board[m].color == enemy_color
        for m in [*perp_moves(pos, 1), *diag_moves(pos, 1)]
    ):
        return False

    # check pincer for pawn
    return not any(
        type(board[m]) == King and board[m].color == enemy_color
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

    # King should not be checked in the end
    # FIXME?
    return not end_game.checked(color)


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
    for quadrant in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
        for magnitude in [(1, 2), (2, 1)]:
            x, y = np.multiply(quadrant, magnitude)
            moves.append(Move((pos[0] + x, pos[1] + y)))
    return filter(in_bounds, moves)


class Board(UserDict[Position, Piece]):
    def __init__(self, fen_string=Setup.START):
        self.data: dict[Position, Piece] = self.process_fen(fen_string)
        self.color_move: Color = Color.WHITE
        self.enpassant_target: Position | None = None
        self.castling_flags: CastlingFlags = CastlingFlags()

        self.all_moves: dict[Position, list[Move]]
        self.recompute_all_moves()

    @staticmethod
    def process_fen(fen_string: str = Setup.START) -> dict[Position, Piece]:
        board_configuration = fen_string.replace("/", "").split(" ")[0]

        for digit in "12345678":
            board_configuration = board_configuration.replace(digit, " " * int(digit))

        board = {}
        for i, p in enumerate(board_configuration):
            color, PieceType = FEN_MAP[p]
            row, col = divmod(i, 8)
            board[row, col] = PieceType(color)
        return board

    def king_pos(self, color: Color) -> Position:
        return next(
            pos
            for pos, piece in self.items()
            if piece.color == color and type(piece) == King
        )

    def toggle_color_move(self) -> None:
        self.color_move = self.color_move.other

    def checked(self, color: Color | None = None) -> bool:
        if color is None:
            color = self.color_move
        return not kingcheck_safe(self, self.king_pos(color), color)

    def checkmated(self, color: Color | None = None) -> bool:
        if color is None:
            color = self.color_move
        return not self.recompute_all_moves(color) and self.checked(color)

    def stalemated(self, color: Color | None = None) -> bool:
        if color is None:
            color = self.color_move
        return not self.recompute_all_moves(color) and not self.checked(color)

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

        if flag == Flag.CASTLE_LONG:
            self.simple_move((back_rank, 0), (back_rank, 3))
            castling_flags.falsify(color)

        if flag == Flag.CASTLE_SHORT:
            self.simple_move((back_rank, 7), (back_rank, 5))
            castling_flags.falsify(color)

        if flag == Flag.LOSE_KING_PRIV:
            castling_flags.falsify(color)

        if flag == Flag.LOSE_ROOK_PRIV:
            if pos == (back_rank, 0):
                castling_flags.falsify(color, Flag.CASTLE_LONG)
            else:
                castling_flags.falsify(color, Flag.CASTLE_SHORT)

        if flag == Flag.ENPASSANT and self.enpassant_target:
            del self[self.enpassant_target]

        self.enpassant_target = move if flag == Flag.ENPASSANT_TRGT else None

        self.simple_move(pos, move)
        self.toggle_color_move()
        self.recompute_all_moves()

        # if self.checked():
        #     print("CHECKED!")

        # if self.checkmated():
        #     print("CHECKMATE!")
        #     showinfo(
        #         "Game ended!",
        #         f"{self.color_move.other} WINS by CHECKMATE!\nPress q to start new game..",
        #     )

        # if self.stalemated():
        #     print("STALEMATE!")
        #     showinfo("Game ended!", f"DRAW BY STALMATE!\nPress q to start new game..")
