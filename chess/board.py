from __future__ import annotations

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


def empty_board() -> _Grid:
    return {pos: Piece() for pos in product(range(8), range(8))}


@dataclass
class Board:
    fen: InitVar[str] = Setup.START
    pieces: _Grid = field(init=False, default_factory=empty_board)
    color_turn: PieceColor = field(init=False, default=PieceColor.WHITE)
    enpassant_target: Position | None = field(init=False, default=None)
    move_counter: int = field(init=False, default=0)
    # REcord down 50 move rule

    def __post_init__(self, fen):
        config, color_turn, *_ = fen.replace("/", "").split(" ")

        self.color_turn = PieceColor.WHITE if color_turn == "w" else PieceColor.BLACK

        for digit in "12345678":
            config = config.replace(digit, " " * int(digit))

        for i, p in enumerate(config):
            if p != " ":
                self[divmod(i, 8)] = Piece(*FEN_MAP[p])

    @property
    def other_color(self) -> PieceColor:
        return (
            PieceColor.WHITE
            if self.color_turn == PieceColor.BLACK
            else PieceColor.BLACK
        )

    def toggle_color_turn(self) -> None:
        self.color_turn = self.other_color

    @property
    def own_king(self) -> Piece | None:
        return next(
            (
                piece
                for piece in self.pieces.values()
                if piece == Piece(self.color_turn, PieceType.KING)
            ),
            None,
        )

    @property
    def other_king(self) -> Piece | None:
        return next(
            (
                piece
                for piece in self.pieces.values()
                if piece == Piece(self.other_color, PieceType.KING)
            ),
            None,
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
    _from: Position
    _to: Position
    _extra_capture: Position | None = None
    enpassant_target: Position | None = None

    @property
    def dist(self) -> float:
        return dist(self._from, self._to)

    # @property
    # def from_piece(self) -> Piece:
    #     return self.board[self._from]

    # @property
    # def to_piece(self) -> Piece:
    #     return self.board[self._to]

    # @property
    # def color_turn(self) -> PieceColor:
    #     return self.board.color_turn

    @classmethod
    def diag(cls, _from: Position, n=7) -> list[Self]:
        row, col = _from
        moves = []
        for i in range(1, n + 1):
            NE = cls(_from, _to=(row + i, col + i))
            NW = cls(_from, _to=(row + i, col - i))
            SE = cls(_from, _to=(row - i, col + i))
            SW = cls(_from, _to=(row - i, col - i))
            moves.extend([NE, NW, SE, SW])

        return moves

    @classmethod
    def perp(cls, _from: Position, n=7) -> list[Self]:
        row, col = _from
        moves = []
        for i in range(1, n + 1):
            N = cls(_from, _to=(row + i, col))
            S = cls(_from, _to=(row - i, col))
            E = cls(_from, _to=(row, col + i))
            W = cls(_from, _to=(row, col - i))
            moves.extend([N, S, E, W])

        return moves

    @classmethod
    def lshapes(cls, _from: Position) -> list[Self]:
        row, col = _from

        moves = []
        for quadrant in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            for magnitude in [(1, 2), (2, 1)]:
                x, y = np.multiply(quadrant, magnitude)

                moves.append(cls(_from, _to=(row + x, col + y)))
        return moves

    # MOVE DIR FROM PAWN MOVES
    @classmethod
    def pincer(cls, _from: Position, dir: int) -> list[Self]:
        row, col = _from

        L = cls(_from, _to=(row + dir, col + 1))
        R = cls(_from, _to=(row + dir, col - 1))

        return [L, R]

    @classmethod
    def enpassant(cls, _from: Position, dir: int) -> list[Self]:
        row, col = _from
        L = cls(_from, _to=(row + dir, col + 1), _extra_capture=(row, col + 1))
        R = cls(_from, _to=(row + dir, col - 1), _extra_capture=(row, col - 1))

        return [L, R]

    @classmethod
    def front_short(cls, _from: Position, dir: int) -> list[Self]:
        row, col = _from

        return [cls(_from, _to=(row + dir, col))]

    @classmethod
    def front_long(cls, _from: Position, dir: int) -> list[Self]:
        row, col = _from

        return [cls(
            _from,
            _to := (row + 2 * dir, col),
            enpassant_target=_to,
        )]


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
    return capture_moves if capture_moves else all_moves


# TODO: capture or kill lists
def get_moves_rook(board: Board, pos: Position) -> list[Move]:

    valid_moves = [move for move in Move.perp(pos) if Checks.final(board, move)]
    capture_moves = [move for move in valid_moves if board[move._to]]

    return capture_moves if capture_moves else valid_moves


def get_moves_knight(board: Board, pos: Position) -> list[Move]:

    valid_moves = [move for move in Move.lshapes(pos) if Checks.final(board, move)]
    capture_moves = [move for move in valid_moves if board[move._to]]

    return capture_moves if capture_moves else valid_moves


def get_moves_bishop(board: Board, pos: Position) -> list[Move]:

    valid_moves = [move for move in Move.diag(pos) if Checks.final(board, move)]
    capture_moves = [move for move in valid_moves if board[move._to]]

    return capture_moves if capture_moves else valid_moves


def get_moves_queen(board: Board, pos: Position) -> list[Move]:

    all_moves = Move.diag(pos) + Move.perp(pos)
    valid_moves = [move for move in all_moves if Checks.final(board, move)]
    capture_moves = [move for move in valid_moves if board[move._to]]

    return capture_moves if capture_moves else valid_moves


def get_moves_king(board: Board, pos: Position) -> list[Move]:

    all_moves = Move.diag(pos, 1) + Move.perp(pos, 1)
    valid_moves = [move for move in all_moves if Checks.final(board, move)]
    capture_moves = [move for move in valid_moves if board[move._to]]

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
        return board.enpassant_target == move._extra_capture

    @staticmethod
    def pincer_valid(board: Board, move: Move) -> bool:
        _from_piece = board[move._from]
        _to_piece = board[move._to]
        if not _to_piece:
            return False
        if _to_piece.color != _from_piece.color:
            return True
        #TODO: equality might be color instead of both color and piece
        return False

    @staticmethod
    def front_long_valid(board: Board, move: Move) -> bool:
        if board[move._from].color == PieceColor.WHITE:
            starting_rank = move._from[0] == 6
            no_obstruction = not board[(5, move._from[1])]
        else:
            starting_rank = move._from[0] == 1
            no_obstruction = not board[(2, move._from[1])]

        _to_empty = not board[move._to]
        return starting_rank and no_obstruction and _to_empty

    @staticmethod
    def front_short_valid(board: Board, move: Move) -> bool:
        _to_empty = not board[move._to]
        return _to_empty


class Checks:
    @staticmethod
    def is_color_turn(board: Board, move: Move) -> bool:
        return board.color_turn == board[move._from].color

    @staticmethod
    def to_pos_in_grid(board: Board, move: Move) -> bool:
        return max(move._to) <= 7 and min(move._to) >= 0

    @staticmethod
    def to_pos_empty_or_not_same_color(board: Board, move: Move) -> bool:
        return board[move._to].color != board.color_turn

    @staticmethod
    def king_not_checked_on_next_move(board: Board, move: Move) -> bool:
        # check for enemy fire in king's current psotion
        # check for enemy fire
        # bishops and queens on the diag, rook on the verts,
        # pawns on the near diags
        # knights on the Ls
        # TODO: King check
        king = board.own_king
        return True

    @staticmethod
    def no_obstruction(board: Board, move: Move) -> bool:
        x1, y1 = move._from
        x2, y2 = move._to

        # adjacent pieces and knights has no obstruction
        if (
            max(abs(x2 - x1), abs(y2 - y1)) == 1
            or board[move._from].type == PieceType.KNIGHT
        ):
            return True

        # perp move: same row
        if x1 == x2:
            for y in range(min(y1, y2) + 1, max(y1, y2)):
                if board[(x1, y)]:
                    return False
        # perp move: same column
        if y1 == y2:
            for x in range(min(x1, x2) + 1, max(x1, x2)):
                if board[(x, y1)]:
                    return False
        # diag move
        if abs(y2 - y1) == abs(x2 - x1):
            X = range(x1, x2, -1 if x2 < x1 else 1)
            Y = range(y1, y2, -1 if y2 < y1 else 1)
            for pos in zip(X, Y):
                if pos != move._from and board[pos]:
                    return False
        return True

    @staticmethod
    def final(board: Board, move: Move) -> bool:
        return (
            Checks.to_pos_in_grid(board, move)
            and Checks.to_pos_empty_or_not_same_color(board, move)
            and Checks.king_not_checked_on_next_move(board, move)
            and Checks.no_obstruction(board, move)
            and Checks.is_color_turn(board, move)
        )
