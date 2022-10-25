from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from typing import Callable, Self

import numpy as np

from .constants import THEME_RED
from .piece import COLOR_STR, FEN_MAP, Piece, PieceColor, PieceType
from .setup import Setup
from .types import ColorPair, Position

_Grid = dict[Position, Piece]


def empty_board() -> _Grid:
    return {pos: Piece(pos) for pos in product(range(8), repeat=2)}


@dataclass
class Board:
    theme: ColorPair = THEME_RED
    pieces: _Grid = field(init=False, default_factory=empty_board)
    color_turn: PieceColor = field(init=False, default=PieceColor.WHITE)
    enpassant_target: Position | None = field(init=False, default=None)
    fifty_move_counter: int = field(init=False, default=0)
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
            self.place(Piece(divmod(i, 8), *FEN_MAP[p]))

    def find_king(self, color: PieceColor) -> Piece:
        return next(
            (
                piece
                for piece in self.pieces.values()
                if piece.type == PieceType.KING and piece.color == color
            )
        )

    def get_valid_moves(self, pos: Position) -> list[Move]:
        return MOVE_CALCULATORS[self.piece(pos).type](self, pos)

    def __str__(self) -> str:
        pieces_str = [str(piece) for piece in self.pieces.values()]
        rows = ["".join(pieces_str[i * 8 : (i + 1) * 8]) for i in range(8)]
        return "\n".join(rows)

    def place(self, piece: Piece) -> None:
        self.pieces[piece.pos] = piece

    def remove(self, pos: Position) -> None:
        self.place(Piece(pos))

    def piece(self, pos: Position) -> Piece:
        return self.pieces[pos]

    def empty(self, pos: Position) -> bool:
        return self.piece(pos).type == PieceType.EMPTY


@dataclass
class Move:
    board: Board
    piece: Piece
    _from: Position
    _to: Position
    _capture: Position | None = None
    enpassant_target: Position | None = None

    @classmethod
    def diag(cls, board: Board, piece: Piece, _from: Position, n=7) -> list[Self]:
        row, col = _from
        move_obj_list = []
        for i in range(1, n + 1):
            NE = cls(board, piece, _from, _to := (row + i, col + i), _to)
            NW = cls(board, piece, _from, _to := (row + i, col - i), _to)
            SE = cls(board, piece, _from, _to := (row - i, col + i), _to)
            SW = cls(board, piece, _from, _to := (row - i, col - i), _to)
            move_obj_list.extend([NE, NW, SE, SW])
        # TODO:validation should not be done in the whole class, move into these factory class methods later

        return move_obj_list

    @classmethod
    def perp(cls, board: Board, piece: Piece, _from: Position, n=7) -> list[Self]:
        row, col = _from
        move_obj_list = []
        for i in range(1, n + 1):
            N = cls(board, piece, _from, _to := (row + i, col), _to)
            S = cls(board, piece, _from, _to := (row - i, col), _to)
            E = cls(board, piece, _from, _to := (row, col + i), _to)
            W = cls(board, piece, _from, _to := (row, col - i), _to)
            move_obj_list.extend([N, S, E, W])
        # TODO:validation should not be done in the whole class, move into these factory class methods later

        return move_obj_list

    @classmethod
    def lshapes(cls, board: Board, piece: Piece, _from: Position) -> list[Self]:
        row, col = _from
        direction = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        magnitude = [(1, 2), (2, 1)]
        vec = [np.multiply(*dm) for dm in product(direction, magnitude)]
        move_obj_list = [
            cls(board, piece, _from, _to := (row + x, col + y), _to) for x, y in vec
        ]
        return move_obj_list

    @classmethod
    def pincer(cls, board: Board, piece: Piece, _from: Position) -> list[Self]:
        row, col = _from
        dir = board.piece(_from).dir
        L = cls(board, piece, _from, _to := (row + dir, col + 1), _to)
        R = cls(board, piece, _from, _to := (row + dir, col - 1), _to)

        return [L, R]

    @classmethod
    def enpassant(cls, board: Board, piece: Piece, _from: Position) -> list[Self]:
        row, col = _from
        dir = board.piece(_from).dir
        # implement board last move to check whether it was a jump long jump
        # maybe also implement piece last move to check if pawn at the side was a long jump
        L = cls(board, piece, _from, (row + dir, col + 1), (row, col + 1))
        R = cls(board, piece, _from, (row + dir, col - 1), (row, col - 1))

        return [L, R]

    @classmethod
    def front_short(cls, board: Board, piece: Piece, _from: Position) -> list[Self]:
        # does not allow capture
        # put condition here
        row, col = _from
        dir = board.piece(_from).dir

        F1 = cls(board, piece, _from, (row + dir, col), None)
        return [F1]

    @classmethod
    def front_long(cls, board, piece, _from: Position) -> list[Self]:
        # does not allow capture
        row, col = _from
        dir = board.piece(_from).dir

        F2 = cls(
            board,
            piece,
            _from,
            _to := (row + 2 * dir, col),
            enpassant_target=_to,
        )
        return [F2]

    # Valid should not be part of piece as property, either external or part of class methods
    @property
    def valid(self) -> bool:
        return Checks.final_valid(self)


