from __future__ import annotations

from abc import abstractmethod
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
        dir_dict = {Color.WHITE: -1, Color.BLACK: 1}
        return dir_dict.get(self, 0)

    @property
    def other(self) -> Self:
        other_dict = {
            Color.WHITE: Color.BLACK,
            Color.BLACK: Color.WHITE,
        }
        return other_dict.get(self, Color.NONE)


# Chess Pieces and it's subclass
@dataclass
class Piece:
    color: Color

    @property
    def dir(self) -> int:
        return self.color.dir

    @abstractmethod
    def get_moves(
        self,
        board: Board,
        pos: Position,
        enpassant_target: Position | None,
        castling_flags: CastlingFlags,
    ) -> list[Move]:
        ...


@dataclass
class Empty(Piece):
    color: Color = field(init=False, default=Color.NONE)

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
        return get_moves_pawn(board, pos, self.color, enpassant_target)


@dataclass
class Rook(Piece):
    def get_moves(self, board: Board, pos: Position, **kwargs) -> list[Move]:
        return get_moves_rook(board, pos, self.color)


@dataclass
class Knight(Piece):
    def get_moves(self, board: Board, pos: Position, **kwargs) -> list[Move]:
        return get_moves_knight(board, pos, self.color)


@dataclass
class Bishop(Piece):
    def get_moves(self, board: Board, pos: Position, **kwargs) -> list[Move]:
        return get_moves_bishop(board, pos, self.color)


@dataclass
class Queen(Piece):
    def get_moves(self, board: Board, pos: Position, **kwargs) -> list[Move]:
        return get_moves_queen(board, pos, self.color)


@dataclass
class King(Piece):
    def get_moves(
        self, board: Board, pos: Position, /, castling_flags: CastlingFlags, **kwargs
    ) -> list[Move]:
        return get_moves_king(board, pos, self.color, castling_flags)


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


CastlingFlags = dict[Color, list[bool]]


def kingcheck_safe(board: Board, pos: Position, color: Color) -> bool:
    enemy_color = color.other

    enemy_knight = any(
        type(board[move]) == Knight and board[move].color == enemy_color
        for move in lshapes_m(pos)
    )

    # check perpendiculars
    enemy_rook_queen = any(
        type(board[move]) in (Queen, Rook)
        and board[move].color == enemy_color
        and no_obstruction(board, pos, move)
        for move in perp_m(pos)
    )

    # check diagonals
    enemy_bishop_queen = any(
        type(board[move]) in (Queen, Bishop)
        and board[move].color == enemy_color
        and no_obstruction(board, pos, move)
        for move in diag_m(pos)
    )

    # check adjacent for king
    enemy_king = any(
        type(board[move]) == King and board[move].color == enemy_color
        for move in perp_m(pos, 1) + diag_m(pos, 1)
    )

    # check pincer for pawn
    enemy_pawn = any(
        type(board[move]) == King and board[move].color == enemy_color
        for move in pincer_m(pos, color.dir)
    )

    # TODO: SEPARATE UI AND BACKEND LOGIC WITHIN ROOT

    return not any(
        [enemy_knight, enemy_rook_queen, enemy_bishop_queen, enemy_king, enemy_pawn]
    )


def castle_long_valid(
    board: Board, color: Color, castling_flags: CastlingFlags
) -> bool:
    row = 7 if color == Color.WHITE else 0

    pos_pass_long = kingcheck_safe(board, (row, 3), color)
    clear_lane = not any(board[(row, col)] for col in (1, 2, 3))

    king_not_checked = board.checked(color)

    priviledge = castling_flags[color][0]

    return all([pos_pass_long, clear_lane, king_not_checked, priviledge])


def castle_short_valid(
    board: Board, color: Color, castling_flags: CastlingFlags
) -> bool:
    row = 7 if color == Color.WHITE else 0

    pos_pass_short = kingcheck_safe(board, (row, 5), color)

    clear_lane = not any(board[(row, col)] for col in (5, 6))

    king_not_checked = board.checked(color)

    priviledge = castling_flags[color][1]

    return all([pos_pass_short, clear_lane, king_not_checked, priviledge])


def enpassant_valid(
    pos: Position, move: Move, enpassant_target: Position | None
) -> bool:

    enemy_pawn = (pos[0], move[1])
    return enpassant_target == enemy_pawn


