from __future__ import annotations

from itertools import product
from random import choice
from tkinter import Button, Event, Tk
from typing import Callable

from tksvg import SvgImage

from .board import Board
from .constants import PIECE_SIZE, THEME, TILE_SIZE
from .piece import COLOR_STR, Piece
from .types import ColorPair, Position


class Root(Tk):
    def __init__(self, theme: ColorPair = THEME.RED) -> None:
        super().__init__()
        self.images = []
        self.theme = theme
        self.title("CHESS")
        self.iconbitmap("res/chess.ico")

        # Bind event logic
        self.bind("<KeyPress>", self.keypress_handler, add=True)
        self.reset_board()

    # account for empassant
    def capture(self, pos_from: Position, pos_to: Position) -> None:
        piece1 = self.board.piece(pos_from)
        self.board.place(Piece(pos_to, piece1.color, piece1.type))
        self.board.place(Piece(pos_from))
        self.refresh_piece(pos_from)
        self.refresh_piece(pos_to)
        self.board.toggle_color_turn()

    def keypress_handler(self, event: Event) -> None:
        print(event)
        match event.char:
            case "\x1b":
                self.quit()
            case "q":
                self.reset_board()

    def reset_board(self) -> None:
        self.board = Board(self.theme)
        self.refresh_board()

    def refresh_piece(self, pos: Position) -> None:
        [slave.destroy() for slave in self.grid_slaves(*pos)]
        piece = self.board.piece(pos)
        bg = self.theme[piece.square_color]

        image = SvgImage(
            file=f"res/{piece.type}_{COLOR_STR[piece.color]}.svg",
            scaletowidth=PIECE_SIZE,
        )
        self.images.append(image)

        Button(
            self,
            image=image,
            bg=bg,
            activebackground=bg,
            bd=0,
            height=TILE_SIZE,
            width=TILE_SIZE,
            command=self.calibrate_button_function(pos),
        ).grid(row=pos[0], column=pos[1])

    # iterate over board
    def refresh_board(self):
        for pos in product(range(8), repeat=2):
            self.refresh_piece(pos)

    # account for empassant
    def calibrate_button_function(self, pos: Position) -> Callable[[], None]:
        def button_function() -> None:
            valid_moves = self.board.get_valid_moves(pos)
            if not valid_moves:
                return
            self.capture(pos, choice(valid_moves))

        return button_function
