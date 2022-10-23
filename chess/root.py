from __future__ import annotations

from tkinter import Tk, Event

from .board import Board
from .constants import THEME


class Root(Tk):
    def __init__(self, theme: tuple[str, str] = THEME.RED):
        super().__init__()
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
        self.board.show_as_frame(self)
