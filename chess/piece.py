from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class PieceType(Enum):
    EMPTY = "empty"
    PAWN = "pawn"
    ROOK = "rook"
    KNIGHT = "knight"
    BISHOP = "bishop"
    QUEEN = "queen"
    KING = "king"


class PieceColor(Enum):
    NONE = -1
    WHITE = 0
    BLACK = 1


FEN_MAP: dict[str, PieceType] = {
    "p": PieceType.PAWN,
    "n": PieceType.KNIGHT,
    "b": PieceType.BISHOP,
    "r": PieceType.ROOK,
    "q": PieceType.QUEEN,
    "k": PieceType.KING,
}


PIECE_STR: dict[PieceType, tuple[str, str]] = {
    PieceType.EMPTY: (" ", " "),
    PieceType.PAWN: ("♙", "♟"),
    PieceType.ROOK: ("♖", "♜"),
    PieceType.BISHOP: ("♗", "♝"),
    PieceType.QUEEN: ("♕", "♛"),
    PieceType.KING: ("♔", "♚"),
    PieceType.KNIGHT: ("♘", "♞"),
}

COLOR_STR: dict[PieceColor, str] = {
    PieceColor.NONE: "none",
    PieceColor.WHITE: "white",
    PieceColor.BLACK: "black",
}


@dataclass
class Piece:
    row: int
    col: int
    color: PieceColor = PieceColor.NONE
    type: PieceType = PieceType.EMPTY

    @property
    def dir(self) -> Literal[-1, 1, 0]:
        match self.color:
            case PieceColor.WHITE:
                return -1
            case PieceColor.BLACK:
                return 1
        return 0

    @property
    def square_color(self) -> int:
        return (self.row + self.col) % 2

    def __str__(self):
        return PIECE_STR[self.type][self.color.value]

    def __bool__(self):
        return self.type != PieceType.EMPTY
