from __future__ import annotations

from enum import Enum, auto
from itertools import product
from tkinter import Button, Event, Tk, Widget
from tkinter.messagebox import showinfo
from typing import Callable

from tksvg import SvgImage

from .constants import SIZE, THEME
from .game import FEN_MAP, Board, Empty, Piece
from .setup import Setup
from .types import Position


# from playsound import playsound
def light_tile(pos: Position) -> bool:
    return sum(pos) % 2 == 0


class State(Enum):
    DEFAULT = auto()
    CAPTURABLE = auto()
    MOVABLE = auto()
    SELECTED = auto()


class Display(Tk):
    def __init__(self) -> None:
        super().__init__()
        self.btns: dict[Position, Widget] = {}
        self.setup_buttons()
        self.__IMG_DICT = {
            (type, color): SvgImage(
                file=f"res/{type.__name__.lower()}_{color}.svg", scaletowidth=SIZE.PIECE
            )
            for color, type in FEN_MAP.values()
        }

    def setup_buttons(self):
        for pos in product(range(8), range(8)):
            button = Button(
                self,
                activebackground=THEME.ACTIVE_BG,
                bd=0,
                height=SIZE.TILE,
                width=SIZE.TILE,
            )
            self.btns[pos] = button
            button.grid(row=pos[0], column=pos[1])
            self.refresh_bg(pos)

    def refresh_fg(self, pos: Position, piece: Piece = Empty()) -> None:

        self.btns[pos]["image"] = self.__IMG_DICT[type(piece), piece.color]

    def refresh_bg(self, pos: Position, state: State = State.DEFAULT) -> None:
        STATE_BG_DICT = {
            State.CAPTURABLE: THEME.VALID_CAPTURE,
            State.MOVABLE: THEME.VALID_HIGHLIGHT_LIGHT
            if light_tile(pos)
            else THEME.VALID_HIGHLIGHT_DARK,
            State.SELECTED: THEME.ACTIVE_BG,
            State.DEFAULT: THEME.LIGHT_TILES if light_tile(pos) else THEME.DARK_TILES,
        }
        self.btns[pos]["bg"] = STATE_BG_DICT.get(
            state, THEME.LIGHT_TILES if light_tile(pos) else THEME.DARK_TILES
        )


class Root(Display):
    def __init__(self):
        super().__init__()
        self.title("CHESS")
        self.iconbitmap("res/chess.ico")

        self.board = Board()
        self.refresh_pieces()
        self.selected: Position | None = None

        self.bind_buttons()

        # Bind event logic
        self.bind("<Escape>", lambda e: self.quit())
        # self.bind("<q>", lambda e: self.reset())
    
    def refresh_pieces(self) -> None:
        for pos, piece in self.board.items():
            self.refresh_fg(pos, piece)
            
    def check_for_end(self):
        if self.board.checked():
            print("CHECKED!")

        if self.board.checkmated():
            print("CHECKMATE!")
            showinfo(
                "Game ended!",
                f"{self.board.color_move.other} WINS by CHECKMATE!\nPress q to start new game..",
            )

        if self.board.stalemated():
            print("STALEMATE!")
            showinfo("Game ended!", f"DRAW BY STALMATE!\nPress q to start new game..")
            
    #FIXME: bugs on castling 
    def bind_buttons(self):
        def contiguous_reset_bg(pos: Position):
            self.refresh_bg(pos)
            for move in self.board.all_moves[pos]:
                self.refresh_bg(move)

        def __bind_factory(pos: Position):
            def on_click(e: Event) -> None:
                selected = self.selected
                all_moves = self.board.all_moves

                # There was a selected move previously
                if selected:
                    contiguous_reset_bg(selected)
                    # Check all moves
                    for move in all_moves[selected]:

                        if pos == selected:
                            self.selected = None
                            return

                        if pos == move:
                            self.board.execute_move(selected, move)
                            self.refresh_pieces()
                            self.check_for_end()
                            self.selected = None
                            return
                    self.selected = None
                # No selected move previously, also an unmovable tile
                if pos not in all_moves:
                    return

                # Tile is valid, so select it
                for move in all_moves[pos]:
                    self.refresh_bg(
                        move,
                        State.CAPTURABLE if self.board[move] else State.MOVABLE,
                    )

                self.refresh_bg(pos, State.SELECTED)
                self.selected = pos

            def on_enter(e: Event) -> None:
                selected_pos = self.selected
                all_moves = self.board.all_moves

                if selected_pos or pos not in all_moves:
                    return

                self.refresh_bg(pos, State.SELECTED)
                for move in all_moves[pos]:
                    self.refresh_bg(
                        move,
                        State.CAPTURABLE if self.board[move] else State.MOVABLE,
                    )

            def on_exit(e: Event) -> None:
                selected_pos = self.selected
                all_moves = self.board.all_moves

                if selected_pos or pos not in all_moves:
                    return

                contiguous_reset_bg(pos)

            return on_click, on_enter, on_exit

        for pos, btn in self.btns.items():
            on_click, on_enter, on_exit = __bind_factory(pos)
            btn.bind("<ButtonRelease-1>", on_click)
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_exit)
