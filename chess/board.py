from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass, field
from itertools import product, repeat
from typing import Callable

import numpy as np

from .constants import PIECE_SIZE, THEME, TILE_SIZE
from .move import Position, get_valid_moves_rook
from .piece import FEN_MAP, Piece, PieceColor, PieceType

Grid = dict[Position, Piece]


@dataclass
class Board:
    theme: tuple[str, str] = THEME.RED
    pieces: Grid = field(init=False)

    def __post_init__(self):
        self.pieces = {
            (row, col): Piece(row, col, theme=self.theme)
            for row, col in product(range(8), range(8))
        }
        
        self.update_from_fen()


    def update_from_fen(self, file: str = "res/start.fen"):
        with open(file) as f:
            text = f.read()

        config, to_move, *_ = text.split(" ")

        for row_i, row in enumerate(config.split("/")):
            col_i = 0
            for char in row:
                if char.isdigit():
                    col_i += int(char)
                    continue
                self.place(
                    Piece(
                        row_i,
                        col_i,
                        PieceColor(char.islower()),
                        FEN_MAP[char.lower()],
                        theme=self.theme,
                    )
                )
                col_i += 1

    def show_as_frame(self, master):
        for piece in self.pieces.values():
            piece.place_frame(master)

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
        line = ""
        for i, piece in enumerate(self.pieces.values()):
            if i % 8 == 0:
                line += "\n"
            line += str(piece)

        return line


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
