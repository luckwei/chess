from __future__ import annotations

from itertools import product
from random import choice
from tkinter import Button, Event, Tk
from typing import Callable

from tksvg import SvgImage

from .board import Board
from .constants import PIECE_SIZE, THEME, TILE_SIZE, ColorPair
from .move import Position
from .piece import COLOR_STR, Piece


class Root(Tk):
    def __init__(self, theme: ColorPair = THEME.RED):
        super().__init__()
        self.images = []
        self.theme = theme
        self.title("CHESS")
        self.iconbitmap("res/chess.ico")

        # Bind event logic
        self.bind("<KeyPress>", self.keypress_handler, add=True)
        self.reset_board()

    # account for empassant
    def capture(self, pos_from: Position, pos_to: Position):
        piece1 = self.board.piece(*pos_from)
        self.board.place(Piece(*pos_to, piece1.color, piece1.type))
        self.board.place(Piece(*pos_from))
        self.refresh_piece(*pos_from)
        self.refresh_piece(*pos_to)
        self.board.toggle_color_turn()

    def keypress_handler(self, event: Event):
        print(event)
        match event.char:
            case "\x1b":
                self.quit()
            case "q":
                self.reset_board()

    def reset_board(self):
        self.board = Board(self.theme)
        self.refresh_board()

    def refresh_piece(self, row, col):
        [slave.destroy() for slave in self.grid_slaves(row, col)]
        piece = self.board.piece(row, col)
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
            command=self.calibrate_button_function(row, col),
        ).grid(row=row, column=col)

    def refresh_board(self):
        for row, col in product(range(8), range(8)):
            self.refresh_piece(row, col)

    # account for empassant
    def calibrate_button_function(self, row, col) -> Callable[[], None]:
        def button_function() -> None:
            # account for empassant: idea is for valid_moves to send dictionaries
            # or moves will consist of tuple[MoveType, Position]
            # TODO: create MoveType: Perp(n), Diag(n, dir), Lshape, Empassant, FrontShort, FrontExtend
            # Knight: Lshape(1,2,+-)
            # King: Diag(1), Perp(1)
            # Queen: Diag(7), Perp(7)
            # Pawn: Diag(1, dir), Empassant[Diag(1,dir)], FrontShort(1), FrontExtended(2)
            # Rook: Perp(7)
            # Bishop: Diag(7)
            valid_moves = self.board.get_valid_moves(row, col)
            if not valid_moves:
                return
            self.capture((row, col), choice(valid_moves))

        return button_function
