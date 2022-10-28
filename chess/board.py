from __future__ import annotations

from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from itertools import product
from math import dist
from os import stat
from typing import Callable, Self

import numpy as np
from tksvg import SvgImage

from .piece import FEN_MAP, Piece, PieceColor, PieceType
from .setup import Setup
from .types import Position

_Grid = dict[Position, Piece]
_Flags = dict[PieceColor, tuple[bool, bool]]


def empty_board() -> _Grid:
    return {pos: Piece() for pos in product(range(8), range(8))}

def castling_flags_initial() -> _Flags:
    return {
        PieceColor.WHITE: (True, True),
        PieceColor.BLACK: (True, True),
    }
    

@dataclass
class Board:
    fen: InitVar[str] = Setup.START
    color_turn: PieceColor = field(init=False, default=PieceColor.WHITE)
    enpassant_target: Position | None = field(init=False, default=None)
    pieces: _Grid = field(init=False, default_factory=empty_board)
    move_counter: int = field(init=False, default=0)
    castling_flags:  _Flags= field(init=False, default_factory=castling_flags_initial)

    def __post_init__(self, fen):
        config, color_turn, *_ = fen.replace("/", "").split(" ")

        self.color_turn = PieceColor.WHITE if color_turn == "w" else PieceColor.BLACK

        for digit in "12345678":
            config = config.replace(digit, " " * int(digit))

        for i, p in enumerate(config):
            if p != " ":
                self[divmod(i, 8)] = Piece(*FEN_MAP[p])

    def __iter__(self):
        return iter(self.pieces.items())

    @property
    def dir(self) -> int:
        return -1 if self.color_turn == PieceColor.WHITE else 1

    @property
    def enemy_color(self) -> PieceColor:
        return (
            PieceColor.WHITE
            if self.color_turn == PieceColor.BLACK
            else PieceColor.BLACK
        )

    def toggle_color_turn(self) -> None:
        self.color_turn = self.enemy_color

    @property
    def king_pos(self) -> Position:
        return next(
            (
                pos
                for pos, piece in self
                if piece == Piece(self.color_turn, PieceType.KING)
            )
        )

    @property
    def other_king(self) -> Position:
        return next(
            (
                pos
                for pos, piece in self
                if piece == Piece(self.enemy_color, PieceType.KING)
            )
        )

    def get_valid_moves(self, pos: Position) -> list[Move]:
        return MOVE_CALCULATORS[self[pos].type](self, pos)

    def __str__(self) -> str:
        pieces_str = [str(piece) for piece in self.pieces.values()]
        rows = ["".join(pieces_str[i : i + 8]) for i in range(0, 64, 8)]
        return "\n".join(rows)

    def __getitem__(self, pos: Position) -> Piece:
        return self.pieces[pos]

    def __setitem__(self, pos: Position, piece):
        self.pieces[pos] = piece

    def __delitem__(self, pos: Position) -> None:
        self[pos] = Piece()


@dataclass
class Move:
    # board: Board
    frm: Position
    to: Position
    extra_capture: Position | None = None
    enpassant_trgt: Position | None = None

    @property
    def dist(self) -> float:
        return dist(self.frm, self.to)

    @classmethod
    def diag(cls, frm: Position, n=7) -> list[Self]:
        row, col = frm
        moves = []
        for i in range(1, n + 1):
            NE = cls(frm, to=(row + i, col + i))
            NW = cls(frm, to=(row + i, col - i))
            SE = cls(frm, to=(row - i, col + i))
            SW = cls(frm, to=(row - i, col - i))
            moves.extend([NE, NW, SE, SW])

        return moves

    @classmethod
    def perp(cls, frm: Position, n=7) -> list[Self]:
        row, col = frm
        moves = []
        for i in range(1, n + 1):
            N = cls(frm, to=(row + i, col))
            S = cls(frm, to=(row - i, col))
            E = cls(frm, to=(row, col + i))
            W = cls(frm, to=(row, col - i))
            moves.extend([N, S, E, W])

        return moves

    @classmethod
    def lshapes(cls, frm: Position) -> list[Self]:
        row, col = frm

        moves = []
        for quadrant in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            for magnitude in [(1, 2), (2, 1)]:
                x, y = np.multiply(quadrant, magnitude)

                moves.append(cls(frm, to=(row + x, col + y)))
        return moves

    @classmethod
    def pincer(cls, frm: Position, dir: int) -> list[Self]:
        row, col = frm

        L = cls(frm, to=(row + dir, col + 1))
        R = cls(frm, to=(row + dir, col - 1))

        return [L, R]

    @classmethod
    def enpassant(cls, frm: Position, dir: int) -> list[Self]:
        row, col = frm
        L = cls(frm, to=(row + dir, col + 1), extra_capture=(row, col + 1))
        R = cls(frm, to=(row + dir, col - 1), extra_capture=(row, col - 1))

        return [L, R]

    @classmethod
    def front_short(cls, frm: Position, dir: int) -> list[Self]:
        row, col = frm

        return [cls(frm, to=(row + dir, col))]

    @classmethod
    def front_long(cls, frm: Position, dir: int) -> list[Self]:
        row, col = frm

        return [
            cls(
                frm,
                to := (row + 2 * dir, col),
                enpassant_trgt=to,
            )
        ]

        # TODO: Dont allow move if mouse release was away from tile


