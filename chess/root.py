from __future__ import annotations

from itertools import product
from tkinter import GROOVE, Button, Event, Tk, Widget
from typing import Callable

from tksvg import SvgImage

from .board import Board, Flag, Move

from .constants import SIZE, THEME
from .piece import COLOR_TYPE, Piece, PieceColor, PieceType
from .types import Position


class Root(Tk):
    def __init__(self) -> None:
        super().__init__()

        self.pointer_image = SvgImage(file="res/circle.svg", scaletowidth=20)

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
        self.selected_pos = None
        self.candidates = []
        self.preview_candidates = []

    @property
    def candidates(self) -> list[Move]:
        return self._candidates

    @candidates.setter
    def candidates(self, moves) -> None:
        self._candidates = moves
        # self.select_mode = bool(moves)

    @candidates.deleter
    def candidates(self) -> None:
        self.candidates = []

    def setup_buttons(self):
        for pos in product(range(8), range(8)):
            button = Button(
                self,
                bg=self.bg(pos),
                activebackground=THEME.ACTIVE_BG,
                bd=0,
                relief=GROOVE,
                overrelief=GROOVE,
                height=SIZE.TILE,
                width=SIZE.TILE,
            )
            on_click, on_enter, on_exit = self.__bind_factory(pos)
            button.bind("<ButtonRelease-1>", on_click)
            button.bind("<Enter>", on_enter)
            button.bind("<Leave>", on_exit)

            button.grid(row=pos[0], column=pos[1])


    def move_piece(self, frm: Position, to: Position, flag=Flag.NONE) -> None:
        # define inner function
        def single_move(frm: Position, to: Position) -> None:
            self[to] = self[frm]
            del self[frm]
            
        match flag:
            case Flag.CASTLE_LONG:
                row = 7 if self.board.color_turn == PieceColor.WHITE else 0
                single_move((row, 0), (row, 3))
                self.board.castling_flags[self.board.color_turn] = [False, False]

            case Flag.CASTLE_SHORT:
                row = 7 if self.board.color_turn == PieceColor.WHITE else 0
                single_move((row,7), (row,5))
                self.board.castling_flags[self.board.color_turn] = [False, False]

            case Flag.LOSE_KING_PRIV:
                self.board.castling_flags[self.board.color_turn] = [False, False]
            case Flag.LOSE_ROOK_PRIV:
                row = 7 if self.board.color_turn == PieceColor.WHITE else 0
                if frm == (row, 0):
                    self.board.castling_flags[self.board.color_turn][0] = False
                if frm == (row, 7):
                    self.board.castling_flags[self.board.color_turn][1] = False

            case Flag.ENPASSANT:
                del self[self.board.enpassant_target]

        self.board.enpassant_target = to if flag == Flag.ENPASSANT_TRGT else None

        if self[frm].type == PieceType.PAWN or self[to]:
            self.board.move_counter = 0

        single_move(frm, to)


        self.board.move_counter += 1
        if self.board.move_counter >= 20:
            print("20 moves since last capture or pawn move!")
            ...  # TODO:draw! Ending game, check or checkmate
        #TODO: PROMOTION LOGIC
        # TODO: GAME WIN/GAME LOSS/GAME DRAW!
        # TODO:UNDO MOVE

        # TODO: force kill, find ALL moves, from own color, highlight available pieces

        # TODO: CHECKS WILL alert the user, refactor into check if board is checked , maybe with a color, so it can also be used for the check if king checked after position used for king checks currently
        self.board.toggle_color_turn()

    # WINNING LOGIC TODO
    # winning logic: if list of get all moves where getall moves = find all pieces of our color and combine their valid moves is False -> color_turn loses / other_color wins -> need a pop up with label text, maybe button to reset board, closes the popup too and invokes the reset board
    def __getitem__(self, pos: Position) -> Piece:
        return self.board[pos]

    def __setitem__(self, pos: Position, piece: Piece) -> None:
        self.board[pos] = piece
        self.btn(pos)["image"] = self.__IMG_DICT[piece.type, piece.color]

    def __delitem__(self, pos: Position | None) -> None:
        if pos is None:
            return
        del self.board[pos]
        self.btn(pos)["image"] = self.__IMG_DICT[PieceType.EMPTY, PieceColor.NONE]

    def bg(self, pos: Position) -> str:
        return THEME.LIGHT_TILES if sum(pos) % 2 == 0 else THEME.DARK_TILES

    # TODO:Set states for background

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
            if self.selected_pos:
                self.reset_btn_bg(self.selected_pos)
                for move in self.candidates:
                    to = move.to
                    self.reset_btn_bg(to)
                # Check all moves
                for move in self.candidates:
                    to, flag = move.to, move.flag

                    if pos == self.selected_pos:
                        self.candidates = []
                        self.selected_pos = None
                        return
                    # If clicked is same as move execute it and return
                    if pos == to:

                        self.move_piece(self.selected_pos, to, flag)
                        self.candidates = []
                        self.selected_pos = None
                        return

            valid_moves = self.board.get_valid_moves(
                pos
            )  # might refactor to be outside of board
            if not valid_moves:
                self.candidates = []
                self.select_mode = False
                return
            self.btn(pos)["bg"] = THEME.ACTIVE_BG
            for move in valid_moves:
                if self[move.to]:
                    self.btn(move.to)["bg"] = THEME.VALID_CAPTURE
                else:
                    self.btn(move.to)["bg"] = (
                        THEME.VALID_HIGHLIGHT_DARK
                        if sum(move.to) % 2
                        else THEME.VALID_HIGHLIGHT_LIGHT
                    )
            self.candidates = valid_moves
            self.selected_pos = pos

        def on_enter(e: Event) -> None:
            if self.candidates:
                return
            if self[pos].color != self.board.color_turn:
                return

            valid_to = [move.to for move in self.board.get_valid_moves(pos)]

            for to in valid_to:
                if self[to]:
                    self.btn(to)["bg"] = THEME.VALID_CAPTURE
                else:
                    self.btn(to)["bg"] = (
                        THEME.VALID_HIGHLIGHT_DARK
                        if sum(to) % 2
                        else THEME.VALID_HIGHLIGHT_LIGHT
                    )

                    # self.btn(move._to)["image"] = self.pointer_image

        def on_exit(e: Event) -> None:
            if self.candidates:
                return
            if not self[pos]:
                return
            valid_moves = self.board.get_valid_moves(pos)
            if not valid_moves:
                self.reset_btn_bg(pos)

            for move in valid_moves:
                self.reset_btn_bg(move.to)

        return on_click, on_enter, on_exit
