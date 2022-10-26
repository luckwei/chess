from __future__ import annotations

from ast import Str
from dataclasses import dataclass
from enum import Enum, StrEnum, auto
from typing import Literal

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



@dataclass
class Piece:
    pos: Position
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
        # TODO: FIX GET WHOLE DICTIONARY

    def __str__(self):
        return PIECE_STR[(self.color, self.type)]

    def __bool__(self):
        return self.type != PieceType.EMPTY
