from __future__ import annotations

from itertools import chain, product
import itertools
from random import choice
from tkinter import Button, Event, Tk
from typing import Callable

from tksvg import SvgImage

from .board import Board
from .constants import PIECE_SIZE, THEME_RED, TILE_SIZE
from .piece import Piece
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
        if self.board.move_counter >= 50:
            ...  # draw! Ending game, check or checkmate

        self.board.toggle_color_turn()

    def reset_board(self) -> None:
        self.board = Board(self.theme)
        self.refresh_board()

    def refresh_piece(self, pos: Position) -> None:
        piece = self.board.piece(pos)
        bg = self.theme[sum(pos) % 2]

        img = SvgImage(
            file=f"res/{piece.type}_{piece.color}.svg",
            scaletowidth=PIECE_SIZE,
        )
        self.imgs.append(img)
        # Might one day want to append to board for garbage collection
        [slave.destroy() for slave in self.grid_slaves(*pos)]
        on_click, on_enter, on_exit = self.bind_factory(pos)
        button = Button(
            self,
            image=img,
            bg=bg,
            activebackground="white",
            bd=0,
            height=TILE_SIZE,
            width=TILE_SIZE,
            command=on_click,
        )
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_exit)
        button.grid(row=pos[0], column=pos[1])
        # TODO: Implement hover for button
    
    def bind_factory(self, pos: Position) -> tuple[Callable[[], None],Callable[[Event], None], Callable[[Event], None]]:
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
            flattened = [btn for sublist in [self.grid_slaves(*move._to) for move in valid_moves] for btn in sublist]
            for btn, move in zip(flattened, valid_moves):
                bg = self.theme[sum(move._to) % 2]
                btn["background"] = bg
            #TODO: add unhighlighting here
            #TODO: create method to find button object, refactor existing function
    #FIXME: After clicking there is a bug where tiles dont turn back into color
    
        def on_enter(e: Event) -> None:
            if not self.board.piece(pos):
                return
            valid_moves = self.board.get_valid_moves(pos)
            if not valid_moves:
                btn = self.grid_slaves(*pos)[0]
                btn["background"] = "#f54842"
            # FIXME
        # TODO: Convert clicker to event handler, add more event handlers with click in and click out
            flattened = [btn for sublist in [self.grid_slaves(*move._to) for move in valid_moves] for btn in sublist]
            for btn in flattened:
                # TODO: bring these to constants, game colors
                btn["background"] = "white"
            #TODO: Add hover for invalid button["bg"] == "white"
            # TODO: add method for getting button element with self.gridslaves
            

        def on_exit(e: Event)-> None:
            if not self.board.piece(pos):
                return
            valid_moves = self.board.get_valid_moves(pos)
            if not valid_moves:
                btn = self.grid_slaves(*pos)[0]
                bg = self.theme[sum(pos)%2]
                #TODO: get tile color property
                btn["background"] = bg

            flattened = [btn for sublist in [self.grid_slaves(*move._to) for move in valid_moves] for btn in sublist]
            for btn, move in zip(flattened, valid_moves):
                bg = self.theme[sum(move._to) % 2]
                btn["background"] = bg

            
        
        return on_click, on_enter, on_exit
    


    # iterate over board
    def refresh_board(self):
        for pos in product(range(8), repeat=2):
            self.refresh_piece(pos)

    # account for empassant
