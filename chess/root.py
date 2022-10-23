from __future__ import annotations

from tkinter import Button, Event, Tk

from tksvg import SvgImage

from chess.piece import COLOR_STR

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
        self.display_board()

    def keypress_handler(self, event: Event):
        print(event)
        match event.char:
            case "\x1b":
                self.quit()
            case "q":
                self.reset_board()

    # TODO: Clear slaves of board's Frames' [Labels]
    # TODO: Add dot (circle) object on board to show moves
    def reset_board(self):
        self.board = Board(self.theme)

    def display_board(self):
        for piece in self.board.pieces.values():
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
                command=self.get_valid_moves_for_this_piece(piece.row, piece.col),
            )
            button.grid(row=piece.row, column=piece.col)

    def get_valid_moves_for_this_piece(self, row, col):
        def custom_function():
            print(self.board.get_valid_moves(row, col))

        return custom_function
