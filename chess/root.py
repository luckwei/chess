from __future__ import annotations

from enum import Enum, auto
from itertools import product
from tkinter import Button, Event, Tk
from tkinter.messagebox import showinfo
from typing import Type

from tksvg import SvgImage

from .constants import SIZE, THEME
from .game import FEN_MAP, Board, Color, Empty, Move, PieceTypeColor
from .types import Position


# from playsound import playsound
def light_tile(pos: Position) -> bool:
    return sum(pos) % 2 == 0


class State(Enum):
    DEFAULT = auto()
    CAPTURABLE = auto()
    MOVABLE = auto()
    SELECTED = auto()
    KING_CHECK =auto()


class CachedBtn(Button):
    def __init__(
        self, master: Display, pos: Position, piece_imgs: dict[PieceTypeColor, SvgImage]
    ):
        super().__init__(
            master,
            activebackground=THEME.ACTIVE_BG,
            bd=0,
            height=SIZE.TILE,
            width=SIZE.TILE,
        )
        self.state_bg_dict = {
            State.KING_CHECK: THEME.VALID_CAPTURE,
            State.CAPTURABLE: THEME.VALID_CAPTURE,
            State.MOVABLE: THEME.VALID_HIGHLIGHT_LIGHT
            if light_tile(pos)
            else THEME.VALID_HIGHLIGHT_DARK,
            State.SELECTED: THEME.ACTIVE_BG,
            State.DEFAULT: THEME.LIGHT_TILES if light_tile(pos) else THEME.DARK_TILES,
        }
        self.PIECE_IMGS = piece_imgs
        self.piece_type_color = Empty, Color.NONE
        self.state = State.DEFAULT

    @property
    def piece_type_color(self) -> PieceTypeColor:
        return self._piece_type_color

    @piece_type_color.setter
    def piece_type_color(self, new_type_color: PieceTypeColor):
        self._piece_type_color = new_type_color
        self["image"] = self.PIECE_IMGS[new_type_color]

    @piece_type_color.deleter
    def piece_type_color(self):
        if self.piece_type_color != (Empty, Color.NONE):
            self.piece_type_color = Empty, Color.NONE

    @property
    def state(self) -> State:
        return self._state

    @state.setter
    def state(self, new_state: State):
        self._state = new_state
        self["bg"] = self.state_bg_dict[new_state]

    @state.deleter
    def state(self):
        if self.state != State.DEFAULT:
            self.state = State.DEFAULT


class Display(Tk):
    def __init__(self) -> None:
        super().__init__()
        self.PIECE_IMGS: dict[PieceTypeColor, SvgImage] = {
            (PieceType, color): SvgImage(
                file=f"res/{PieceType.__name__}_{color}.svg",
                scaletowidth=SIZE.PIECE,
            )
            for PieceType, color in FEN_MAP.values()
        }
        self.btns: dict[Position, CachedBtn] = {}
        self.setup_buttons()

    def setup_buttons(self):
        for pos in product(range(8), range(8)):
            self.btns[pos] = (btn := CachedBtn(self, pos, self.PIECE_IMGS))
            btn.grid(row=pos[0], column=pos[1])


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
        self.bind("<q>", lambda e: self.reset())

    def reset(self) -> None:
        for btn in self.btns.values():
            del btn.state
        self.board.set_from_fen("6k1/Np2P2R/p6B/K1P2Np1/1p3P2/P2p4/8/3n3R w - - 0 1")
        self.refresh_pieces()

    def refresh_pieces(self) -> None:
        btns = self.btns
        for pos, piece in self.board.items():
            if btns[pos].piece_type_color != piece.type_color:
                btns[pos].piece_type_color = piece.type_color

    def execute_move_root(self, pos: Position, move: Move) -> None:
        board = self.board
        color = board.color_move
        board.execute_move(pos, move)
        self.refresh_pieces()

        if board.checked:
            self.btns[board.find_king(color.other)].state = State.CAPTURABLE
            if board.checkmated:
                print("CHECKMATE!")
                showinfo("Game ended!", f"CHECKMATE: {color.upper()} WINS!")
                return
            print("CHECKED!")
            return

        if board.stalemated:
            print("STALEMATE!")
            showinfo("Game ended!", f"STALEMATE: DRAW!")
            return

    def bind_buttons(self):

        btns = self.btns
        board = self.board
        def __bind_factory(pos: Position):
            btn = btns[pos]
            
            def on_click(e: Event) -> None:
                selected = self.selected
                all_moves = board.all_moves

                # There was a selected move previously
                if selected:
                    self.selected = None  # Consume selection
                    
                    # Contiguous reset
                    del btns[selected].state
                    for move in all_moves[selected]:
                        del btns[move].state
                    # Check all moves
                    for move in all_moves[selected]:
                        if pos == selected:
                            return

                        if pos == move:
                            self.execute_move_root(selected, move)
                            return
                # No selected move previously, also an unmovable tile
                if board.checked:
                    btns[board.find_king()].state = State.KING_CHECK
                
                if pos not in all_moves:
                    return

                # Tile is valid, so select it
                for move in all_moves[pos]:
                    btns[move].state = (
                        State.CAPTURABLE if board[move] else State.MOVABLE
                    )

                btn.state = State.SELECTED
                self.selected = pos

            def on_enter(e: Event) -> None:
                all_moves = board.all_moves

                if self.selected or pos not in all_moves:
                    return
                
                btn.state = State.SELECTED

                for move in all_moves[pos]:
                    btns[move].state = (
                        State.CAPTURABLE if board[move] else State.MOVABLE
                    )

            def on_exit(e: Event) -> None:
                if self.selected or pos not in board.all_moves:
                    return
                if board.checked and pos==board.find_king():
                    btn.state = State.KING_CHECK
                else:
                    del btn.state
                for move in board.all_moves[pos]:
                    del btns[move].state


            return on_click, on_enter, on_exit

        for pos, btn in btns.items():
            on_click, on_enter, on_exit = __bind_factory(pos)
            btn.bind("<ButtonRelease-1>", on_click)
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_exit)
