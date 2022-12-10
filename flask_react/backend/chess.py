from __future__ import annotations

from abc import ABC, abstractmethod
from collections import UserDict
from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from enum import Enum, StrEnum, auto
from itertools import product
from random import choice
from typing import Any, Callable, Iterable, Self

import numpy as np


class Setup:
    START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def in_bounds(pos: str) -> bool:
    return max(pos_tup(pos)) <= 7 and min(pos_tup(pos)) >= 0


def add_pos(pos: str, other: str | tuple[int, int]) -> str:
    pos_row, pos_col = pos_tup(pos)
    other_row, other_col = pos_tup(other) if isinstance(other, str) else other

    return pos_str(pos_row + other_row, pos_col + other_col)


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

    @property
    def pawn_rank(self) -> int:
        return {Color.WHITE: 6, Color.BLACK: 1}.get(self, -1)


def pos_str(row: int, col: int) -> str:
    return f"{row},{col}"


def pos_tup(pos_str: str) -> tuple[int, int]:
    return tuple(int(coord) for coord in pos_str.split(","))


# Chess Pieces and its subclasses
@dataclass(slots=True, eq=True)
class Piece(ABC):
    color: Color
    type: str

    @abstractmethod
    def moves(self, board: Board, pos: str) -> list[Move]:
        ...

@dataclass
class Empty(Piece):
    color: Color = Color.NONE
    type: str = "none"

    def __bool__(self):
        return False

    def moves(self, *_: Any) -> list[Move]:
        return []

@dataclass
class Pawn(Piece):
    type: str = "pawn"
    def moves(self, board: Board, frm: str) -> list[Move]:
        possible_moves: list[Move] = []

        frm_row, frm_col = pos_tup(frm)

        color = self.color
        dir = color.dir
        enpassant_target = board.enpassant_target
        enemy_br = color.other.back_rank

        for side in [1, -1]:
            to = add_pos(frm, (dir, side))
            to_row, to_col = pos_tup(to)
            # Enpassant
            if enpassant_target and enpassant_target == (frm_row, to_col):
                possible_moves.append(
                    Move(self, frm, to, enpassant_capture=enpassant_target)
                )

            # Capture/Promotion
            if in_bounds(to) and board[to].color == color.other:
                possible_moves.append(Move(self, frm, to, promote=to_row == enemy_br))

        # Front long
        front_long = add_pos(frm, (2 * dir, 0))
        if frm_row == color.pawn_rank and not board[front_long]:
            possible_moves.append(
                Move(self, frm, front_long, enpassant_target=enpassant_target)
            )

        # Front short/Promotion
        front_short = add_pos(frm, (dir, 0))
        if not board[front_short]:
            possible_moves.append(
                Move(
                    self, frm, front_short, promote=pos_tup(front_short)[0] == enemy_br
                )
            )

        return [move for move in possible_moves if final_checks(board, move)]

@dataclass
class Rook(Piece):
    type: str = "rook"
    def moves(self, board: Board, frm: str) -> list[Move]:
        return [
            move
            for to in perpendicular_moves(frm)
            if final_checks(
                board,
                move := Move(self, frm, to, castling_flag=CastlingFlag.ROOK_MOVED),
            )
        ]

@dataclass
class Knight(Piece):
    type: str = "knight"
    def moves(self, board: Board, frm: str) -> list[Move]:
        return [
            move
            for to in l_shaped_moves(frm)
            if final_checks(board, move := Move(self, frm, to))
        ]

@dataclass
class Bishop(Piece):
    type:str="bishop"
    def moves(self, board: Board, frm: str) -> list[Move]:
        return [
            move
            for to in diagonal_moves(frm)
            if final_checks(board, move := Move(self, frm, to))
        ]

@dataclass
class Queen(Piece):
    type: str="queen"
    def moves(self, board: Board, frm: str) -> list[Move]:
        return [
            move
            for to in [*diagonal_moves(frm), *perpendicular_moves(frm)]
            if final_checks(board, move := Move(self, frm, to))
        ]

