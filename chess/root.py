from __future__ import annotations

from itertools import product
from random import choices
from tkinter import Button, Event, Tk, Widget
from typing import Any, Callable

from tksvg import SvgImage

from .board import Board, Move
from .constants import SIZE, THEME
from .piece import COLOR_TYPE, PIECE_VAL, Piece, PieceColor, PieceType
from .types import Position


class Root(Tk):
    def __init__(self) -> None:
        super().__init__()

        self.__IMG_DICT = {
            (type, color): SvgImage(
                file=f"res/{type}_{color}.svg", scaletowidth=SIZE.PIECE
            )
            for color, type in COLOR_TYPE
        }
        self.title("CHESS")
        self.iconbitmap("res/chess.ico")

        # Bind event logic
        self.bind("<Escape>", lambda e: self.quit())
        self.bind("<q>", lambda e: self.reset())

        self.setup_buttons()
        self.board = Board()

        self.select_mode = False
        self.candidates = []

    @property
    def candidates(self) -> list[Move]:
        return self._candidate_moves

    @candidates.setter
    def candidates(self, lst) -> None:
        self._candidate_moves = lst
        self.select_mode = bool(lst)

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
            on_click, on_enter, on_exit = self.__bind_factory(pos)
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
    ) -> None:

        if self[_from].type == PieceType.PAWN or self[_to]:
            self.board.move_counter = 0

        self[_to] = self[_from]
        del self[_from]

        if _extra_capture:
            del self[_extra_capture]

        self.board.enpassant_target = enpassant_target

        self.board.move_counter += 1
        if self.board.move_counter >= 20:
            print("20 moves since last capture or pawn move!")
            ...  # TODO:draw! Ending game, check or checkmate
        # TODO: GAME WIN/GAME LOSS/GAME DRAW!
        # TODO:UNDO MOVE
        # TODO: ALLOW player's own move, two click moves
        # record down last selected piece and button detect that selected piece and does something when clicked, else it deselects logic if click away or another piece, if click on other pieces other than highlighted ones, deselect!
        # TODO: force kill, find ALL moves, from own color, highlight available pieces
        
        #TODO: CHECKS WILL alert the user, refactor into check if board is checked , maybe with a color, so it can also be used for the check if king checked after position used for king checks currently
        self.board.toggle_color_turn()

    # WINNING LOGIC TODO
    # winning logic: if list of get all moves where getall moves = find all pieces of our color and combine their valid moves is False -> color_turn loses / other_color wins -> need a pop up with label text, maybe button to reset board, closes the popup too and invokes the reset board
    def __getitem__(self, pos: Position) -> Piece:
        return self.board[pos]

    def __setitem__(self, pos: Position, piece: Piece) -> None:
        self.board[pos] = piece
        self.btn(pos)["image"] = self.__IMG_DICT[(piece.type, piece.color)]

    def __delitem__(self, pos: Position) -> None:
        del self.board[pos]
        self.btn(pos)["image"] = self.__IMG_DICT[PieceType.EMPTY, PieceColor.NONE]

    def bg(self, pos: Position) -> str:
        return (THEME.LIGHT_TILES, THEME.DARK_TILES)[sum(pos) % 2]

    @property
    def board(self) -> Board:
        return self._board

    @board.setter
    def board(self, board: Board) -> None:
        self._board = board
        for pos, piece in self.board.pieces.items():
            self.btn(pos)["image"] = self.__IMG_DICT[piece.type, piece.color]

    def reset(self) -> None:
        self.board = Board()

    def btn(self, pos: Position) -> Widget:
        return self.grid_slaves(*pos)[0]

    def reset_btn_bg(self, pos: Position) -> None:
        self.btn(pos)["bg"] = self.bg(pos)

    def __bind_factory(
        self, pos: Position
    ) -> tuple[
        Callable[[Event], None], Callable[[Event], None], Callable[[Event], None]
    ]:
        def on_click(e: Event) -> None:

            # There was a selected move previously
            if self.candidates:
                for move in self.candidates:
                    self.reset_btn_bg(move._to)
                    self.reset_btn_bg(move._from)
                # Check all moves
                for move in self.candidates:
                    if pos == move._from:
                        self.candidates = []
                        return
                    # If clicked is same as move execute it and return
                    if pos == move._to:
                        self.move_piece(
                            move._from,
                            move._to,
                            move._extra_capture,
                            move.enpassant_target,
                        )
                        self.candidates = []
                        return

                # else erase previous hints, reset and try doing the proper way

            valid_moves = self.board.get_valid_moves(
                pos
            )  # might refactor to be outside of board
            if not valid_moves:
                self.candidates = []
                self.select_mode = False
                return
            self.btn(pos)["bg"] = "#f2cf1f"
            for move in valid_moves:
                self.btn(move._to)["bg"] = "#a3e8ff"
            self.candidates = valid_moves

        # default mode: nothing happens
        # -- hover mode: just showing
        # selected piece mode: if there are valid moves, and click, enter this mode -> store candidate moves in root variable and light them up maybe in a different color like yellow "#f2cf1f"
        # if candidatemoves is not None, deactivate hover mode -> do next depending on where clicked:
        # if tile is blank or invalid enemy: reset candidate moves
        # if another own piece: reset candidate moves then check if  have candidate moves again
        # reset candidate moves on clicks on blank tile or  if clicked on another own piece -> reset again then run it correct piece,

        def on_enter(e: Event) -> None:
            if self.select_mode:
                return
            if self[pos].color != self.board.color_turn:
                return
            valid_moves = self.board.get_valid_moves(pos)
            if not valid_moves:
                self.btn(pos)["bg"] = THEME.INVALID_TILE

            for move in valid_moves:
                btn = self.btn(move._to)
                btn["bg"] = THEME.VALID_HIGHLIGHT

        def on_exit(e: Event) -> None:
            if self.select_mode:
                return
            if not self[pos]:
                return
            valid_moves = self.board.get_valid_moves(pos)
            if not valid_moves:
                self.reset_btn_bg(pos)

            for move in valid_moves:
                self.reset_btn_bg(move._to)

        return on_click, on_enter, on_exit
