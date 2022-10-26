from __future__ import annotations

import itertools
from itertools import chain, product
from random import choice
from tkinter import Button, Event, Tk, Widget
from typing import Callable

from tksvg import SvgImage

from .board import Board
from .constants import PIECE_SIZE, THEME_RED, TILE_SIZE
from .piece import Piece, PieceColor, PieceType
from .types import ColorPair, Position

type_color = [
    (PieceType.EMPTY, PieceColor.NONE),
    (PieceType.PAWN, PieceColor.BLACK),
    (PieceType.KNIGHT, PieceColor.BLACK),
    (PieceType.BISHOP, PieceColor.BLACK),
    (PieceType.ROOK, PieceColor.BLACK),
    (PieceType.QUEEN, PieceColor.BLACK),
    (PieceType.KING, PieceColor.BLACK),
    (PieceType.PAWN, PieceColor.WHITE),
    (PieceType.KNIGHT, PieceColor.WHITE),
    (PieceType.BISHOP, PieceColor.WHITE),
    (PieceType.ROOK, PieceColor.WHITE),
    (PieceType.QUEEN, PieceColor.WHITE),
    (PieceType.KING, PieceColor.WHITE),
]


class Root(Tk):
    def __init__(self, theme: ColorPair = THEME_RED) -> None:
        super().__init__()

        self.theme = theme

        self.title("CHESS")
        self.iconbitmap("res/chess.ico")

        self.IMG_DICT = {
            (type, color): SvgImage(
                file=f"res/{type}_{color}.svg", scaletowidth=PIECE_SIZE
            )
            for type, color in type_color
        }

        # Bind event logic
        self.bind("<Escape>", lambda e: self.quit())
        self.bind("<q>", lambda e: self.reset_board())

        self.setup_buttons()
        self.reset_board()
    def setup_buttons(self):
        for pos in product(range(8), range(8)):
            on_click, on_enter, on_exit = self.bind_factory(pos)

            button = Button(
                self,
                bg=self.theme[sum(pos) % 2],
                activebackground="white",
                bd=0,
                height=TILE_SIZE,
                width=TILE_SIZE,
                command=on_click,
            )

            button.bind("<Enter>", on_enter)
            button.bind("<Leave>", on_exit)

            button.grid(row=pos[0], column=pos[1])
    # account for empassant
    def move_piece(
        self,
        _from: Position,
        _to: Position,
        _extra_capture: Position | None = None,
        enpassant_target: Position | None = None,

        reset_counter: bool = False,
    ) -> None:
        piece = self.board.piece(_from)

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
            ...  # draw! Ending game, check or checkmate

        self.board.toggle_color_turn()

    def reset_board(self) -> None:
        self.board = Board(self.theme)
        for pos in self.board.pieces:
            self.refresh_piece(pos)

    def btn(self, pos: Position) -> Widget:
        return self.grid_slaves(*pos)[0]
        # iterate over board

    def refresh_piece(self, pos: Position) -> None:
        piece = self.board.piece(pos)
        self.btn(pos)["image"] = self.IMG_DICT[(piece.type, piece.color)]

    def bind_factory(
        self, pos: Position
    ) -> tuple[Callable[[], None], Callable[[Event], None], Callable[[Event], None]]:
        def on_click() -> None:
            if not self.board.piece(pos):
                return
            valid_moves = self.board.get_valid_moves(pos)
            if not valid_moves:
                return
            move = choice(valid_moves)
            self.move_piece(
                move._from,
                move._to,
                move._extra_capture,
                move.enpassant_target,
                move.reset_counter,
            )
            flattened = [
                btn
                for sublist in [self.grid_slaves(*move._to) for move in valid_moves]
                for btn in sublist
            ]
            for btn, move in zip(flattened, valid_moves):
                bg = self.theme[sum(move._to) % 2]
                btn["background"] = bg
            # TODO: add unhighlighting here
            # TODO: create method to find button object, refactor existing function

        # FIXME: After clicking there is a bug where tiles dont turn back into color

        def on_enter(e: Event) -> None:
            if not self.board.piece(pos):
                return
            if self.board.piece(pos).color != self.board.color_turn:
                return
            valid_moves = self.board.get_valid_moves(pos)
            if not valid_moves:
                btn = self.grid_slaves(*pos)[0]
                btn["background"] = "#f54842"
            # FIXME
            # TODO: Convert clicker to event handler, add more event handlers with click in and click out
            flattened = [
                btn
                for sublist in [self.grid_slaves(*move._to) for move in valid_moves]
                for btn in sublist
            ]
            for btn in flattened:
                # TODO: bring these to constants, game colors
                btn["background"] = "white"
            # TODO: Add hover for invalid button["bg"] == "white"
            # TODO: add method for getting button element with self.gridslaves

        def on_exit(e: Event) -> None:
            if not self.board.piece(pos):
                return
            valid_moves = self.board.get_valid_moves(pos)
            if not valid_moves:
                btn = self.grid_slaves(*pos)[0]
                bg = self.theme[sum(pos) % 2]
                # TODO: get tile color property
                btn["background"] = bg

            flattened = [
                btn
                for sublist in [self.grid_slaves(*move._to) for move in valid_moves]
                for btn in sublist
            ]
            for btn, move in zip(flattened, valid_moves):
                bg = self.theme[sum(move._to) % 2]
                btn["background"] = bg

        return on_click, on_enter, on_exit
