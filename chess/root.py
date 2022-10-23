from __future__ import annotations

import tkinter as tk

from .board import Board
from .constants import THEME, TILE_SIZE


class Root(tk.Tk):
    def __init__(
        self,
        theme: tuple[str, str] = THEME.RED,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.theme = theme
        self.title("CHESS")
        self.iconbitmap("res/chess.ico")

        # Bind event logic
        self.bind("<KeyPress>", self.keypress_handler, add=True)
        self.board = Board(theme)
        self.display_board()
        self.mainloop()

    def keypress_handler(self, event):
        print(event)
        match event.char:
            case "\x1b":
                self.quit()
            case "q":
                self.reset()

    def reset(self):
        self.board = Board(self.theme)
        
    def display_board(self):
        self.board.show_as_frame(self)
        
        
        
        
        
