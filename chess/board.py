from __future__ import annotations

from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from enum import Enum, IntEnum, auto
from itertools import product
from math import dist
from os import stat
from typing import Callable, Self

import numpy as np

from .piece import FEN_MAP, Piece, PieceColor, PieceType
from .setup import Setup
from .types import Position

_Grid = dict[Position, Piece]
_Flags = dict[PieceColor, list[bool]]


def empty_board() -> _Grid:
    return {pos: Piece() for pos in product(range(8), range(8))}


def castling_flags_initial() -> _Flags:
    return {
        PieceColor.WHITE: [True, True],
        PieceColor.BLACK: [True, True],
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

    # TODO: ADD CHECKMATED PROPERTY
    # TODO: ADD CHECKED PROPERTY
    # TODO: ADD STALEMATE PROPERTY
    ##FIXME: CHECK
    @property
    def checked(self) -> bool:
        return not KingCheck.safe(self, self.king_pos, self.color_turn)

    @property
    def checkmated(self) -> bool:
        return not self.get_all_possible_moves() and self.checked

    @property
    def stalemated(self) -> bool:
        return not self.get_all_possible_moves() and not self.checked

    ##END OF FIXME CHECK

    def __iter__(self):
        return iter(self.pieces.items())

    def get_all_possible_moves(self) -> dict[Position, list[Move]]:
        all_moves = {
            pos: MOVE_CALCULATORS[self[pos].type](self, pos)
            for pos in self.pieces.keys()
        }
        return {pos: move for pos, move in all_moves.items() if move}

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

    def __str__(self) -> str:
        pieces_str = [str(piece) for piece in self.pieces.values()]
        rows = ["".join(pieces_str[i : i + 8]) for i in range(0, 64, 8)]
        return "\n".join(rows)

    def __getitem__(self, pos: Position) -> Piece:
        return self.pieces[pos]

    def __setitem__(self, pos: Position, piece):
        self.pieces[pos] = piece

    def __delitem__(self, pos: Position | None) -> None:
        if pos is None:
            return
        self[pos] = Piece()


class Flag(Enum):
    NONE = auto()
    ENPASSANT_TRGT = auto()
    ENPASSANT = auto()
    CASTLE_LONG = auto()
    CASTLE_SHORT = auto()
    LOSE_KING_PRIV = auto()
    LOSE_ROOK_PRIV = auto()


@dataclass
class Move:
    to: Position
    flag: Flag = Flag.NONE

    @classmethod
    def diag(cls, pos: Position, n=7) -> list[Self]:
        moves = []
        for i in range(1, n + 1):
            NE = cls((pos[0] + i, pos[1] + i))
            NW = cls((pos[0] + i, pos[1] - i))
            SE = cls((pos[0] - i, pos[1] + i))
            SW = cls((pos[0] - i, pos[1] - i))
            moves.extend([NE, NW, SE, SW])
        return moves

    @classmethod
    def perp(cls, pos: Position, n=7) -> list[Self]:
        moves = []
        for i in range(1, n + 1):
            N = cls((pos[0] + i, pos[1]))
            S = cls((pos[0] - i, pos[1]))
            E = cls((pos[0], pos[1] + i))
            W = cls((pos[0], pos[1] - i))
            moves.extend([N, S, E, W])
        return moves

    @classmethod
    def lshapes(cls, pos: Position) -> list[Self]:
        moves = []
        for quadrant in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            for magnitude in [(1, 2), (2, 1)]:
                x, y = np.multiply(quadrant, magnitude)
                moves.append(cls((pos[0] + x, pos[1] + y)))
        return moves

    @classmethod
    def castle_short(cls, pos: Position) -> list[Self]:
        SHORT = cls((pos[0], pos[1] + 2), Flag.CASTLE_SHORT)
        return [SHORT]

    @classmethod
    def castle_long(cls, pos: Position) -> list[Self]:
        LONG = cls((pos[0], pos[1] - 2), Flag.CASTLE_LONG)
        return [LONG]

    @classmethod
    def pincer(cls, pos: Position, dir: int) -> list[Self]:
        L = cls((pos[0] + dir, pos[1] + 1))
        R = cls((pos[0] + dir, pos[1] - 1))
        return [L, R]

    @classmethod
    def enpassant(cls, pos: Position, dir: int) -> list[Self]:
        L = cls((pos[0] + dir, pos[1] + 1), Flag.ENPASSANT)
        R = cls((pos[0] + dir, pos[1] - 1), Flag.ENPASSANT)
        return [L, R]

    @classmethod
    def front_short(cls, pos: Position, dir: int) -> list[Self]:
        return [cls((pos[0] + dir, pos[1]))]

    @classmethod
    def front_long(cls, pos: Position, dir: int) -> list[Self]:
        return [cls((pos[0] + 2 * dir, pos[1]), Flag.ENPASSANT_TRGT)]
        # TODO: Dont allow move if mouse release was away from tile


def get_moves_empty(*args, **kwargs) -> list[Move]:
    return []


def get_moves_pawn(board: Board, pos: Position) -> list[Move]:
    """Priority: Empassat, Pincer, Long, Short"""
    dir = board[pos].dir

    enpassant = [
        move
        for move in Move.enpassant(pos, dir)
        if Checks.final(board, pos, move)
        and PawnCheck.enpassant_valid(board, pos, move)
    ]

    pincer = [
        move
        for move in Move.pincer(pos, dir)
        if Checks.final(board, pos, move) and PawnCheck.pincer_valid(board, pos, move)
    ]

    front_long = [
        move
        for move in Move.front_long(pos, dir)
        if Checks.final(board, pos, move)
        and PawnCheck.front_long_valid(board, pos, move)
    ]

    front_short = [
        move
        for move in Move.front_short(pos, dir)
        if Checks.final(board, pos, move)
        and PawnCheck.front_short_valid(board, pos, move)
    ]
    all_moves = enpassant + pincer + front_long + front_short
    return all_moves


def get_moves_rook(board: Board, pos: Position) -> list[Move]:
    all_moves = [move for move in Move.perp(pos) if Checks.final(board, pos, move)]
    for move in all_moves:
        move.flag = Flag.LOSE_ROOK_PRIV
    return all_moves


def get_moves_knight(board: Board, pos: Position) -> list[Move]:
    return [move for move in Move.lshapes(pos) if Checks.final(board, pos, move)]


def get_moves_bishop(board: Board, pos: Position) -> list[Move]:
    return [move for move in Move.diag(pos) if Checks.final(board, pos, move)]


def get_moves_queen(board: Board, pos: Position) -> list[Move]:
    all_moves = Move.diag(pos) + Move.perp(pos)
    return [move for move in all_moves if Checks.final(board, pos, move)]


def get_moves_king(board: Board, pos: Position) -> list[Move]:
    castle_short = [
        move for move in Move.castle_short(pos) if KingCheck.castle_short_valid(board)
    ]
    castle_long = [
        move for move in Move.castle_long(pos) if KingCheck.castle_long_valid(board)
    ]

    normal_moves = Move.diag(pos, 1) + Move.perp(pos, 1)
    for move in normal_moves:
        move.flag = Flag.LOSE_KING_PRIV

    all_moves = normal_moves + castle_long + castle_short
    return [move for move in all_moves if Checks.final(board, pos, move)]


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


class KingCheck:
    @staticmethod
    def safe(board: Board, pos: Position, color: PieceColor) -> bool:
        enemy_color = (
            PieceColor.WHITE if color == PieceColor.BLACK else PieceColor.BLACK
        )

        dir = -1 if color == PieceColor.WHITE else 1

        enemy_knight = [
            1
            for move in Move.lshapes(pos)
            if Checks.to_pos_in_grid(move)
            and board[move.to] == Piece(enemy_color, PieceType.KNIGHT)
        ]

        # check perpendiculars
        enemy_rook_queen = [
            1
            for move in Move.perp(pos)
            if Checks.to_pos_in_grid(move)
            and board[move.to]
            in (Piece(enemy_color, PieceType.ROOK), Piece(enemy_color, PieceType.QUEEN))
            and Checks.no_obstruction(board, pos, move)
        ]

        # check diagonals
        enemy_bishop_queen = [
            1
            for move in Move.diag(pos)
            if Checks.to_pos_in_grid(move)
            and board[move.to]
            in (
                Piece(enemy_color, PieceType.BISHOP),
                Piece(enemy_color, PieceType.QUEEN),
            )
            and Checks.no_obstruction(board, pos, move)
        ]

        # check adjacent for king
        enemy_king = [
            1
            for move in Move.perp(pos, 1) + Move.diag(pos, 1)
            if Checks.to_pos_in_grid(move)
            and board[move.to] == Piece(enemy_color, PieceType.KING)
        ]

        # check pincer for pawn
        enemy_pawn = [
            1
            for move in Move.pincer(pos, dir)
            if Checks.to_pos_in_grid(move)
            and board[move.to] == Piece(enemy_color, PieceType.PAWN)
        ]

        all_enemies = (
            enemy_knight
            + enemy_rook_queen
            + enemy_bishop_queen
            + enemy_king
            + enemy_pawn
        )

        return not all_enemies

    # TODO GET ALL POSSIBLE MOVES AND CHECK IF 0, IF YES THEN CHECKMATE, black/grey background?
    # TODO KING IS RED IF CHECKED, OR! WHEN INVALID MOVE DUR TO CHECK
    # TODO: IMPLEMENT DRAW FOR stALEMATE
    @staticmethod
    def castle_long_valid(board: Board) -> bool:
        row = 7 if board.color_turn == PieceColor.WHITE else 0

        pos_pass_long = KingCheck.safe(board, (row, 3), board.color_turn)
        clear_lane = not [
            1
            for btwn_pos in [
                (row, 1),
                (row, 2),
                (row, 3),
            ]
            if board[btwn_pos]
        ]

        king_not_checked = KingCheck.safe(board, (row, 4), board.color_turn)

        priviledge = board.castling_flags[board.color_turn][0]
        return pos_pass_long and clear_lane and king_not_checked and priviledge

    @staticmethod
    def castle_short_valid(board: Board) -> bool:
        row = 7 if board.color_turn == PieceColor.WHITE else 0

        pos_pass_short = KingCheck.safe(board, (row, 5), board.color_turn)
        clear_lane = not [
            1
            for btwn_pos in [
                (row, 5),
                (row, 6),
            ]
            if board[btwn_pos]
        ]

        king_not_checked = KingCheck.safe(board, (row, 4), board.color_turn)

        priviledge = board.castling_flags[board.color_turn][1]
        return pos_pass_short and clear_lane and king_not_checked and priviledge


class PawnCheck:
    @staticmethod
    def enpassant_valid(board: Board, pos: Position, move: Move) -> bool:
        to = move.to
        enemy_pawn = (pos[0], to[1])
        return board.enpassant_target == enemy_pawn

    @staticmethod
    def pincer_valid(board: Board, pos: Position, move: Move) -> bool:
        to = move.to
        if not board[to]:
            return False
        if board[move.to].color != board[pos].color:
            return True
        return False

    @staticmethod
    def front_long_valid(board: Board, pos: Position, move: Move) -> bool:
        to = move.to
        color_turn = board.color_turn

        starting_rank = pos[0] == (6 if color_turn == PieceColor.WHITE else 1)
        to_is_empty = not board[to]
        return starting_rank and to_is_empty

    @staticmethod
    def front_short_valid(board: Board, pos: Position, move: Move) -> bool:
        to = move.to
        to_piece = board[to]

        return to_piece.type == PieceType.EMPTY


class Checks:
    @staticmethod
    def to_pos_in_grid(move: Move) -> bool:
        to = move.to

        return max(to) <= 7 and min(to) >= 0

    @staticmethod
    def is_color_turn(board: Board, pos: Position) -> bool:
        color_turn = board.color_turn
        piece = board[pos]

        return color_turn == piece.color

    @staticmethod
    def to_empty_or_enemy(board: Board, pos: Position, move: Move) -> bool:
        to = move.to
        color_turn = board.color_turn
        to_piece = board[to]

        return to_piece.color != color_turn or to_piece.color == PieceColor.NONE

    @staticmethod
    def no_obstruction(board: Board, pos: Position, move: Move) -> bool:
        to = move.to
        pos_x, pos_y = pos
        to_x, to_y = to

        X = range(pos_x, to_x, 1 if to_x > pos_x else -1)
        Y = range(pos_y, to_y, 1 if to_y > pos_y else -1)

        # short moves and knights have no obstruction
        if min(len(X), len(Y)) == 1:
            return True

        # If both exist, diag move
        if X and Y:
            obstructions = [1 for xy in zip(X, Y) if xy != pos and board[xy]]

        # If x exists, perp col, same column
        elif X:
            obstructions = [1 for x in X if (x, pos_y) != pos and board[x, pos_y]]

        # Else y exists, perp col, same row
        else:
            obstructions = [1 for y in Y if (pos_x, y) != pos and board[pos_x, y]]

        return not obstructions

    # TODO: decoupling
    @staticmethod
    def king_safe_at_end(board: Board, pos: Position, move: Move) -> bool:
        to, flag = move.to, move.flag

        end_board = deepcopy(board)
        end_board[to] = end_board[pos]
        del end_board[pos]

        if flag == Flag.ENPASSANT:
            del end_board[end_board.enpassant_target]

        return KingCheck.safe(end_board, end_board.king_pos, board.color_turn)

    @staticmethod
    def final(board: Board, pos: Position, move: Move) -> bool:
        return (
            Checks.to_pos_in_grid(move)
            and Checks.is_color_turn(board, pos)
            and Checks.to_empty_or_enemy(board, pos, move)
            and Checks.no_obstruction(board, pos, move)
            and Checks.king_safe_at_end(board, pos, move)
        )