def get_moves_empty(*args, **kwargs) -> list[Move]:
    return []


def get_moves_pawn(board: Board, pos: Position) -> list[Move]:
    """Priority: Empassat, Pincer, Long, Short"""
    dir = board[pos].dir

    enpassant = [
        move
        for move in Move.enpassant(pos, dir)
        if Checks.final(board, move) and PawnCheck.enpassant_valid(board, move)
    ]

    pincer = [
        move
        for move in Move.pincer(pos, dir)
        if Checks.final(board, move) and PawnCheck.pincer_valid(board, move)
    ]

    front_long = [
        move
        for move in Move.front_long(pos, dir)
        if Checks.final(board, move) and PawnCheck.front_long_valid(board, move)
    ]

    front_short = [
        move
        for move in Move.front_short(pos, dir)
        if Checks.final(board, move) and PawnCheck.front_short_valid(board, move)
    ]
    capture_moves = enpassant + pincer
    all_moves = enpassant + pincer + front_long + front_short
    return all_moves
    return capture_moves if capture_moves else all_moves


def get_moves_rook(board: Board, pos: Position) -> list[Move]:

    valid_moves = [move for move in Move.perp(pos) if Checks.final(board, move)]
    capture_moves = [move for move in valid_moves if board[move.to]]
    return valid_moves
    return capture_moves if capture_moves else valid_moves


def get_moves_knight(board: Board, pos: Position) -> list[Move]:

    valid_moves = [move for move in Move.lshapes(pos) if Checks.final(board, move)]
    capture_moves = [move for move in valid_moves if board[move.to]]
    return valid_moves

    return capture_moves if capture_moves else valid_moves


def get_moves_bishop(board: Board, pos: Position) -> list[Move]:

    valid_moves = [move for move in Move.diag(pos) if Checks.final(board, move)]
    capture_moves = [move for move in valid_moves if board[move.to]]
    return valid_moves

    return capture_moves if capture_moves else valid_moves


def get_moves_queen(board: Board, pos: Position) -> list[Move]:

    all_moves = Move.diag(pos) + Move.perp(pos)
    valid_moves = [move for move in all_moves if Checks.final(board, move)]
    capture_moves = [move for move in valid_moves if board[move.to]]
    return valid_moves

    return capture_moves if capture_moves else valid_moves


def get_moves_king(board: Board, pos: Position) -> list[Move]:

    all_moves = Move.diag(pos, 1) + Move.perp(pos, 1)
    valid_moves = [move for move in all_moves if Checks.final(board, move)]
    capture_moves = [move for move in valid_moves if board[move.to]]
    return valid_moves
    return capture_moves if capture_moves else valid_moves


ValidMoveCalculator = Callable[[Board, Position], list[Move]]

MOVE_CALCULATORS: dict[PieceType, ValidMoveCalculator] = {
    PieceType.EMPTY: get_moves_empty,
    PieceType.ROOK: get_moves_rook,
    PieceType.BISHOP: get_moves_bishop,
    PieceType.KNIGHT: get_moves_knight,
    PieceType.QUEEN: get_moves_queen,
    PieceType.KING: get_moves_king,
    PieceType.PAWN: get_moves_pawn,
}


