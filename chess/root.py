from __future__ import annotations

from itertools import product
from random import choice
from tkinter import Button, Event, Tk
from typing import Callable

from tksvg import SvgImage

from .board import Board
from .constants import PIECE_SIZE, THEME_RED, TILE_SIZE
from .piece import COLOR_STR, Piece
from .types import ColorPair, Position


class Root(Tk):
    def __init__(self, theme: ColorPair = THEME_RED) -> None:
        super().__init__()
        self.imgs = []
        self.theme = theme

        self.title("CHESS")
        self.iconbitmap("res/chess.ico")

        # Bind event logic
        self.bind("<KeyPress>", self.keypress_handler, add=True)
        self.reset_board()

    def keypress_handler(self, event: Event) -> None:
        print(event)
        match event.char:
            case "\x1b":
                self.quit()
            case "q":
                self.reset_board()

    # account for empassant
    def move_piece(
        self,
        _from: Position,
        _to: Position,
        _extra_capture: Position | None = None,
        enpassant_target: Position | None = None,
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

        # add additional flag: reset when pawn moves is made or capture
        
        if reset:=True:
            self.board.fifty_move_counter = 0
        self.board.fifty_move_counter += 1
        if self.board.fifty_move_counter >= 50:
            ... #draw! Ending game, check or checkmate
        
        self.board.toggle_color_turn()

    def calibrate_btn_cmd(self, pos: Position) -> Callable[[], None]:
        def btn_cmd() -> None:
            valid_moves = self.board.get_valid_moves(pos)
            if not valid_moves:
                return
            move = choice(valid_moves)
            self.move_piece(pos, move._to, move._extra_capture, move.enpassant_target)

        return btn_cmd

    def reset_board(self) -> None:
        self.board = Board(self.theme)
        self.refresh_board()

    def refresh_piece(self, pos: Position) -> None:
        [slave.destroy() for slave in self.grid_slaves(*pos)]
        piece = self.board.piece(pos)
        bg = self.theme[sum(pos) % 2]

        img = SvgImage(
            file=f"res/{piece.type}_{COLOR_STR[piece.color]}.svg",
            scaletowidth=PIECE_SIZE,
        )
        self.imgs.append(img)
        # Might one day want to append to board for garbage collection
        command = self.calibrate_btn_cmd(pos)
        Button(
            self,
            image=img,
            bg=bg,
            activebackground=bg,
            bd=0,
            height=TILE_SIZE,
            width=TILE_SIZE,
            command=command,
        ).grid(row=pos[0], column=pos[1])

    # iterate over board
    def refresh_board(self):
        for pos in product(range(8), repeat=2):
            self.refresh_piece(pos)

    # account for empassant
