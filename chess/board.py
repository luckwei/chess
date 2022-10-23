from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass, field
from itertools import product
from typing import Callable

from .constants import PIECE_SIZE, TILE_SIZE
from .move import Position, get_valid_moves_rook
from .piece import Piece, PieceColor, PieceType

Grid = dict[Position, Piece]


def empty_board() -> Grid:
    return {(row, col): Piece(row, col) for row, col in product(range(8), range(8))}


@dataclass
class Board:
    theme: tuple[str, str]
    pieces: Grid = field(init=False, default_factory=empty_board)

    def show_as_frame(self, master):
        for piece in self.pieces.values():
            piece.frame(master)

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


ValidMoveCalculator = Callable[[Board, int, int], list[Position]]

MOVE_LIST: dict[PieceType, ValidMoveCalculator] = {PieceType.ROOK: get_valid_moves_rook}


# class Tile(tk.Frame):
#     """Tile of the Chessboard, able to house a chess Piece"""

#     def __init__(
#         self, cb: ChessBoard, pos: tuple[int, int], theme: tuple[str, str]
#     ) -> None:
#         # Create a tile in chessboard's grid
#         super().__init__(cb, width=TILE_SIZE, height=TILE_SIZE, bg=theme[sum(pos) % 2])
#         self.grid(row=pos[0], column=pos[1])


# class ChessBoard(tk.Frame):
#     """Chessboard with Root as Master"""

#     def __init__(self, master: Root, theme: tuple[str, str]) -> None:
#         # Initialise chessboard frame and display it
#         super().__init__(master, width=8 * TILE_SIZE, height=8 * TILE_SIZE)
#         self.pack()

#         self._theme = theme

#         # Initialise 8 x 8 tiles with alternating colors
#         self.tiles = {
#             pos: Tile(self, pos, theme) for pos in product(range(8), range(8))
#         }
#         self.pieces: dict[tuple[int, int], chess.Piece | None] = {
#             pos: None for pos in product(range(8), range(8))
#         }

#         # Initialise starting position
#         self.reset()
#         self.master.bind("<KeyPress>", self.keypress_handler, add=True)

#     def clear(self) -> None:
#         """Clears pieces from chessboard"""
#         [piece.captured() for piece in self.pieces.values() if piece]

#     def reset(self) -> None:
#         """Clears pieces and sets starting position"""
#         self.clear()
#         for row, color, pieces in chess.SETUP:
#             for col, Piece in enumerate(pieces):
#                 self.pieces[(row, col)] = Piece(self, color, Pos(row, col), self._theme)

#     def keypress_handler(self, event):
#         if event.char == "f":
#             import numpy as np

#             a = np.array([1 if piece else 0 for piece in self.pieces.values()])
#             print(a.reshape((8, 8)))


# def main() -> None:
#     ...


# if __name__ == "__main__":
#     main()
