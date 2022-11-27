from __future__ import annotations

from enum import Enum, auto
from itertools import product
from tkinter import Button, Event, Tk, Widget
from tkinter.messagebox import showinfo
from typing import Callable

from tksvg import SvgImage

from .constants import SIZE, THEME
from .game import COLOR_TYPE, Color, Empty, Flag, Game, Move
from .setup import Setup
from .types import Position

# from playsound import playsound


class State(Enum):
    DEFAULT = auto()
    CAPTURABLE = auto()
    MOVABLE = auto()
    SELECTED = auto()


class Root(Tk):
    def __init__(self) -> None:
        super().__init__()

        self.__IMG_DICT = {
            (type, color): SvgImage(
                file=f"res/{type.__name__.lower()}_{color}.svg", scaletowidth=SIZE.PIECE
            )
            for color, type in COLOR_TYPE
        }
        self.title("CHESS")
        self.iconbitmap("res/chess.ico")

        # Bind event logic
        self.bind("<Escape>", lambda e: self.quit())
        self.bind("<q>", lambda e: self.reset())

        self.setup_buttons()
        self.game = Game.from_fen(Setup.START)

        self.selected_pos = None

    @property
    def candidates(self) -> list[Move]:
        return self._candidates

    @candidates.setter
    def candidates(self, moves) -> None:
        self._candidates = moves

    @candidates.deleter
    def candidates(self) -> None:
        self.candidates = []
        self.selected_pos = None

    def setup_buttons(self):
        for pos in product(range(8), range(8)):
            button = Button(
                self,
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
            self.reset_bg(pos)

    def move_piece(self, frm: Position, to: Position, flag: Flag = Flag.NONE) -> None:
        def single_move(frm: Position, to: Position) -> None:
            self.game[to] = self.game[frm]
            del self[frm]

        match flag:
            case Flag.CASTLE_LONG:
                row = 7 if self.game.color_to_move == Color.WHITE else 0
                single_move((row, 0), (row, 3))
                self.game.castling_flags[self.game.color_to_move] = [False, False]

            case Flag.CASTLE_SHORT:
                row = 7 if self.game.color_to_move == Color.WHITE else 0
                single_move((row, 7), (row, 5))
                self.game.castling_flags[self.game.color_to_move] = [False, False]

            case Flag.LOSE_KING_PRIV:
                self.game.castling_flags[self.game.color_to_move] = [False, False]
            case Flag.LOSE_ROOK_PRIV:
                row = 7 if self.game.color_to_move == Color.WHITE else 0
                if frm == (row, 0):
                    self.game.castling_flags[self.game.color_to_move][0] = False
                if frm == (row, 7):
                    self.game.castling_flags[self.game.color_to_move][1] = False

            case Flag.ENPASSANT:
                del self[self.game.enpassant_target]

        self.game.enpassant_target = to if flag == Flag.ENPASSANT_TRGT else None

        single_move(frm, to)

        # TODO: PROMOTION LOGIC
        # TODO:UNDO MOVE

        # TODO: CHECKS WILL alert the user
        self.game.toggle_color_turn()

        # TODO: ADD SOUNDS!
        if self.game.checked:
            print("CHECKED!")

        if self.game.checkmated:
            print("CHECKMATE!")
            showinfo(
                "Game ended!",
                f"{self.game.color_to_move.other} WINS by CHECKMATE!\nPress q to start new game..",
            )

        if self.game.stalemated:
            print("STALEMATE!")
            showinfo("Game ended!", f"DRAW BY STALMATE!\nPress q to start new game..")

    def __setitem__(self, pos: Position, piece: Empty) -> None:
        self.game[pos] = piece
        self.btn(pos)["image"] = self.__IMG_DICT[type(piece), piece.color]

    def __delitem__(self, pos: Position | None) -> None:
        if pos is None:
            return
        del self.game[pos]
        self.btn(pos)["image"] = self.__IMG_DICT[Empty, Color.NONE]

    # TODO: AT END/START OF EVERY MOVE FIND ALL POSSIBLE MOVES PLACE THEM IN A dict[Position, list[Move]] and use checking to see hover and clicking logic
    # STALEMATE/CHECKMATE LOGIC, check logic is just seeing whether king is under attack currently using
    # not KingChecks.safe(self.game.color_to_move)

    def reset_bg(self, pos: Position, state: State = State.DEFAULT) -> None:
        match state:
            case State.CAPTURABLE:
                bg = THEME.VALID_CAPTURE
            case State.MOVABLE:
                bg = (
                    THEME.VALID_HIGHLIGHT_DARK
                    if sum(pos) % 2
                    else THEME.VALID_HIGHLIGHT_LIGHT
                )
            case State.SELECTED:
                bg = THEME.ACTIVE_BG
            case _:
                bg = THEME.LIGHT_TILES if sum(pos) % 2 == 0 else THEME.DARK_TILES
        self.btn(pos)["bg"] = bg

    @property
    def game(self) -> Game:
        return self._game

    @game.setter
    def game(self, game: Game) -> None:
        self._game = game
        for pos, piece in self.game.board.items():
            self.btn(pos)["image"] = self.__IMG_DICT[type(piece), piece.color]
            self.reset_bg(pos)

    def reset(self) -> None:
        self.game = Game()
        self.selected_pos = None

    def btn(self, pos: Position) -> Widget:
        return self.grid_slaves(*pos)[0]

    def __bind_factory(
        self, pos: Position
    ) -> tuple[
        Callable[[Event], None], Callable[[Event], None], Callable[[Event], None]
    ]:
        def on_click(e: Event) -> None:

            # There was a selected move previously
            if self.selected_pos:
                self.reset_bg(self.selected_pos)

                for move in self.game.all_moves[self.selected_pos]:
                    to = move
                    self.reset_bg(to)
                # Check all moves
                for move in self.game.all_moves[self.selected_pos]:
                    to, flag = move, move.flag

                    if pos == self.selected_pos:

                        self.selected_pos = None
                        return
                    # If clicked is same as move execute it and return
                    if pos == to:
                        # playsound("res/sound/s1.wav", False)

                        self.move_piece(self.selected_pos, to, flag)

                        self.selected_pos = None
                        return

            if pos not in self.game.all_moves:
                return

            self.reset_bg(pos, State.SELECTED)
            for move in self.game.all_moves[pos]:
                self.reset_bg(
                    move, State.CAPTURABLE if self.game[move] else State.MOVABLE
                )

            self.selected_pos = pos

        def on_enter(e: Event) -> None:
            if self.selected_pos:
                return

            if pos not in self.game.all_moves:
                return

            for move in self.game.all_moves[pos]:
                self.reset_bg(
                    move, State.CAPTURABLE if self.game[move] else State.MOVABLE
                )

        def on_exit(e: Event) -> None:
            if self.selected_pos:
                return

            if pos not in self.game.all_moves:
                return

            self.reset_bg(pos)

            for move in self.game.all_moves[pos]:
                self.reset_bg(move)

        return on_click, on_enter, on_exit
