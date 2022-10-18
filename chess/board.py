from __future__ import annotations

import itertools
import tkinter as tk

import chess

from .constants import THEME, TILE_SIZE

# def function that will check whether


class Tile(tk.Frame):
    def __init__(self, cb: ChessBoard, bg, pos: tuple[int, int]):
        # Create a tile in chessboard's grid
        super().__init__(cb, width=TILE_SIZE, height=TILE_SIZE, bg=bg)
        self.grid(row=pos[0], column=pos[1])

        # Tiles are empty until a Piece is attached
        self.piece: chess.Piece | None = None


class ChessBoard(tk.Frame):
    def __init__(self, master, theme: tuple[str, str] = THEME, **kwargs) -> None:
        # Initialise chessboard frame and display it
        super().__init__(master, width=8 * TILE_SIZE, height=8 * TILE_SIZE, **kwargs)
        self.pack()
        
        # Initialise 8 x 8 tiles with alternating colors
        self.tiles = {
            pos: Tile(self, theme[sum(pos) % 2], pos)
            for pos in itertools.product(range(8), range(8))
        }


        self.reset()

        self.master.bind("<KeyPress>", self.keypress_response, add=True)

    def clear(self):
        [tile.piece.remove() for tile in self.tiles.values() if tile.piece]

    def reset(self):
        self.clear()
        for row, color, pieces in chess.SETUP:
            for col, piece in enumerate(pieces):
                self.tiles[(row, col)].piece = piece(self, color, (row, col))

    def keypress_response(self, event):
        if event.char == "q":
            self.clear()
        elif event.char == "w":
            self.reset()


def main() -> None:
    ...


if __name__ == "__main__":
    main()
