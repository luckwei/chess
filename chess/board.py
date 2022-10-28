from __future__ import annotations

from ast import Try
from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from enum import IntEnum, auto
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
    castling_flags: _Flags = field(init=False, default_factory=castling_flags_initial)

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

    def __delitem__(self, pos: Position|None) -> None:
        if pos is None:
            return
        self[pos] = Piece()


class Flag(IntEnum):
    NONE = auto()
    ENPASSANT_TRGT = auto()
    ENPASSANT = auto()
    CASTLING = auto()


@dataclass
class Move:
    frm: Position
    to: Position
    flag: Flag = Flag.NONE

    @classmethod
    def diag(cls, frm: Position, n=7) -> list[Self]:
        moves = []
        for i in range(1, n + 1):
            NE = cls(frm, (frm[0] + i, frm[1] + i))
            NW = cls(frm, (frm[0] + i, frm[1] - i))
            SE = cls(frm, (frm[0] - i, frm[1] + i))
            SW = cls(frm, (frm[0] - i, frm[1] - i))
            moves.extend([NE, NW, SE, SW])
        return moves

    @classmethod
    def perp(cls, frm: Position, n=7) -> list[Self]:
        moves = []
        for i in range(1, n + 1):
            N = cls(frm, (frm[0] + i, frm[1]))
            S = cls(frm, (frm[0] - i, frm[1]))
            E = cls(frm, (frm[0], frm[1] + i))
            W = cls(frm, (frm[0], frm[1] - i))
            moves.extend([N, S, E, W])
        return moves

    @classmethod
    def lshapes(cls, frm: Position) -> list[Self]:
        moves = []
        for quadrant in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            for magnitude in [(1, 2), (2, 1)]:
                x, y = np.multiply(quadrant, magnitude)
                moves.append(cls(frm, (frm[0] + x, frm[1] + y)))
        return moves
    
    @classmethod
    def castle_short(cls, frm: Position, dir: int) -> list[Self]:
        # SHORT = cls(frm, (frm))
        # LONG = cls(frm, (frm[0]))
        ...
    @classmethod
    def castle_long(cls, frm: Position, dir: int) -> list[Self]:
        ...

    @classmethod
    def pincer(cls, frm: Position, dir: int) -> list[Self]:
        L = cls(frm, (frm[0] + dir, frm[1] + 1))
        R = cls(frm, (frm[0] + dir, frm[1] - 1))
        return [L, R]

    @classmethod
    def enpassant(cls, frm: Position, dir: int) -> list[Self]:
        L = cls(frm, (frm[0] + dir, frm[1] + 1), Flag.ENPASSANT)
        R = cls(frm, (frm[0] + dir, frm[1] - 1), Flag.ENPASSANT)
        return [L, R]

    @classmethod
    def front_short(cls, frm: Position, dir: int) -> list[Self]:
        return [cls(frm, (frm[0] + dir, frm[1]))]

    @classmethod
    def front_long(cls, frm: Position, dir: int) -> list[Self]:
        return [cls(frm, (frm[0] + 2 * dir, frm[1]), Flag.ENPASSANT_TRGT)]
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
    all_moves = enpassant + pincer + front_long + front_short
    return all_moves


def get_moves_rook(board: Board, pos: Position) -> list[Move]:
    return [move for move in Move.perp(pos) if Checks.final(board, move)]


def get_moves_knight(board: Board, pos: Position) -> list[Move]:
    return [move for move in Move.lshapes(pos) if Checks.final(board, move)]


def get_moves_bishop(board: Board, pos: Position) -> list[Move]:
    return [move for move in Move.diag(pos) if Checks.final(board, move)]


def get_moves_queen(board: Board, pos: Position) -> list[Move]:
    all_moves = Move.diag(pos) + Move.perp(pos)
    return [move for move in all_moves if Checks.final(board, move)]


def get_moves_king(board: Board, pos: Position) -> list[Move]:
    all_moves = Move.diag(pos, 1) + Move.perp(pos, 1)
    return [move for move in all_moves if Checks.final(board, move)]


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
        frm, to = move.frm, move.to
        enemy_pawn = (frm[0], to[1])
        return board.enpassant_target == enemy_pawn

    @staticmethod
    def pincer_valid(board: Board, move: Move) -> bool:
        frm, to = move.frm, move.to
        if not board[to]:
            return False
        if board[move.to].color != board[frm].color:
            return True
        return False

    @staticmethod
    def front_long_valid(board: Board, move: Move) -> bool:
        frm, to = move.frm, move.to
        color_turn = board.color_turn
        
        starting_rank = frm[0] == (6 if color_turn == PieceColor.WHITE else 1)
        to_is_empty = not board[to]
        return starting_rank and to_is_empty

    @staticmethod
    def front_short_valid(board: Board, move: Move) -> bool:
        to = move.to
        to_piece = board[to]
        
        return to_piece.type == PieceType.EMPTY


class Checks:
    @staticmethod
    def to_pos_in_grid(move: Move) -> bool:
        to = move.to
        
        return max(to) <= 7 and min(to) >= 0

    @staticmethod
    def is_color_turn(board: Board, move: Move) -> bool:
        frm = move.frm
        color_turn = board.color_turn
        piece = board[frm]

        return color_turn == piece.color

    @staticmethod
    def to_empty_or_enemy(board: Board, move: Move) -> bool:
        to = move.to
        color_turn = board.color_turn
        to_piece = board[to]
        
        return to_piece.color != color_turn or to_piece.color == PieceColor.NONE

    @staticmethod
    def no_obstruction(board: Board, move: Move) -> bool:
        frm, to = move.frm, move.to
        frm_x, frm_y = frm
        to_x, to_y = to
        

        X = range(frm_x, to_x, 1 if to_x > frm_x else -1)
        Y = range(frm_y, to_y, 1 if to_y > frm_y else -1)

        # short moves and knights have no obstruction
        if min(len(X), len(Y)) == 1:
            return True

        # If both exist, diag move
        if X and Y:
            obstructions = [1 for pos in zip(X, Y) if pos != frm and board[pos]]

        # If x exists, perp col, same column
        elif X:
            obstructions = [1 for x in X if (x, frm_y) != frm and board[x, frm_y]]

        # Else y exists, perp col, same row
        else:
            obstructions = [1 for y in Y if (frm_x, y) != frm and board[frm_x, y]]

        return not obstructions

    # TODO: decoupling
    @staticmethod
    def king_safe_at_end(board: Board, move: Move) -> bool:
        frm, to, flag = move.frm, move.to, move.flag
        enemy_color = board.enemy_color

        end_board = deepcopy(board)
        end_board[to] = end_board[frm]
        del end_board[frm]

        if flag == Flag.ENPASSANT:  # TODO be refactored
            del end_board[end_board.enpassant_target]

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