def pincer_valid(board: Board, pos: Position, move: Move) -> bool:

    if not board[move]:
        return False
    if board[move].color != board[pos].color:
        return True
    return False


def front_long_valid(board: Board, pos: Position, move: Move, color: Color) -> bool:
    starting_rank = pos[0] == (6 if color == Color.WHITE else 1)
    return starting_rank and not board[move]


def front_short_valid(board: Board, move: Move) -> bool:
    to_piece = board[move]

    return not to_piece


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
        end_game.single_move(pos, to)
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


def final_checks_filter(
    moves: list[Move],
    board: Board,
    pos: Position,
    color: Color,
    enpassant_target: Position | None = None,
):
    return [m for m in moves if final_checks(board, pos, m, color, enpassant_target)]


class Flag(Enum):
    NONE = auto()
    ENPASSANT_TRGT = auto()
    ENPASSANT = auto()
    CASTLE_LONG = auto()
    CASTLE_SHORT = auto()
    LOSE_KING_PRIV = auto()
    LOSE_ROOK_PRIV = auto()


class Move(tuple):
    def __new__(cls, pos: Position, flag=Flag.NONE):
        return super().__new__(cls, pos)

    def __init__(self, pos: Position, flag=Flag.NONE):
        self.flag = flag


def in_bounds_filter(pos_list):
    return [p for p in pos_list if max(p) <= 7 and min(p) >= 0]


def diag_m(pos: Position, n=7) -> list[Move]:
    moves = []
    for i in range(1, n + 1):
        NE = Move((pos[0] + i, pos[1] + i))
        NW = Move((pos[0] + i, pos[1] - i))
        SE = Move((pos[0] - i, pos[1] + i))
        SW = Move((pos[0] - i, pos[1] - i))
        moves.extend([NE, NW, SE, SW])
    return in_bounds_filter(moves)


def perp_m(pos: Position, n=7) -> list[Move]:
    moves = []
    for i in range(1, n + 1):
        N = Move((pos[0] + i, pos[1]))
        S = Move((pos[0] - i, pos[1]))
        E = Move((pos[0], pos[1] + i))
        W = Move((pos[0], pos[1] - i))
        moves.extend([N, S, E, W])
    return in_bounds_filter(moves)


def lshapes_m(pos: Position) -> list[Move]:
    moves = []
    for quadrant in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
        for magnitude in [(1, 2), (2, 1)]:
            x, y = np.multiply(quadrant, magnitude)
            moves.append(Move((pos[0] + x, pos[1] + y)))
    return in_bounds_filter(moves)


def castle_short_m(pos: Position) -> list[Move]:
    return [Move((pos[0], pos[1] + 2), Flag.CASTLE_SHORT)]


def castle_long_m(pos: Position) -> list[Move]:
    return [Move((pos[0], pos[1] - 2), Flag.CASTLE_LONG)]


def pincer_m(pos: Position, dir: int) -> list[Move]:
    L = Move((pos[0] + dir, pos[1] + 1))
    R = Move((pos[0] + dir, pos[1] - 1))
    return in_bounds_filter([L, R])


def enpassant_m(pos: Position, dir: int) -> list[Move]:
    L = Move((pos[0] + dir, pos[1] + 1), Flag.ENPASSANT)
    R = Move((pos[0] + dir, pos[1] - 1), Flag.ENPASSANT)
    return in_bounds_filter([L, R])


def front_short_m(pos: Position, dir: int) -> list[Move]:
    return [Move((pos[0] + dir, pos[1]))]


def front_long_m(pos: Position, dir: int) -> list[Move]:
    return [Move((pos[0] + 2 * dir, pos[1]), Flag.ENPASSANT_TRGT)]


def get_moves_empty(*args, **kwargs) -> list[Move]:
    return []


