from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from os import stat
from typing import Callable, Self

import numpy as np
from tksvg import SvgImage

from .piece import FEN_MAP, Piece, PieceColor, PieceType
from .setup import Setup
from .types import Position

_Grid = dict[Position, Piece]


def empty_board() -> _Grid:
    return {pos: Piece() for pos in product(range(8), repeat=2)}


@dataclass
class Board:
    pieces: _Grid = field(init=False, default_factory=empty_board)
    color_turn: PieceColor = field(init=False, default=PieceColor.WHITE)
    enpassant_target: Position | None = field(init=False, default=None)
    move_counter: int = field(init=False, default=0)
    # REcord down 50 move rule

    def __post_init__(self):
        self.update_from_fen(Setup.START)

    def toggle_color_turn(self):
        self.color_turn = (
            PieceColor.WHITE
            if self.color_turn == PieceColor.BLACK
            else PieceColor.BLACK
        )

    def update_from_fen(self, fen: str = Setup.START):
        config, color_turn, *_ = fen.replace("/", "").split(" ")
        self.color_turn = PieceColor.WHITE if color_turn == "w" else PieceColor.BLACK

        for digit in "12345678":
            config = config.replace(digit, " " * int(digit))

        for i, p in enumerate(config):
            if p == " ":
                continue
            self[divmod(i,8)] = Piece(*FEN_MAP[p])

    # Slicing for indexing __getitem__

    @property
    def own_king(self) -> Piece | None:
        return next(
            (
                piece
                for piece in self.pieces.values()
                if piece.type == PieceType.KING and piece.color == self.color_turn
            ),
            None,
        )

    @property
    def other_king(self) -> Piece | None:
        return next(
            (
                piece
                for piece in self.pieces.values()
                if piece.type == PieceType.KING and piece.color != self.color_turn
            ),
            None,
        )

    def get_valid_moves(self, pos: Position) -> list[Move]:
        return MOVE_CALCULATORS[self[pos].type](self, pos)

    def __str__(self) -> str:
        pieces_str = [str(piece) for piece in self.pieces.values()]
        rows = ["".join(pieces_str[i : i + 8]) for i in range(0, 64, 8)]
        return "\n".join(rows)


    def __delitem__(self, pos: Position) -> None:
        self[pos] = Piece()
    def __setitem__(self, pos: Position, piece):
        self.pieces[pos] = piece
    def __getitem__(self, pos: Position) -> Piece:
        return self.pieces[pos]


@dataclass
class Move:
    board: Board
    _from: Position
    _to: Position
    _extra_capture: Position | None = None
    enpassant_target: Position | None = None

    @property
    def reset_counter(self) -> bool:
        return self._from_piece.type == PieceType.PAWN or bool(self._to_piece)

    @property
    def _from_piece(self) -> Piece:
        return self.board[self._from]

    @property
    def _to_piece(self) -> Piece:
        return self.board[self._to]

    @property
    def color_turn(self) -> PieceColor:
        return self.board.color_turn

    @classmethod
    def diag(cls, board: Board, _from: Position, n=7) -> list[Self]:
        row, col = _from
        moves = []
        for i in range(1, n + 1):
            NE = cls(board, _from, _to=(row + i, col + i))
            NW = cls(board, _from, _to=(row + i, col - i))
            SE = cls(board, _from, _to=(row - i, col + i))
            SW = cls(board, _from, _to=(row - i, col - i))
            moves.extend([NE, NW, SE, SW])

        return moves

    @classmethod
    def perp(cls, board: Board, _from: Position, n=7) -> list[Self]:
        row, col = _from
        moves = []
        for i in range(1, n + 1):
            N = cls(board, _from, _to=(row + i, col))
            S = cls(board, _from, _to=(row - i, col))
            E = cls(board, _from, _to=(row, col + i))
            W = cls(board, _from, _to=(row, col - i))
            moves.extend([N, S, E, W])

        return moves

    @classmethod
    def lshapes(cls, board: Board, _from: Position) -> list[Self]:
        row, col = _from

        moves = []
        for quadrant in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            for magnitude in [(1, 2), (2, 1)]:
                x, y = np.multiply(quadrant, magnitude)

                moves.append(cls(board, _from, _to=(row + x, col + y)))
        return moves

    @classmethod
    def pincer(cls, board: Board, _from: Position) -> list[Self]:
        row, col = _from
        dir = board[_from].dir
        L = cls(board, _from, _to=(row + dir, col + 1))
        R = cls(board, _from, _to=(row + dir, col - 1))

        return [L, R]

    @classmethod
    def enpassant(cls, board: Board, _from: Position) -> list[Self]:
        row, col = _from
        dir = board[_from].dir
        L = cls(board, _from, _to=(row + dir, col + 1), _extra_capture=(row, col + 1))
        R = cls(board, _from, _to=(row + dir, col - 1), _extra_capture=(row, col - 1))

        return [L, R]

    @classmethod
    def front_short(cls, board: Board, _from: Position) -> list[Self]:
        row, col = _from
        dir = board[_from].dir

        return [cls(board, _from, _to=(row + dir, col))]

    @classmethod
    def front_long(cls, board, _from: Position) -> list[Self]:
        row, col = _from
        dir = board[_from].dir

        return [
            cls(
                board,
                _from,
                _to := (row + 2 * dir, col),
                enpassant_target=_to,
            )
        ]

    @property
    def valid(self) -> bool:
        return (
            Checks.to_pos_in_grid(self)
            and Checks.to_pos_empty_or_not_same_color(self)
            and Checks.king_not_checked_on_next_move(self)
            and Checks.no_obstruction(self)
            and Checks.is_color_turn(self)
        )