def print_valid_moves(moves: list[Move], piece: Piece):
    valid_moves = [move._to for move in moves]
    print(f"{piece}\t{valid_moves=}" if valid_moves else f"!NO VALID {piece} MOVES!")


def get_valid_moves_empty(*args, **kwargs) -> list[Move]:
    print("!EMPTY!")
    return []


def get_valid_moves_pawn(board: Board, pos: Position) -> list[Move]:
    """Priority: Empassat, Pincer, Long, Short"""
    piece = board.piece(pos)
    if piece.color != board.color_turn:
        print(f"!{COLOR_STR[board.color_turn]}'s TURN!")
        return []

    enpassant = [
        move
        for move in Move.enpassant(board, piece, pos)
        if PawnChecks.enpassant_valid(move) and move.valid
    ]

    pincer = [
        move
        for move in Move.pincer(board, piece, pos)
        if PawnChecks.pincer_valid(move) and move.valid
    ]

    front_long = [
        move
        for move in Move.front_long(board, piece, pos)
        if PawnChecks.front_long_valid(move) and move.valid
    ]

    front_short = [
        move
        for move in Move.front_short(board, piece, pos)
        if PawnChecks.front_short_valid(move) and move.valid
    ]


    if enpassant:
        return enpassant
    if pincer:
        return pincer
    if front_long:
        return front_long
    if front_short:
        return front_short
    return []
    # if
    # for front_long in Move.front_long(board,piece, pos):
    #     if Checks.front_long_valid(front_long):
    #         return [front_long]

    # for front_short in Move.front_short(board,piece, pos):
    #     if Checks.final_valid(front_short):
    #         return [front_short]

    # all_moves = (
    #     Move.pincer(board,piece, pos)
    #     + Move.empassant(board,piece, pos)
    #     + Move.front_short(board,piece, pos)
    #     + Move.front_long(board, piece,pos)
    # )
    # valid_moves = [move for move in all_moves if move.valid]

    # print_valid_moves(valid_moves, piece)
    # return valid_moves


def get_valid_moves_rook(board: Board, pos: Position) -> list[Move]:
    piece = board.piece(pos)
    if board.piece(pos).color != board.color_turn:
        print(f"!{COLOR_STR[board.color_turn]}'s TURN!")
        return []

    all_moves = Move.perp(board, piece, pos)
    valid_moves = [move for move in Move.perp(board, piece, pos) if move.valid]

    print_valid_moves(valid_moves, piece)
    return valid_moves


## TODO: Root remove mechanism, hence all these return list[Move], use Move information to do UI change
def get_valid_moves_knight(board: Board, pos: Position) -> list[Move]:
    piece = board.piece(pos)
    if board.piece(pos).color != board.color_turn:
        print(f"!{COLOR_STR[board.color_turn]}'s TURN!")
        return []
    all_moves = Move.lshapes(board, piece, pos)
    valid_moves = [move for move in all_moves if move.valid]

    print_valid_moves(valid_moves, piece)
    return valid_moves


