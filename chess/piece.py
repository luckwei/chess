from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, StrEnum, auto


from .types import Position


class PieceType(StrEnum):
    EMPTY = auto()
    PAWN = auto()
    ROOK = auto()
    KNIGHT = auto()
    BISHOP = auto()
    QUEEN = auto()
    KING = auto()


class PieceColor(StrEnum):
    NONE = auto()
    WHITE = auto()
    BLACK = auto()


COLOR_TYPE: list[tuple[PieceColor, PieceType]] = [
    (PieceColor.NONE, PieceType.EMPTY),
    (PieceColor.BLACK, PieceType.PAWN),
    (PieceColor.BLACK, PieceType.KNIGHT),
    (PieceColor.BLACK, PieceType.BISHOP),
    (PieceColor.BLACK, PieceType.ROOK),
    (PieceColor.BLACK, PieceType.QUEEN),
    (PieceColor.BLACK, PieceType.KING),
    (PieceColor.WHITE, PieceType.PAWN),
    (PieceColor.WHITE, PieceType.KNIGHT),
    (PieceColor.WHITE, PieceType.BISHOP),
    (PieceColor.WHITE, PieceType.ROOK),
    (PieceColor.WHITE, PieceType.QUEEN),
    (PieceColor.WHITE, PieceType.KING),
]


FEN_MAP: dict[str, tuple[PieceColor, PieceType]] = {
    "p": (PieceColor.BLACK, PieceType.PAWN),
    "n": (PieceColor.BLACK, PieceType.KNIGHT),
    "b": (PieceColor.BLACK, PieceType.BISHOP),
    "r": (PieceColor.BLACK, PieceType.ROOK),
    "q": (PieceColor.BLACK, PieceType.QUEEN),
    "k": (PieceColor.BLACK, PieceType.KING),
    "P": (PieceColor.WHITE, PieceType.PAWN),
    "N": (PieceColor.WHITE, PieceType.KNIGHT),
    "B": (PieceColor.WHITE, PieceType.BISHOP),
    "R": (PieceColor.WHITE, PieceType.ROOK),
    "Q": (PieceColor.WHITE, PieceType.QUEEN),
    "K": (PieceColor.WHITE, PieceType.KING),
}

PIECE_STR: dict[tuple[PieceColor, PieceType], str] = {
    (PieceColor.NONE, PieceType.EMPTY): " ",
    (PieceColor.BLACK, PieceType.PAWN): "♟",
    (PieceColor.BLACK, PieceType.KNIGHT): "♞",
    (PieceColor.BLACK, PieceType.BISHOP): "♝",
    (PieceColor.BLACK, PieceType.ROOK): "♜",
    (PieceColor.BLACK, PieceType.QUEEN): "♛",
    (PieceColor.BLACK, PieceType.KING): "♚",
    (PieceColor.WHITE, PieceType.PAWN): "♙",
    (PieceColor.WHITE, PieceType.KNIGHT): "♘",
    (PieceColor.WHITE, PieceType.BISHOP): "♗",
    (PieceColor.WHITE, PieceType.ROOK): "♖",
    (PieceColor.WHITE, PieceType.QUEEN): "♕",
    (PieceColor.WHITE, PieceType.KING): "♔",
}

PIECE_VAL = {
    PieceType.EMPTY: 0.5,
    # No problem since captures and moves are exclusive
    PieceType.PAWN: 1,
    PieceType.KNIGHT: 3,
    PieceType.BISHOP: 3,
    PieceType.ROOK: 5,
    PieceType.QUEEN: 9,
    PieceType.KING: 10,
    # Generally stronger than bishop/knight in end game (4)
    # But in killer chess has to be worth more than the queen (10)
}


@dataclass
class Piece:
    color: PieceColor = PieceColor.NONE
    type: PieceType = PieceType.EMPTY

    @property
    def dir(self) -> int:
        direction = {PieceColor.WHITE: -1, PieceColor.BLACK: 1, PieceColor.NONE: 0}
        return direction[self.color]

    def __str__(self):
        return PIECE_STR[(self.color, self.type)]

    def __bool__(self):
        return self.type != PieceType.EMPTY
    
    def __eq__(self, other: Piece) -> bool:
        return self.color == other.color and self.type == other.type
