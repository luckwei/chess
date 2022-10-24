from __future__ import annotations
from itertools import product
from random import choice

from tkinter import Button, Event, Tk
from typing import Callable

from tksvg import SvgImage

from chess.piece import COLOR_STR, Piece, PieceColor

from .board import Board
from .constants import PIECE_SIZE, THEME, TILE_SIZE


class Root(Tk):
    def __init__(self, theme: tuple[str, str] = THEME.RED):
        super().__init__()
        self.images = []
        self.theme = theme
        self.title("CHESS")
        self.iconbitmap("res/chess.ico")

        # Bind event logic
        self.bind("<KeyPress>", self.keypress_handler, add=True)
        self.reset_board()
    
    def capture(self, row1, col1, row2, col2):
        piece1 = self.board.piece(row1, col1)
        self.board.place(Piece(row2, col2, piece1.color, piece1.type))
        self.board.place(Piece(row1, col1))
        self.refresh_piece(row1, col1)
        self.refresh_piece(row2, col2)
    
    #After every move
    def toggle_board_to_move(self):
        self.board.to_move = PieceColor.WHITE if self.board.to_move == PieceColor.BLACK else PieceColor.BLACK

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
            file=f"res/{piece.type.value}_{COLOR_STR[piece.color]}.svg",
            scaletowidth=PIECE_SIZE,
        )
        self.images.append(image)

        button = Button(
            self,
            image=image,
            bg=bg,
            activebackground=bg,
            bd=0,
            height=TILE_SIZE,
            width=TILE_SIZE,
            command=self.calibrate_button_function(row, col),
        )
        button.grid(row=piece.row, column=piece.col)
    
    def refresh_board(self):
        for row, col in product(range(8), range(8)):
            self.refresh_piece(row, col)
    
    def calibrate_button_function(self, row, col) -> Callable[[], None]:
        def button_function() -> None:
            list_of_moves = self.board.get_valid_moves(row, col)
            if list_of_moves:
                self.capture(row, col, *choice(list_of_moves))
        return button_function