@dataclass
class King(Piece):
    type: str = "king"
    def moves(self, board: Board, frm: str) -> list[Move]:
        color = self.color
        back_rank = color.back_rank
        castling_perm = board.castling_perm

        possible_moves: list[Move] = []

        king_not_checked = not board.checked

        # King-side castle
        if (
            castling_perm[color, CastlingFlag.KING_SIDE]
            and king_not_checked
            and kingcheck_safe(board, pos_str(back_rank, 5))
            and not any(board[pos_str(back_rank, col)] for col in [5, 6])
        ):
            possible_moves.append(
                Move(
                    self,
                    frm,
                    add_pos(frm, (0, 2)),
                    castling_flag=CastlingFlag.KING_SIDE,
                )
            )

        # Queen-side castle
        if (
            castling_perm[color, CastlingFlag.QUEEN_SIDE]
            and king_not_checked
            and kingcheck_safe(board, pos_str(back_rank, 3))
            and not any(board[pos_str(back_rank, col)] for col in [1, 2, 3])
        ):
            possible_moves.append(
                Move(
                    self,
                    frm,
                    add_pos(frm, (0, -2)),
                    castling_flag=CastlingFlag.QUEEN_SIDE,
                )
            )

        # Normal moves
        possible_moves.extend(
            Move(self, frm, to, castling_flag=CastlingFlag.KING_MOVED)
            for to in [*diagonal_moves(frm, 1), *perpendicular_moves(frm, 1)]
        )
        return [move for move in possible_moves if final_checks(board, move)]


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


class CastlingFlag(Enum):
    QUEEN_SIDE = auto()
    KING_SIDE = auto()
    KING_MOVED = auto()
    ROOK_MOVED = auto()


class CastlingPerm(UserDict[tuple[Color, CastlingFlag], bool]):
    __slots__ = ("data",)
    FEN_CASTLING = {
        (Color.WHITE, CastlingFlag.KING_SIDE): "K",
        (Color.WHITE, CastlingFlag.QUEEN_SIDE): "Q",
        (Color.BLACK, CastlingFlag.KING_SIDE): "k",
        (Color.BLACK, CastlingFlag.QUEEN_SIDE): "q",
    }

    def __init__(self, fen_substring: str = "KQkq") -> None:
        self.data = {
            color_side: i in fen_substring
            for color_side, i in self.FEN_CASTLING.items()
        }

    def remove(
        self, color: Color, flag: CastlingFlag = CastlingFlag.KING_MOVED
    ) -> None:
        if flag == CastlingFlag.KING_MOVED:
            self[color, CastlingFlag.QUEEN_SIDE] = False
            self[color, CastlingFlag.KING_SIDE] = False
            return
        self[color, flag] = False


def kingcheck_safe(board: Board, pos: str, color: Color | None = None) -> bool:
    if color is None:
        color = board.color_move
    enemy_color = color.other

    if any(board[m] == Knight(enemy_color) for m in l_shaped_moves(pos)):
        return False

    # check perpendiculars
    if any(
        board[m] in (Queen(enemy_color), Rook(enemy_color))
        and not obstruction(board, pos, m)
        for m in perpendicular_moves(pos)
    ):
        return False

    # check diagonals
    if any(
        board[m] in (Queen(enemy_color), Bishop(enemy_color))
        and not obstruction(board, pos, m)
        for m in diagonal_moves(pos)
    ):
        return False

    # check adjacent for king
    if any(
        board[m] == King(enemy_color)
        for m in [*perpendicular_moves(pos, 1), *diagonal_moves(pos, 1)]
    ):
        return False

    # check pincer for pawn
    return not any(
        in_bounds(m := add_pos(pos, (color.dir, side)))
        and board[m] == Pawn(enemy_color)
        for side in [1, -1]
    )


@dataclass
class Move:
    updates: dict[str, Piece] = field(init=False, default_factory=dict)
    piece: Piece
    frm: str
    to: str
    enpassant_capture: str | None = None
    enpassant_target: str | None = None
    castling_flag: CastlingFlag | None = None
    promote: InitVar[bool] = False

    def __post_init__(self, promote):
        updates = self.updates
        frm, to = self.frm, self.to
        piece = self.piece
        color = piece.color
        enpassant_capture = self.enpassant_capture
        back_rank = color.back_rank

        updates[frm] = Empty()
        updates[to] = Queen(color) if promote else piece

        if enpassant_capture:
            updates[enpassant_capture] = Empty()

        if self.castling_flag == CastlingFlag.QUEEN_SIDE:
            self.updates[pos_str(back_rank, 3)] = Rook(color)
            self.updates[pos_str(back_rank, 0)] = Empty()

        elif self.castling_flag == CastlingFlag.KING_SIDE:
            self.updates[pos_str(back_rank, 5)] = Rook(color)
            self.updates[pos_str(back_rank, 7)] = Empty()


def obstruction(board: Board, frm: str, to: str) -> bool:
    # return False
    frm_row, frm_col = pos_tup(frm)
    to_row, to_col = pos_tup(to)
    ROWS = range(frm_row, to_row, 1 if to_row > frm_row else -1)
    COLS = range(frm_col, to_col, 1 if to_col > frm_col else -1)

    # short moves and knights have no obstruction
    if min(len(ROWS), len(COLS)) == 1:
        return False

    # If both exist, diag move
    if ROWS and COLS:
        return any(
            pos_str(row, col) != frm and board[pos_str(row, col)]
            for row, col in zip(ROWS, COLS)
        )

    # If x exists, perp col, same column
    if ROWS:
        return any(
            pos_str(row, frm_col) != frm and board[pos_str(row, frm_col)]
            for row in ROWS
        )
        
    

    # Else y exists, perp col, same row
    return any(
        pos_str(frm_row, col) != frm and board[pos_str(frm_row, col)] for col in COLS
    )