def get_moves_empty(*args, **kwargs) -> list[Move]:
    return []


def get_moves_pawn(board: Board, pos: Position) -> list[Move]:
    """Priority: Empassat, Pincer, Long, Short"""

    enpassant = [
        move
        for move in Move.enpassant(board, pos)
        if move.valid and PawnCheck.enpassant_valid(move)
    ]

    pincer = [
        move
        for move in Move.pincer(board, pos)
        if move.valid and PawnCheck.pincer_valid(move)
    ]

    front_long = [
        move
        for move in Move.front_long(board, pos)
        if move.valid and PawnCheck.front_long_valid(move)
    ]

    front_short = [
        move
        for move in Move.front_short(board, pos)
        if move.valid and PawnCheck.front_short_valid(move)
    ]
    capture_moves = enpassant + pincer
    all_moves = enpassant + pincer + front_long + front_short
    return capture_moves if capture_moves else all_moves


def get_moves_rook(board: Board, pos: Position) -> list[Move]:

    valid_moves = [move for move in Move.perp(board, pos) if move.valid]
    capture_moves = [move for move in valid_moves if move._to_piece]

    return capture_moves if capture_moves else valid_moves


def get_moves_knight(board: Board, pos: Position) -> list[Move]:

    valid_moves = [move for move in Move.lshapes(board, pos) if move.valid]
    capture_moves = [move for move in valid_moves if move._to_piece]

    return capture_moves if capture_moves else valid_moves


def get_moves_bishop(board: Board, pos: Position) -> list[Move]:

    valid_moves = [move for move in Move.diag(board, pos) if move.valid]
    capture_moves = [move for move in valid_moves if move._to_piece]

    return capture_moves if capture_moves else valid_moves


def get_moves_queen(board: Board, pos: Position) -> list[Move]:

    all_moves = Move.diag(board, pos) + Move.perp(board, pos)
    valid_moves = [move for move in all_moves if move.valid]
    capture_moves = [move for move in valid_moves if move._to_piece]

    return capture_moves if capture_moves else valid_moves


def get_moves_king(board: Board, pos: Position) -> list[Move]:

    all_moves = Move.diag(board, pos, 1) + Move.perp(board, pos, 1)
    valid_moves = [move for move in all_moves if move.valid]
    capture_moves = [move for move in valid_moves if move._to_piece]

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
    def enpassant_valid(move: Move) -> bool:
        return move.board.enpassant_target == move._extra_capture

    @staticmethod
    def pincer_valid(move: Move) -> bool:
        _from_piece = move.board[move._from]
        _to_piece = move.board[move._to]
        if not _to_piece:
            return False
        if _to_piece.color != _from_piece.color:
            return True
        return False

    @staticmethod
    def front_long_valid(move: Move) -> bool:
        if move._from_piece.color == PieceColor.WHITE:
            starting_rank = move._from[0] == 6
            no_obstruction = not move.board[(5, move._from[1])]
        else:
            starting_rank = move._from[0] == 1
            no_obstruction = not move.board[(2, move._from[1])]

        _to_empty = not move.board[move._to]
        return starting_rank and no_obstruction and _to_empty

    @staticmethod
    def front_short_valid(move: Move) -> bool:
        _to_empty = not move.board[move._to]
        return _to_empty


class Checks:
    @staticmethod
    def is_color_turn(move: Move) -> bool:
        return move.color_turn == move._from_piece.color

    @staticmethod
    def to_pos_in_grid(move: Move) -> bool:
        return max(move._to) <= 7 and min(move._to) >= 0

    @staticmethod
    def to_pos_empty_or_not_same_color(move: Move):
        to_piece = move.board[move._to]
        color_turn = move.color_turn
        return to_piece.color != color_turn

    @staticmethod
    def king_not_checked_on_next_move(move: Move) -> bool:
        # check for enemy fire in king's current psotion
        # check for enemy fire
        # bishops and queens on the diag, rook on the verts,
        # pawns on the near diags
        # knights on the Ls
        #TODO: King check
        board = move.board
        king = board.own_king
        return True

    @staticmethod
    def no_obstruction(move: Move) -> bool:
        x1, y1 = move._from
        x2, y2 = move._to

        # adjacent pieces and knights has no obstruction
        if (
            max(abs(x2 - x1), abs(y2 - y1)) == 1
            or move._from_piece.type == PieceType.KNIGHT
        ):
            return True

        # perp move: same row
        if x1 == x2:
            for y in range(min(y1, y2) + 1, max(y1, y2)):
                if move.board[(x1, y)]:
                    return False
        # perp move: same column
        if y1 == y2:
            for x in range(min(x1, x2) + 1, max(x1, x2)):
                if move.board[(x, y1)]:
                    return False
        # diag move
        if abs(y2 - y1) == abs(x2 - x1):
            X = range(x1, x2, -1 if x2 < x1 else 1)
            Y = range(y1, y2, -1 if y2 < y1 else 1)
            for pos in zip(X, Y):
                if pos != move._from and move.board[pos]:
                    return False
        return True
