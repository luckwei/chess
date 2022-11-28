from __future__ import annotations

from abc import ABC, abstractmethod
from collections import UserDict
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum, StrEnum, auto
from itertools import product
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

    def get_moves(self, *args, **kwargs) -> list:
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
    ) -> filter[Move]:
        def get_moves_pawn(
            board: Board, pos: Position, color: Color, enpassant_target: Position | None
        ) -> filter[Move]:
            dir = color.dir

            enpassant = filter(
                lambda m: in_bounds(m) and enpassant_target == (pos[0], m[1]),
                [
                    Move((pos[0] + dir, pos[1] + 1), Flag.ENPASSANT),
                    Move((pos[0] + dir, pos[1] - 1), Flag.ENPASSANT),
                ],
            )

            pincer = filter(
                lambda m: in_bounds(m) and board[m].color == color.other,
                [Move((pos[0] + dir, pos[1] + 1)), Move((pos[0] + dir, pos[1] - 1))],
            )

            front_long = filter(
                lambda m: pos[0] == (6 if color == Color.WHITE else 1) and not board[m],
                (Move((pos[0] + 2 * dir, pos[1]), Flag.ENPASSANT_TRGT),),
            )

            front_short = filter(
                lambda m: not board[m], (Move((pos[0] + dir, pos[1])),)
            )

            all_moves = (*enpassant, *pincer, *front_long, *front_short)

            return filter(
                lambda m: final_checks(board, pos, m, color, enpassant_target),
                all_moves,
            )

        return get_moves_pawn(board, pos, self.color, enpassant_target)


@dataclass
class Rook(Piece):
    def get_moves(self, board: Board, pos: Position, **kwargs) -> filter[Move]:
        def get_moves_rook(board: Board, pos: Position, color: Color) -> filter[Move]:
            all_moves = perp_m(pos)
            for move in all_moves:
                move.flag = Flag.LOSE_ROOK_PRIV
            return filter(lambda m: final_checks(board, pos, m, color), all_moves)

        return get_moves_rook(board, pos, self.color)


@dataclass
class Knight(Piece):
    def get_moves(self, board: Board, pos: Position, **kwargs) -> filter[Move]:
        def get_moves_knight(board: Board, pos: Position, color: Color) -> filter[Move]:
            all_moves = lshapes_m(pos)
            return filter(lambda m: final_checks(board, pos, m, color), all_moves)

        return get_moves_knight(board, pos, self.color)


@dataclass
class Bishop(Piece):
    def get_moves(self, board: Board, pos: Position, **kwargs) -> filter[Move]:
        return filter(lambda m: final_checks(board, pos, m, self.color), diag_m(pos))


@dataclass
class Queen(Piece):
    def get_moves(self, board: Board, pos: Position, **kwargs) -> filter[Move]:
        all_moves = (*diag_m(pos), *perp_m(pos))
        return filter(lambda m: final_checks(board, pos, m, self.color), all_moves)


@dataclass
class King(Piece):
    def get_moves(
        self, board: Board, pos: Position, /, castling_flags: CastlingFlags, **kwargs
    ) -> filter[Move]:
        color = self.color
        all_moves = []

        king_not_checked = board.checked(color)
        row = 7 if color == Color.WHITE else 0

        castle_short_valid = (
            king_not_checked
            and kingcheck_safe(board, (row, 5), color)
            and not any(board[(row, col)] for col in (5, 6))
            and castling_flags[color, Flag.CASTLE_SHORT],
        )

        castle_long_valid = (
            king_not_checked
            and kingcheck_safe(board, (row, 3), color)
            and not any(board[(row, col)] for col in (1, 2, 3))
            and castling_flags[color, Flag.CASTLE_LONG]
        )

        if castle_short_valid:
            all_moves.append(Move((pos[0], pos[1] + 2), Flag.CASTLE_SHORT))

        if castle_long_valid:
            all_moves.append(Move((pos[0], pos[1] - 2), Flag.CASTLE_LONG))

        normal_moves = (*diag_m(pos, 1), *perp_m(pos, 1))
        for move in normal_moves:
            move.flag = Flag.LOSE_KING_PRIV
        all_moves.extend(normal_moves)

        return filter(lambda m: final_checks(board, pos, m, color), all_moves)


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
            self.data[color, flag] = False
            return
        self.data[color, Flag.CASTLE_LONG] = False
        self.data[color, Flag.CASTLE_SHORT] = False


