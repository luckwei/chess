from __future__ import annotations

import tkinter as tk
from itertools import product

import chess

from .constants import THEME, TILE_SIZE
from .GUI import Root


class Tile(tk.Frame):
    """Tile of the Chessboard, able to house a chess Piece"""

    def __init__(self, cb: ChessBoard, pos: tuple[int, int]) -> None:
        # Create a tile in chessboard's grid
        super().__init__(cb, width=TILE_SIZE, height=TILE_SIZE, bg=THEME[sum(pos) % 2])
        self.grid(row=pos[0], column=pos[1])

        self.pos = pos
        # Tiles are empty until a Piece is attached
        self._piece: chess.Piece | None = None

    @property
    def piece(self) -> chess.Piece | None:
        return self._piece

    @piece.setter
    def piece(self, new_piece: chess.Piece) -> None:

        # If a piece already exists on new spot, remove display and kill it
        if self._piece:
            self._piece.remove(kill=True)

        # Remove from old spot and show in new_spot
        new_piece.remove()
        new_piece.show(self.pos)

        self._piece = new_piece


class ChessBoard(tk.Frame):
    """Chessboard with Root as Master"""

    def __init__(self, master: Root) -> None:
        # Initialise chessboard frame and display it
        super().__init__(master, width=8 * TILE_SIZE, height=8 * TILE_SIZE)
        self.pack()

        # Initialise 8 x 8 tiles with alternating colors
        self.tiles = {pos: Tile(self, pos) for pos in product(range(8), range(8))}

        # Initialise starting position
        self.reset()

        # Bind event logic
        self.master.bind("<KeyPress>", self.keypress_handler, add=True)

    def clear(self) -> None:
        """Clears pieces from chessboard"""
        for tile in self.tiles.values():
            if tile.piece:
                tile.piece.remove()
                tile.piece.alive = False

    def reset(self) -> None:
        """Clears pieces and sets starting position"""
        self.clear()
        for row, color, pieces in chess.SETUP:
            for col, Piece in enumerate(pieces):
                self.tiles[(row, col)].piece = Piece(self, color, (row, col))

    def keypress_handler(self, event) -> None:
        """Handles keypress events"""
        if event.char == "q":
            self.clear()
        elif event.char == "w":
            self.reset()


def main() -> None:
    ...


if __name__ == "__main__":
    main()
