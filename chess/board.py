from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product

from .constants import THEME
from .move import MOVE_CALCULATORS, Position
from .piece import FEN_MAP, Piece, PieceColor, PieceType
from .setup import Setup

_Grid = dict[Position, Piece]


def empty_board() -> _Grid:
    return {pos: Piece(pos) for pos in product(range(8), repeat=2)}


@dataclass
class Board:
    theme: tuple[str, str] = THEME.RED
    pieces: _Grid = field(init=False, default_factory=empty_board)
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
        #change to string loop
        for i in range(1, 9):
            config = config.replace(str(i), " " * i)
        for i, char in enumerate(config):
            if char == " ":
                continue
            self.place(
                Piece(divmod(i, 8), PieceColor(char.islower()), FEN_MAP[char.lower()])
            )

    def find_king(self, color: PieceColor) -> Piece:
        return next(
            (
                piece
                for piece in self.pieces.values()
                if piece.type == PieceType.KING and piece.color == color
            )
        )

    def get_valid_moves(self, pos: Position) -> list[Position]:
        return MOVE_CALCULATORS[self.piece(pos).type](self, pos)

    def __str__(self) -> str:
        pieces_str = [str(piece) for piece in self.pieces.values()]
        rows = ["".join(pieces_str[i * 8 : (i + 1) * 8]) for i in range(8)]
        return "\n".join(rows)

    def place(self, piece: Piece):
        self.pieces[piece.pos] = piece

    def piece(self, pos: Position) -> Piece:
        return self.pieces[pos]

    def empty(self, pos: Position) -> bool:
        return self.piece(pos).type == PieceType.EMPTY