def kingcheck_safe(board: Board, pos: Position, color: Color) -> bool:
    enemy_color = color.other

    if any(
        type(board[move]) == Knight and board[move].color == enemy_color
        for move in lshapes_m(pos)
    ):
        return False

    # check perpendiculars
    if any(
        type(board[move]) in (Queen, Rook)
        and board[move].color == enemy_color
        and no_obstruction(board, pos, move)
        for move in perp_m(pos)
    ):
        return False

    # check diagonals
    if any(
        type(board[move]) in (Queen, Bishop)
        and board[move].color == enemy_color
        and no_obstruction(board, pos, move)
        for move in diag_m(pos)
    ):
        return False

    # check adjacent for king
    if any(
        type(board[move]) == King and board[move].color == enemy_color
        for move in (*perp_m(pos, 1), *diag_m(pos, 1))
    ):
        return False

    # check pincer for pawn
    return not any(
        type(board[move]) == King and board[move].color == enemy_color
        for move in [
            Move((pos[0] + color.dir, pos[1] + 1)),
            Move((pos[0] + color.dir, pos[1] - 1)),
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
    board: Board,
    pos: Position,
    move: Move,
    color: Color,
    enpassant_target: Position | None = None,
) -> bool:
    def is_color(board: Board, pos: Position, color: Color) -> bool:
        piece = board[pos]

        return color == piece.color

    def king_safe_at_end(
        board: Board,
        pos: Position,
        move: Move,
        color: Color,
        enpassant_target: Position | None = None,
    ) -> bool:
        # return True
        to, flag = move, move.flag

        end_game = deepcopy(board)
        # simulate move
        end_game.simple_move(pos, to)
        if flag == Flag.ENPASSANT and enpassant_target:
            end_game[enpassant_target] = Empty()

        return not end_game.checked(color)

    def not_color(board: Board, move: Move, color: Color) -> bool:
        return board[move].color != color

    return (
        is_color(board, pos, color)
        and not_color(board, move, color)
        and no_obstruction(board, pos, move)
        and king_safe_at_end(board, pos, move, color, enpassant_target)
    )


class Move(tuple):
    def __new__(cls, pos: Position, flag=Flag.NONE):
        return super().__new__(cls, pos)

    def __init__(self, pos: Position, flag=Flag.NONE):
        self.flag = flag


def in_bounds(p: Position):
    return max(p) <= 7 and min(p) >= 0


def diag_m(pos: Position, n=7) -> filter[Move]:
    moves = []
    for i in range(1, n + 1):
        NE = Move((pos[0] + i, pos[1] + i))
        NW = Move((pos[0] + i, pos[1] - i))
        SE = Move((pos[0] - i, pos[1] + i))
        SW = Move((pos[0] - i, pos[1] - i))
        moves.extend([NE, NW, SE, SW])
    return filter(in_bounds, moves)


def perp_m(pos: Position, n=7) -> filter[Move]:
    moves = []
    for i in range(1, n + 1):
        N = Move((pos[0] + i, pos[1]))
        S = Move((pos[0] - i, pos[1]))
        E = Move((pos[0], pos[1] + i))
        W = Move((pos[0], pos[1] - i))
        moves.extend([N, S, E, W])
    return filter(in_bounds, moves)


def lshapes_m(pos: Position) -> filter[Move]:
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

    def checked(self, color: Color) -> bool:
        return not kingcheck_safe(self, self.king_pos(color), color)

    def king_pos(self, color: Color) -> Position:
        return next(
            pos
            for pos, piece in self.items()
            if piece.color == color and type(piece) == King
        )

    def toggle_color_to_move(self) -> None:
        self.color_move = self.color_move.other

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

    def execute_move(self, frm: Position, to: Position, flag: Flag = Flag.NONE) -> None:
        # if self.checked:
        #     print("CHECKED!")

        # if self.checkmated:
        #     print("CHECKMATE!")
        #     showinfo(
        #         "Game ended!",
        #         f"{self.color_to_move.other} WINS by CHECKMATE!\nPress q to start new game..",
        #     )

        # if self.stalemated:
        #     print("STALEMATE!")
        #     showinfo("Game ended!", f"DRAW BY STALMATE!\nPress q to start new game..")
        color = self.color_move
        castling_flags = self.castling_flags
        back_rank = 7 if color == Color.WHITE else 0

        if flag == Flag.CASTLE_LONG:
            self.simple_move((back_rank, 0), (back_rank, 3))
            castling_flags.falsify(color)

        if flag == Flag.CASTLE_SHORT:
            self.simple_move((back_rank, 7), (back_rank, 5))
            castling_flags.falsify(color)

        if flag == Flag.LOSE_KING_PRIV:
            castling_flags.falsify(color)

        if flag == Flag.LOSE_ROOK_PRIV:
            if frm == (back_rank, 0):
                castling_flags.falsify(color, Flag.CASTLE_LONG)
            else:
                castling_flags.falsify(color, Flag.CASTLE_SHORT)

        if flag == Flag.ENPASSANT and self.enpassant_target:
            del self[self.enpassant_target]

        self.enpassant_target = to if flag == Flag.ENPASSANT_TRGT else None

        self.simple_move(frm, to)

        self.toggle_color_to_move()