def get_valid_moves_bishop(board: Board, pos: Position) -> list[Move]:
    piece = board.piece(pos)
    if board.piece(pos).color != board.color_turn:
        print(f"!{COLOR_STR[board.color_turn]}'s TURN!")
        return []

    all_moves = Move.diag(board, piece, pos)
    valid_moves = [move for move in all_moves if move.valid]

    print_valid_moves(valid_moves, piece)
    return valid_moves


def get_valid_moves_queen(board: Board, pos: Position) -> list[Move]:
    piece = board.piece(pos)
    if board.piece(pos).color != board.color_turn:
        print(f"!{COLOR_STR[board.color_turn]}'s TURN!")
        return []

    all_moves = Move.diag(board, piece, pos) + Move.perp(board, piece, pos)
    valid_moves = [move for move in all_moves if move.valid]

    print_valid_moves(valid_moves, piece)
    return valid_moves


def get_valid_moves_king(board: Board, pos: Position) -> list[Move]:
    piece = board.piece(pos)
    if board.piece(pos).color != board.color_turn:
        print(f"!{COLOR_STR[board.color_turn]}'s TURN!")
        return []

    all_moves = Move.diag(board, piece, pos, 1) + Move.perp(board, piece, pos, 1)
    valid_moves = [move for move in all_moves if move.valid]

    print_valid_moves(valid_moves, piece)
    return valid_moves


ValidMoveCalculator = Callable[[Board, Position], list[Move]]

MOVE_CALCULATORS: dict[PieceType, ValidMoveCalculator] = {
    PieceType.EMPTY: get_valid_moves_empty,
    PieceType.ROOK: get_valid_moves_rook,
    PieceType.BISHOP: get_valid_moves_bishop,
    PieceType.KNIGHT: get_valid_moves_knight,
    PieceType.QUEEN: get_valid_moves_queen,
    PieceType.KING: get_valid_moves_king,
    PieceType.PAWN: get_valid_moves_pawn,
}

from .types import Position


class PawnChecks:
    @staticmethod
    def pincer_valid(move: Move) -> bool:
        _to_piece = move.board.piece(move._to)
        if not _to_piece:
            return False
        if _to_piece.color != move.piece.color:
            return True
        return False

    @staticmethod
    def front_short_valid(move: Move) -> bool:
        _to_empty = not move.board.piece(move._to)
        return _to_empty

    @staticmethod
    def front_long_valid(move: Move) -> bool:
        if move.piece.color == PieceColor.WHITE:
            starting_rank = move._from[0] == 6
            no_obstruction = not move.board.piece((5, move._from[1]))
        else:
            starting_rank = move._from[0] == 1
            no_obstruction = not move.board.piece((2, move._from[1]))

        _to_empty = not move.board.piece(move._to)
        return starting_rank and no_obstruction and _to_empty

    @staticmethod
    def enpassant_valid(move: Move) -> bool:
        return move.board.enpassant_target == move._capture


class Checks:
    @staticmethod
    def is_color_turn(move: Move) -> bool:
        return move.board.color_turn == move.piece.color

    @staticmethod
    def to_pos_in_grid(move: Move) -> bool:
        pos = move._to
        return max(pos) <= 7 and min(pos) >= 0

    @staticmethod
    def to_pos_empty_or_not_same_color(move: Move):
        to_piece = move.board.piece(move._to)
        color_turn = move.board.color_turn
        return to_piece.color != color_turn

    @staticmethod
    def king_not_checked(move: Move) -> bool:
        # check for enemy fire in king's current psotion
        board = move.board
        king = board.find_king(board.color_turn)
        return not_targetted(board, king.pos)

    @staticmethod
    def no_obstruction(board: Board, _from: Position, _to: Position) -> bool:
        ...

    @staticmethod
    def final_valid(move: Move) -> bool:
        return (
            Checks.to_pos_in_grid(move)
            and Checks.to_pos_empty_or_not_same_color(move)
            and (
                Checks.king_not_checked(move)  # before
                or Checks.king_not_checked(move)  # after
            )
            and Checks.is_color_turn(move)
        )


def not_targetted(board: Board, pos: Position) -> bool:
    # check for enemy fire
    # bishops and queens on the diag, rook on the verts,
    # pawns on the near diags
    # knights on the Ls
    return True
