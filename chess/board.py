from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from typing import Callable

from .constants import THEME
from .move import (
    Position,
    get_valid_moves_bishop,
    get_valid_moves_empty,
    get_valid_moves_king,
    get_valid_moves_knight,
    get_valid_moves_pawn,
    get_valid_moves_queen,
    get_valid_moves_rook,
)
from .piece import COLOR_STR, FEN_MAP, Piece, PieceColor, PieceType
from .setup import Setup

Grid = dict[Position, Piece]


def empty_board() -> Grid:
    return {pos: Piece(*pos) for pos in product(range(8), range(8))}


@dataclass
class Board:
    theme: tuple[str, str] = THEME.RED
    pieces: Grid = field(init=False, default_factory=empty_board)
    color_turn: PieceColor = field(init=False, default=PieceColor.WHITE)

    def __post_init__(self):
        self.update_from_fen(Setup.START)

    def toggle_color_turn(self):
        self.color_turn = (
            PieceColor.WHITE
            if self.color_turn == PieceColor.BLACK
            else PieceColor.BLACK
        )

    def update_from_fen(self, fen: str = Setup.START):
        config, *_ = fen.replace("/", "").split(" ")

        for i in range(1, 9):
            config = config.replace(str(i), " " * i)
        for i, char in enumerate(config):
            if char == " ":
                continue
            self.place(
                Piece(*divmod(i, 8), PieceColor(char.islower()), FEN_MAP[char.lower()])
            )

    def find_king(self, color: PieceColor) -> Piece:
        return next(
            (
                piece
                for piece in self.pieces.values()
                if piece.type == PieceType.KING and piece.color == color
            )
        )

    def get_valid_moves(self, row: int, col: int) -> list[Position]:
        return MOVE_CALCULATOR[self.piece(row, col).type](self, row, col)

    def __str__(self) -> str:
        pieces_str = [str(piece) for piece in self.pieces.values()]
        rows = ["".join(pieces_str[i * 8 : (i + 1) * 8]) for i in range(8)]
        return "\n".join(rows)

    def place(self, piece: Piece):
        self.pieces[(piece.row, piece.col)] = piece

    def piece(self, row: int, col: int) -> Piece:
        return self.pieces[(row, col)]

    def empty(self, row: int, col: int) -> bool:
        return self.piece(row, col).type == PieceType.EMPTY


ValidMoveCalculator = Callable[[Board, int, int], list[Position]]
CalibratedMoveCalculator = Callable[[], list[Position]]

MOVE_CALCULATOR: dict[PieceType, ValidMoveCalculator] = {
    PieceType.EMPTY: get_valid_moves_empty,
    PieceType.ROOK: get_valid_moves_rook,
    PieceType.BISHOP: get_valid_moves_bishop,
    PieceType.KNIGHT: get_valid_moves_knight,
    PieceType.QUEEN: get_valid_moves_queen,
    PieceType.KING: get_valid_moves_king,
    PieceType.PAWN: get_valid_moves_pawn,
}
