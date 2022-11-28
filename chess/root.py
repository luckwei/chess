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


class State(Enum):
    DEFAULT = auto()
    CAPTURABLE = auto()
    MOVABLE = auto()
    SELECTED = auto()


class Display(Tk):
    def __init__(self) -> None:
        super().__init__()
        self.__IMG_DICT = {
            (type, color): SvgImage(
                file=f"res/{type.__name__.lower()}_{color}.svg", scaletowidth=SIZE.PIECE
            )
            for color, type in FEN_MAP.values()
        }

    def btns(self):
        print(self.grid_slaves())
        return self.grid_slaves()

    def btn(self, pos: Position) -> Widget:
        return self.grid_slaves(*pos)[0]

    def refresh_fg(self, pos: Position, piece: Piece = Empty()) -> None:
        self.btn(pos)["image"] = self.__IMG_DICT[type(piece), piece.color]

    def refresh_bg(self, pos: Position, state: State = State.DEFAULT) -> None:
        STATE_BG_DICT = {
            State.CAPTURABLE: THEME.VALID_CAPTURE,
            State.MOVABLE: THEME.VALID_HIGHLIGHT_DARK
            if sum(pos) % 2
            else THEME.VALID_HIGHLIGHT_LIGHT,
            State.SELECTED: THEME.ACTIVE_BG,
            State.DEFAULT: THEME.LIGHT_TILES if sum(pos) % 2 == 0 else THEME.DARK_TILES,
        }
        self.btn(pos)["bg"] = STATE_BG_DICT.get(state, THEME.LIGHT_TILES)


class Root(Display):
    def __init__(self):
        super().__init__()
        self.title("CHESS")
        self.iconbitmap("res/chess.ico")

        self.board = Board()
        self.selected_pos: Position | None = None
        self.setup_buttons()
        self.setup_board()

        # Bind event logic
        self.bind("<Escape>", lambda e: self.quit())
        # self.bind("<q>", lambda e: self.reset())

    def setup_board(self) -> None:
        for pos, piece in self.board.items():
            # SET FOREGROUND BACKGROUND
            self.refresh_fg(pos, piece)
            self.refresh_bg(pos)

    def setup_buttons(self):
        def __bind_factory(pos: Position):
            def on_click(e: Event) -> None:
                selected_pos = self.selected_pos
                all_moves = self.board.all_moves

                # There was a selected move previously
                if selected_pos:
                    self.refresh_bg(selected_pos)

                    for move in all_moves[selected_pos]:
                        self.refresh_bg(move)
                    # Check all moves
                    for move in all_moves[selected_pos]:
                        to, flag = move, move.flag

                        if pos == self.selected_pos:
                            self.selected_pos = None
                            return

                        if pos == to:
                            self.board.execute_move(selected_pos, to, flag)
                            self.selected_pos = None
                            return
                # No selected move previously, also an unmovable tile
                if pos not in all_moves:
                    return

                self.refresh_bg(pos, State.SELECTED)
                for move in all_moves[pos]:
                    self.refresh_bg(
                        move,
                        State.CAPTURABLE if self.board[move] else State.MOVABLE,
                    )

                self.selected_pos = pos

            def on_enter(e: Event) -> None:
                selected_pos = self.selected_pos
                all_moves = self.board.all_moves

                if selected_pos or pos not in all_moves:
                    return

                for move in all_moves[pos]:
                    self.refresh_bg(
                        move,
                        State.CAPTURABLE if self.board[move] else State.MOVABLE,
                    )

            def on_exit(e: Event) -> None:
                selected_pos = self.selected_pos
                all_moves = self.board.all_moves

                if selected_pos or pos not in all_moves:
                    return

                self.refresh_bg(pos)

                for move in all_moves[pos]:
                    self.refresh_bg(move)

            return on_click, on_enter, on_exit

        for pos in product(range(8), range(8)):
            button = Button(
                self,
                activebackground=THEME.ACTIVE_BG,
                bd=0,
                height=SIZE.TILE,
                width=SIZE.TILE,
            )
            on_click, on_enter, on_exit = __bind_factory(pos)
            button.bind("<ButtonRelease-1>", on_click)
            button.bind("<Enter>", on_enter)
            button.bind("<Leave>", on_exit)

            button.grid(row=pos[0], column=pos[1])
            self.refresh_bg(pos)