class PawnCheck:
    @staticmethod
    def enpassant_valid(board: Board, move: Move) -> bool:
        return board.enpassant_target == move.extra_capture

    @staticmethod
    def pincer_valid(board: Board, move: Move) -> bool:
        if not board[move.to]:
            return False
        if board[move.to].color != board[move.frm].color:
            return True
        return False

    @staticmethod
    def front_long_valid(board: Board, move: Move) -> bool:

        starting_rank = move.frm[0] == (
            6 if board.color_turn == PieceColor.WHITE else 1
        )
        to_is_empty = not board[move.to]
        return starting_rank and to_is_empty

    @staticmethod
    def front_short_valid(board: Board, move: Move) -> bool:
        to_is_empty = not board[move.to]
        return to_is_empty


class Checks:
    @staticmethod
    def to_pos_in_grid(move: Move) -> bool:
        return max(move.to) <= 7 and min(move.to) >= 0

    @staticmethod
    def is_color_turn(board: Board, move: Move) -> bool:
        return board.color_turn == board[move.frm].color

    @staticmethod
    def to_empty_or_enemy(board: Board, move: Move) -> bool:
        return board[move.to].color != board.color_turn

    @staticmethod
    def no_obstruction(board: Board, move: Move) -> bool:
        xfrm, yfrm = move.frm
        xto, yto = move.to

        X = range(xfrm, xto, 1 if xto > xfrm else -1)
        Y = range(yfrm, yto, 1 if yto > yfrm else -1)

        # short moves and knights have no obstruction
        if min(len(X), len(Y)) == 1:
            return True

        # If both exist, diag move
        if X and Y:
            obstructions = [1 for pos in zip(X, Y) if pos != move.frm and board[pos]]

        # If x exists, perp col, same column
        elif X:
            obstructions = [1 for x in X if (x, yfrm) != move.frm and board[x, yfrm]]

        # Else y exists, perp col, same row
        else:
            obstructions = [1 for y in Y if (xfrm, y) != move.frm and board[xfrm, y]]

        return not obstructions

    @staticmethod
    def king_safe_at_end(board: Board, move: Move) -> bool:
        # return True
        enemy_color = board.enemy_color

        end_board = deepcopy(board)

        end_board[move.to] = end_board[move.frm]
        del end_board[move.frm]

        if move.extra_capture:
            del end_board[move.extra_capture]

        # check knights on L
        enemy_knight = [
            1
            for move in Move.lshapes(end_board.king_pos)
            if Checks.to_pos_in_grid(move)
            and end_board[move.to] == Piece(enemy_color, PieceType.KNIGHT)
        ]

        # check perpendiculars
        enemy_rook_queen = [
            1
            for move in Move.perp(end_board.king_pos)
            if Checks.to_pos_in_grid(move)
            and end_board[move.to]
            in (Piece(enemy_color, PieceType.ROOK), Piece(enemy_color, PieceType.QUEEN))
            and Checks.no_obstruction(end_board, move)
        ]

        # check diagonals
        enemy_bishop_queen = [
            1
            for move in Move.diag(end_board.king_pos)
            if Checks.to_pos_in_grid(move)
            and end_board[move.to]
            in (
                Piece(enemy_color, PieceType.BISHOP),
                Piece(enemy_color, PieceType.QUEEN),
            )
            and Checks.no_obstruction(end_board, move)
        ]

        # check adjacent for king
        enemy_king = [
            1
            for move in Move.perp(end_board.king_pos, 1)
            + Move.diag(end_board.king_pos, 1)
            if Checks.to_pos_in_grid(move) and move.to == end_board.other_king
        ]

        # check pincer for pawn
        enemy_pawn = [
            1
            for move in Move.pincer(end_board.king_pos, board.dir)
            if Checks.to_pos_in_grid(move)
            and end_board[move.to] == Piece(enemy_color, PieceType.PAWN)
        ]

        all_enemies = (
            enemy_knight
            + enemy_rook_queen
            + enemy_bishop_queen
            + enemy_king
            + enemy_pawn
        )

        return not all_enemies

    @staticmethod
    def final(board: Board, move: Move) -> bool:
        return (
            Checks.to_pos_in_grid(move)
            and Checks.is_color_turn(board, move)
            and Checks.to_empty_or_enemy(board, move)
            and Checks.no_obstruction(board, move)
            and Checks.king_safe_at_end(board, move)
        )