def final_checks(
    board: Board,
    move: Move,
) -> bool:
    frm, to = move.frm, move.to
    # Rejection criterias:
    # Not in bounds
    # From pos is not color
    # To pos is own color
    # Move has obstruction
    if (
        not in_bounds(to)
        or board[frm].color != board.color_move
        or board[to].color == board.color_move
        or obstruction(board, frm, to)
    ):
        return False

    # simulate move and check if king safe
    end_game = deepcopy(board)
    end_game.update_from_move(move)

    return not end_game.checked


def diagonal_moves(pos: str, distance=7) -> Iterable[str]:
    quadrants = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    magnitude = zip((mag := range(1, distance + 1)), mag)
    deltas = (
        tuple(np.multiply(quadrant, magnitude))
        for quadrant, magnitude in product(quadrants, magnitude)
    )

    return (to for delta in deltas if in_bounds(to := add_pos(pos, delta)))


def perpendicular_moves(pos: str, distance=7) -> Iterable[str]:
    sides = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    magnitude = zip((mag := range(1, distance + 1)), mag)
    deltas = (
        tuple(np.multiply(side, magnitude))
        for side, magnitude in product(sides, magnitude)
    )

    return (to for delta in deltas if in_bounds(to := add_pos(pos, delta)))


def l_shaped_moves(pos: str) -> Iterable[str]:
    quadrants = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    magnitude = [(1, 2), (2, 1)]
    deltas = (
        tuple(np.multiply(quadrant, magnitude))
        for quadrant, magnitude in product(quadrants, magnitude)
    )

    return (to for delta in deltas if in_bounds(to := add_pos(pos, delta)))


@dataclass(slots=True)
class Board(UserDict[str, Piece]):
    fen_string: InitVar[str | None] = Setup.START

    color_move: Color = field(init=False)
    castling_perm: CastlingPerm = field(init=False)
    enpassant_target: str | None = field(init=False)
    all_moves_cache: dict[str, list[Move]] = field(init=False)

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
            self.enpassant_target = None
        else:
            col, row = enpassant_trgt
            self.enpassant_target = pos_str(8 - int(row), "abcdefgh".index(col))

        for i in "12345678":
            board_config = board_config.replace(i, " " * int(i))

        self.data = {
            pos_str(*divmod(i, 8)): FEN_MAP[p] for i, p in enumerate(board_config)
        }
        self.recompute_all_moves()

    def find_king(self, color: Color | None = None) -> str:
        if color is None:
            color = self.color_move
        return next(
            pos
            for pos, piece in self.items()
            if piece.color == color and isinstance(piece, King)
        )

    @property
    def checked(self) -> bool:
        return not kingcheck_safe(
            self, self.find_king(self.color_move), self.color_move
        )

    @property
    def checkmated(self) -> bool:
        return not self.all_moves_cache and self.checked

    @property
    def stalemated(self, color: Color | None = None) -> bool:
        return not self.all_moves_cache and not self.checked

    def recompute_all_moves(self, color: Color | None = None) -> None:
        color = self.color_move if color is None else color

        self.all_moves_cache = {
            pos: moves
            for pos, piece in self.items()
            if piece.color == color and (moves := piece.moves(self, pos))
        }

    def update_from_move(self, move: Move) -> None:
        for pos, piece in move.updates.items():
            self[pos] = piece

    def execute_move(self, move: Move) -> None:
        color = self.color_move
        castling_perm = self.castling_perm
        back_rank = color.back_rank
        castling_flag = move.castling_flag

        self.update_from_move(move)

        if castling_flag == CastlingFlag.QUEEN_SIDE:
            castling_perm.remove(color, castling_flag)

        if castling_flag == CastlingFlag.KING_SIDE:
            castling_perm.remove(color, castling_flag)

        if castling_flag == CastlingFlag.KING_MOVED:
            castling_perm.remove(color)

        if castling_flag == CastlingFlag.ROOK_MOVED:
            castling_perm.remove(
                color,
                CastlingFlag.QUEEN_SIDE
                if move.frm == pos_str(back_rank, 0)
                else CastlingFlag.KING_SIDE,
            )

        self.enpassant_target = move.enpassant_target
        self.color_move = self.color_move.other
        self.recompute_all_moves()