def get_moves_pawn(
    board: Board, pos: Position, color: Color, enpassant_target: Position | None
) -> list[Move]:
    """Priority: Empassat, Pincer, Long, Short"""
    dir = color.dir

    enpassant = [
        move
        for move in enpassant_m(pos, dir)
        if enpassant_valid(pos, move, enpassant_target)
    ]

    pincer = [move for move in pincer_m(pos, dir) if pincer_valid(board, pos, move)]

    front_long = [
        move
        for move in front_long_m(pos, dir)
        if front_long_valid(board, pos, move, color)
    ]

    front_short = [
        move for move in front_short_m(pos, dir) if front_short_valid(board, move)
    ]
    all_moves = enpassant + pincer + front_long + front_short
    return final_checks_filter(all_moves, board, pos, color, enpassant_target)


def get_moves_rook(board: Board, pos: Position, color: Color) -> list[Move]:
    all_moves = perp_m(pos)
    for move in all_moves:
        move.flag = Flag.LOSE_ROOK_PRIV
    return final_checks_filter(all_moves, board, pos, color)


def get_moves_knight(board: Board, pos: Position, color: Color) -> list[Move]:
    all_moves = lshapes_m(pos)
    return final_checks_filter(all_moves, board, pos, color)


def get_moves_bishop(board: Board, pos: Position, color: Color) -> list[Move]:
    all_moves = diag_m(pos)
    return final_checks_filter(all_moves, board, pos, color)


def get_moves_queen(board: Board, pos: Position, color: Color) -> list[Move]:
    all_moves = diag_m(pos) + perp_m(pos)
    return final_checks_filter(all_moves, board, pos, color)


def get_moves_king(
    board: Board, pos: Position, color: Color, castling_flags: CastlingFlags
) -> list[Move]:
    castle_short = [
        move
        for move in castle_short_m(pos)
        if castle_short_valid(board, color, castling_flags)
    ]
    castle_long = [
        move
        for move in castle_long_m(pos)
        if castle_long_valid(board, color, castling_flags)
    ]

    normal_moves = diag_m(pos, 1) + perp_m(pos, 1)

    for move in normal_moves:
        move.flag = Flag.LOSE_KING_PRIV

    all_moves = normal_moves + castle_long + castle_short
    return [move for move in all_moves if final_checks(board, pos, move, color)]


EMPTY_BOARD: dict[Position, Piece] = {
    pos: Empty() for pos in product(range(8), range(8))
}


INITIAL_CASTING_FLAGS: CastlingFlags = {
    Color.WHITE: [True, True],
    Color.BLACK: [True, True],
}


class Board(UserDict):
    def __init__(self):
        self.data: dict[Position, Piece] = EMPTY_BOARD
        self.color_to_move: Color = Color.WHITE
        self.enpassant_target: Position | None = None
        self.castling_flags: CastlingFlags = INITIAL_CASTING_FLAGS

    @classmethod
    def from_fen(cls, fen_string: str = Setup.START) -> Self:
        board_configuration = fen_string.replace("/", "").split(" ")[0]

        for digit in "12345678":
            board_configuration = board_configuration.replace(digit, " " * int(digit))

        board = cls()

        for i, p in enumerate(board_configuration):
            if p.isspace():
                continue
            color, PieceType = FEN_MAP[p]
            row, col = divmod(i, 8)
            board[row, col] = PieceType(color)
        return board

    def checked(self, color: Color) -> bool:
        king_pos = self.king_pos(color)
        return not kingcheck_safe(self, king_pos, color)

    def king_pos(self, color: Color) -> Position:
        return next(
            pos
            for pos, piece in self.items()
            if piece.color == color and type(piece) == King
        )

    def toggle_color_turn(self) -> None:
        self.color_to_move = self.color_to_move.other

    def checkmated(self) -> bool:
        color = self.color_to_move
        return not self.all_moves and self.checked(color)

    def stalemated(self) -> bool:
        color = self.color_to_move
        return not self.all_moves and not self.checked(color)

    @property
    def all_moves(self) -> dict[Position, list[Move]]:
        color = self.color_to_move

        all_moves = {}
        for pos, piece in self.items():
            if piece.color != color:
                continue
            if moves := piece.get_moves(
                self,
                pos,
                enpassant_target=self.enpassant_target,
                castling_flags=self.castling_flags,
            ):
                all_moves[pos] = moves
        return all_moves

    def __delitem__(self, pos: Position) -> None:
        self.data[pos] = Empty()

    def single_move(self, frm: Position, to: Position) -> None:
        self.data[to] = self.data[frm]
        self.data[frm] = Empty()
