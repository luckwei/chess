from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from typing import Callable

from .constants import THEME
from .move import (
    Position,
    get_valid_moves_bishop,
    get_valid_moves_king,
    get_valid_moves_knight,
    get_valid_moves_pawn,
    get_valid_moves_queen,
    get_valid_moves_rook,
)
from .piece import FEN_MAP, Piece, PieceColor, PieceType
from .setup import Setup

Grid = dict[Position, Piece]


def empty_board() -> Grid:
    return {pos: Piece(*pos) for pos in product(range(8), range(8))}


@dataclass
class Board:
    theme: tuple[str, str] = THEME.RED
    pieces: Grid = field(init=False, default_factory=empty_board)

    def __post_init__(self):
        self.update_from_fen()

    def update_from_fen(self, fen: str = Setup.START):
        config, *_ = fen.replace("/", "").split(" ")

        for i in range(1, 9):
            config = config.replace(str(i), " " * i)
        for i, char in enumerate(config):
            if char == " ":
                continue
            row, col = divmod(i, 8)
            self.place(
                Piece(row, col, PieceColor(char.islower()), FEN_MAP[char.lower()])
            )

    def show_as_frame(self, master):
        [piece.place_frame(master, self.theme) for piece in self.pieces.values()]

    def place(self, piece: Piece):
        self.pieces[piece.pos] = piece

    def piece(self, row: int, col: int) -> Piece:
        return self.pieces[(row, col)]

    def empty(self, row: int, col: int) -> bool:
        return not bool(self.piece(row, col))

    def find_king(self, color: PieceColor) -> Piece | None:
        return next(
            (
                piece
                for piece in self.pieces.values()
                if piece.type == PieceType.KING and piece.color == color
            ),
            None,
        )

    def get_valid_moves(self, row: int, col: int) -> list[Position]:
        return MOVE_LIST[self.piece(row, col).type](self, row, col)

    def __str__(self) -> str:
        pieces_str = [str(piece) for piece in self.pieces.values()]
        rows = ["".join(pieces_str[i * 8 : (i + 1) * 8]) for i in range(8)]
        return "\n".join(rows)


ValidMoveCalculator = Callable[[Board, int, int], list[Position]]

MOVE_LIST: dict[PieceType, ValidMoveCalculator] = {
    PieceType.ROOK: get_valid_moves_rook,
    PieceType.BISHOP: get_valid_moves_bishop,
    PieceType.KNIGHT: get_valid_moves_knight,
    PieceType.QUEEN: get_valid_moves_queen,
    PieceType.KING: get_valid_moves_king,
    PieceType.PAWN: get_valid_moves_pawn,
}