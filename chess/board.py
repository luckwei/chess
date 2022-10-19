from __future__ import annotations

import tkinter as tk
from itertools import product

import chess

from .constants import THEME, TILE_SIZE
from .GUI import Root
from .helper import Pos


class Tile(tk.Frame):
    """Tile of the Chessboard, able to house a chess Piece"""

    def __init__(self, cb: ChessBoard, pos: tuple[int, int]) -> None:
        # Create a tile in chessboard's grid
        super().__init__(cb, width=TILE_SIZE, height=TILE_SIZE, bg=THEME[sum(pos) % 2])
        self.grid(row=pos[0], column=pos[1])


class ChessBoard(tk.Frame):
    """Chessboard with Root as Master"""

    def __init__(self, master: Root) -> None:
        # Initialise chessboard frame and display it
        super().__init__(master, width=8 * TILE_SIZE, height=8 * TILE_SIZE)
        self.pack()

        # Initialise 8 x 8 tiles with alternating colors
        self.tiles = {pos: Tile(self, pos) for pos in product(range(8), range(8))}
        self.pieces: dict[tuple[int, int], chess.Piece | None] = {
            pos: None for pos in product(range(8), range(8))
        }

        # Initialise starting position
        self.reset()

    def clear(self) -> None:
        """Clears pieces from chessboard"""
        [piece.kill() for piece in self.pieces.values() if piece]

    def reset(self) -> None:
        """Clears pieces and sets starting position"""
        self.clear()
        for row, color, pieces in chess.SETUP:
            for col, Piece in enumerate(pieces):
                self.pieces[(row, col)] = Piece(self, color, Pos(row, col))


def main() -> None:
    ...


if __name__ == "__main__":
    main()
