from __future__ import annotations

from itertools import product
from random import choices
from tkinter import Button, Event, Tk, Widget
from typing import Callable

from tksvg import SvgImage

from .board import Board
from .constants import SIZE, THEME
from .piece import COLOR_TYPE, PIECE_VAL, Piece
from .types import Position


class Root(Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title("CHESS")
        self.iconbitmap("res/chess.ico")

        self.IMG_DICT = {
            (type, color): SvgImage(
                file=f"res/{type}_{color}.svg", scaletowidth=SIZE.PIECE
            )
            for color, type in COLOR_TYPE
        }

        # Bind event logic
        self.bind("<Escape>", lambda e: self.quit())
        self.bind("<q>", lambda e: self.reset_board())

        self.setup_buttons()
        self.reset_board()

    def setup_buttons(self):
        for pos in product(range(8), range(8)):
            button = Button(
                self,
                bg=self.bg(pos),
                activebackground=THEME.ACTIVE_BG,
                bd=0,
                height=SIZE.TILE,
                width=SIZE.TILE,
            )
            on_click, on_enter, on_exit = self.bind_factory(pos)
            button.bind("<ButtonRelease-1>", on_click)
            button.bind("<Enter>", on_enter)
            button.bind("<Leave>", on_exit)

            button.grid(row=pos[0], column=pos[1])

    def move_piece(
        self,
        _from: Position,
        _to: Position,
        _extra_capture: Position | None = None,
        enpassant_target: Position | None = None,
        reset_counter: bool = False,
    ) -> None:
        piece = self.board[_from]

        self.board.remove(_from)
        self.refresh_piece(_from)

        self.board.place(Piece(_to, piece.color, piece.type))
        self.refresh_piece(_to)

        if _extra_capture:
            self.board.remove(_extra_capture)
            self.refresh_piece(_extra_capture)

        self.board.enpassant_target = enpassant_target

        if reset_counter:
            self.board.move_counter = 0

        self.board.move_counter += 1
        if self.board.move_counter >= 20:
            print("20 moves since last capture or pawn move!")
            ...  # TODO:draw! Ending game, check or checkmate

        self.board.toggle_color_turn()

    def bg(self, pos: Position) -> str:
        return (THEME.LIGHT_TILES, THEME.DARK_TILES)[sum(pos) % 2]

    def reset_board(self) -> None:
        self.board = Board()
        for pos in self.board.pieces:
            self.refresh_piece(pos)

    def btn(self, pos: Position) -> Widget:
        return self.grid_slaves(*pos)[0]

    def reset_btn_bg(self, pos: Position) -> None:
        self.btn(pos)["bg"] = self.bg(pos)

    def refresh_piece(self, pos: Position) -> None:
        piece = self.board[pos]
        self.btn(pos)["image"] = self.IMG_DICT[(piece.type, piece.color)]

    def bind_factory(
        self, pos: Position
    ) -> tuple[
        Callable[[Event], None], Callable[[Event], None], Callable[[Event], None]
    ]:
        def on_click(e: Event) -> None:

            if self.board[pos].color != self.board.color_turn:
                return
            valid_moves = self.board.get_valid_moves(pos)
            if not valid_moves:
                return
            # TODO: Choose movement by displacement of x,y moved
            weights = [PIECE_VAL[move._to_piece.type] for move in valid_moves]

            move = choices(valid_moves, weights)[0]
            self.move_piece(
                move._from,
                move._to,
                move._extra_capture,
                move.enpassant_target,
                move.reset_counter,
            )

            for move in valid_moves:
                self.reset_btn_bg(move._to)

        def on_enter(e: Event) -> None:
            if self.board[pos].color != self.board.color_turn:
                return
            valid_moves = self.board.get_valid_moves(pos)
            if not valid_moves:
                self.btn(pos)["bg"] = THEME.INVALID_TILE

            for move in valid_moves:
                btn = self.btn(move._to)
                btn["bg"] = THEME.VALID_HIGHLIGHT

        def on_exit(e: Event) -> None:
            if not self.board[pos]:
                return
            valid_moves = self.board.get_valid_moves(pos)
            if not valid_moves:
                self.reset_btn_bg(pos)

            for move in valid_moves:
                self.reset_btn_bg(move._to)

        return on_click, on_enter, on_exit
