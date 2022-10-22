import tkinter as tk


import chess
from .constants import THEME

class Root(tk.Tk):
    def __init__(self, theme: tuple[str, str]=THEME.RED, title="CHESS", icon="res/chess.ico", **kwargs):
        super().__init__(**kwargs)
        self._theme = theme
        self.title(title)
        self.iconbitmap(icon)

        # Bind event logic
        self.bind("<KeyPress>", self.keypress_handler, add=True)
        self._cb = chess.ChessBoard(self, theme)

    def keypress_handler(self, event):
        print(event)
        match event.char:
            case '\x1b':
                self.quit()
            case 'q':
                self.reset()

    def reset(self):
        self._cb.destroy()
        self._cb = chess.ChessBoard(self, self._theme)
