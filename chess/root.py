from __future__ import annotations

from enum import Enum, auto
from itertools import product
from tkinter import Button, Event, Tk, Widget
from tkinter.messagebox import showinfo
from typing import Callable

from tksvg import SvgImage

from .constants import SIZE, THEME
from .game import FEN_MAP, Board, Color, Empty, Flag
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
        self.title("CHESS")
        self.iconbitmap("res/chess.ico")

        # Bind event logic
        self.bind("<Escape>", lambda e: self.quit())
        self.bind("<q>", lambda e: self.reset())

        self.selected_pos: Position | None = None

    def reset(self) -> None:
        self.selected_pos = None

    def __setitem__(self, pos: Position, piece: Empty) -> None:
        self.btn(pos)["image"] = self.__IMG_DICT[type(piece), piece.color]

    def __delitem__(self, pos: Position | None) -> None:
        if pos is None:
            return
        self.btn(pos)["image"] = self.__IMG_DICT[Empty, Color.NONE]

    def set_board(self, board: Board) -> None:
        for pos, piece in board.items():
            # SET FOREGROUND BACKGROUND
            self.btn(pos)["image"] = self.__IMG_DICT[type(piece), piece.color]
            self.reset_bg(pos)

    def btns(self):
        print(self.grid_slaves())
        return self.grid_slaves()

    def btn(self, pos: Position) -> Widget:

        return self.grid_slaves(*pos)[0]

    def reset_bg(self, pos: Position, state: State = State.DEFAULT) -> None:
        STATE_BG_DICT = {
            State.CAPTURABLE: THEME.VALID_CAPTURE,
            State.MOVABLE: THEME.VALID_HIGHLIGHT_DARK
            if sum(pos) % 2
            else THEME.VALID_HIGHLIGHT_LIGHT,
            State.SELECTED: THEME.ACTIVE_BG,
        }
        self.btn(pos)["bg"] = STATE_BG_DICT.get(
            state, THEME.LIGHT_TILES if sum(pos) % 2 == 0 else THEME.DARK_TILES
        )


class Game_Engine:
    def __init__(self) -> None:
        self.board = Board.from_fen(Setup.START)

    def reset(self) -> None:
        self.board = Board.from_fen(Setup.START)

    def __setitem__(self, pos: Position, piece: Empty) -> None:
        self.board[pos] = piece

    def __delitem__(self, pos: Position) -> None:
        del self.board[pos]

    def move_piece(self, frm: Position, to: Position, flag: Flag = Flag.NONE) -> None:
        if self.board.checked:
            print("CHECKED!")

        if self.board.checkmated:
            print("CHECKMATE!")
            showinfo(
                "Game ended!",
                f"{self.board.color_to_move.other} WINS by CHECKMATE!\nPress q to start new game..",
            )

        if self.board.stalemated:
            print("STALEMATE!")
            showinfo("Game ended!", f"DRAW BY STALMATE!\nPress q to start new game..")

        match flag:
            case Flag.CASTLE_LONG:
                row = 7 if self.board.color_to_move == Color.WHITE else 0
                self.board.single_move((row, 0), (row, 3))
                self.board.castling_flags[self.board.color_to_move] = [False, False]

            case Flag.CASTLE_SHORT:
                row = 7 if self.board.color_to_move == Color.WHITE else 0
                self.board.single_move((row, 7), (row, 5))
                self.board.castling_flags[self.board.color_to_move] = [False, False]

            case Flag.LOSE_KING_PRIV:
                self.board.castling_flags[self.board.color_to_move] = [False, False]
            case Flag.LOSE_ROOK_PRIV:
                row = 7 if self.board.color_to_move == Color.WHITE else 0
                if frm == (row, 0):
                    self.board.castling_flags[self.board.color_to_move][0] = False
                if frm == (row, 7):
                    self.board.castling_flags[self.board.color_to_move][1] = False

            case Flag.ENPASSANT:
                if self.board.enpassant_target:
                    del self.board[self.board.enpassant_target]

        self.board.enpassant_target = to if flag == Flag.ENPASSANT_TRGT else None

        self.board.single_move(frm, to)

        self.board.toggle_color_turn()
        # TODO: PROMOTION LOGIC
        # TODO:UNDO MOVE

        # TODO: CHECKS WILL alert the user

        # TODO: ADD SOUNDS!


class Root:
    def __init__(self):
        self.display = Display()
        self.game = Game_Engine()
        self.setup_buttons()

    def setup_buttons(self):
        for pos in product(range(8), range(8)):
            button = Button(
                self.display,
                activebackground=THEME.ACTIVE_BG,
                bd=0,
                height=SIZE.TILE,
                width=SIZE.TILE,
            )
            on_click, on_enter, on_exit = self.__bind_factory(pos)
            button.bind("<ButtonRelease-1>", on_click)
            button.bind("<Enter>", on_enter)
            button.bind("<Leave>", on_exit)

            button.grid(row=pos[0], column=pos[1])
            self.display.reset_bg(pos)

    def __bind_factory(
        self, pos: Position
    ) -> tuple[
        Callable[[Event], None], Callable[[Event], None], Callable[[Event], None]
    ]:
        def on_click(e: Event) -> None:

            # There was a selected move previously
            if self.display.selected_pos:
                self.display.reset_bg(self.display.selected_pos)

                for move in self.game.board.all_moves[self.display.selected_pos]:
                    to = move
                    self.display.reset_bg(to)
                # Check all moves
                for move in self.game.board.all_moves[self.display.selected_pos]:
                    to, flag = move, move.flag

                    if pos == self.display.selected_pos:

                        self.display.selected_pos = None
                        return
                    # If clicked is same as move execute it and return
                    if pos == to:
                        # playsound("res/sound/s1.wav", False)

                        self.game.move_piece(self.display.selected_pos, to, flag)

                        self.display.selected_pos = None
                        return

            if pos not in self.game.board.all_moves:
                return
            self.display.reset_bg(pos, State.SELECTED)
            for move in self.game.board.all_moves[pos]:
                self.display.reset_bg(
                    move, State.CAPTURABLE if self.game.board[move] else State.MOVABLE
                )

            self.display.selected_pos = pos

        def on_enter(e: Event) -> None:
            if self.display.selected_pos:
                return

            if pos not in self.game.board.all_moves:
                return

            for move in self.game.board.all_moves[pos]:
                self.display.reset_bg(
                    move, State.CAPTURABLE if self.game.board[move] else State.MOVABLE
                )

        def on_exit(e: Event) -> None:
            if self.display.selected_pos:
                return

            if pos not in self.game.board.all_moves:
                return

            self.display.reset_bg(pos)

            for move in self.game.board.all_moves[pos]:
                self.display.reset_bg(move)

        return on_click, on_enter, on_exit
    
