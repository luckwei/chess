import random
from abc import ABC, abstractmethod
from dataclasses import InitVar, dataclass, field
from tkinter import Event, Label
from typing import Literal

from tksvg import SvgImage

from .board import ChessBoard
from .constants import PIECE_SIZE, THEME, TILE_SIZE
from .helper import Pos


@dataclass
class Piece(ABC):
    """Abstract base class for all following pieces for movement"""

    _cb: ChessBoard = field(repr=False)
    _color: Literal["white", "black"]
    piece: InitVar[Literal["pawn", "knight", "bishop", "rook", "king", "queen"]]

    _pos: Pos

    _alive: bool = field(init=False, default=True)

    _img: SvgImage = field(init=False, repr=False)
    _dir: Literal[-1, 1] = field(init=False, repr=False)

    def __post_init__(
        self, piece: Literal["pawn", "knight", "bishop", "rook", "king", "queen"]
    ) -> None:
        self._dir = -1 if self._color == "white" else 1
        self._cb.pieces[self._pos.tup] = self

        # Create image for the piece
        self._img = SvgImage(
            file=f"res/svg/{piece}_{self._color}.svg",
            scaletowidth=PIECE_SIZE,
        )

        self.refresh_label()

    @property
    def pos(self) -> Pos:
        return self._pos

    # When moving the piece
    @pos.setter
    def pos(self, new_pos: Pos) -> None:
        """Setting a new position is akin to moving, logic is carried over to the tile object"""

        assert new_pos.valid, "values of position can only be from 0-7"

        # Remove piece from old position
        self._cb.pieces[self._pos.tup] = None

        # Kill existing piece on new position if exists
        if other_piece := self._cb.pieces[new_pos.tup]:
            other_piece.kill()

        # Put piece in new position
        self._cb.pieces[new_pos.tup] = self

        # Update position value and refresh image
        self._pos = new_pos
        self.refresh_label()

    def refresh_label(self) -> None:
        """Remove old label and create new one"""
        if hasattr(self, "_label"):
            self._label.destroy()

        self._label = Label(
            self._cb.tiles[self._pos.tup],
            image=self._img,
            bg=THEME[sum(self._pos.tup) % 2],
        )
        self._label.bind("<Button-1>", self.click_handler, add=True)
        self._label.place(height=TILE_SIZE, width=TILE_SIZE)

    def click_handler(self, event: Event) -> None:
        """Handles logic when clicked"""
        self.move()
        print(event)

    def kill(self) -> None:
        """Kills this piece, removes label and piece from chessboard"""
        self._cb.pieces[self._pos.tup] = None
        self._label.destroy()
        self._alive = False

    @abstractmethod
    def move(self) -> None:
        """If piece is alive, move it depending on piece"""


class Pawn(Piece):
    def __init__(
        self, cb: ChessBoard, color: Literal["white", "black"], pos: Pos
    ) -> None:
        super().__init__(cb, color, "pawn", pos)

    def move(self):
        if self._alive is False:
            return

        available_moves = []

        # normal_move
        normal_move = self._pos + (self._dir, 0)

        if normal_move.valid and self._cb.pieces[normal_move.tup] is None:
            available_moves.append(normal_move)

        capture_moves = [
            self._pos + (self._dir, -1),
            self._pos + (self._dir, 1),
        ]

        capture_moves = [move for move in capture_moves if move.valid]

        for move in capture_moves:
            if (other := self._cb.pieces[move.tup]) and other._color != self._color:
                available_moves.append(move)

        if available_moves:
            self.pos = random.choice(available_moves)


class Bishop(Piece):
    def __init__(
        self, cb: ChessBoard, color: Literal["white", "black"], pos: Pos
    ) -> None:
        super().__init__(cb, color, "bishop", pos)

    def move(self):
        ...


class Knight(Piece):
    def __init__(
        self, cb: ChessBoard, color: Literal["white", "black"], pos: Pos
    ) -> None:
        super().__init__(cb, color, "knight", pos)

    def move(self):
        ...


class Rook(Piece):
    def __init__(
        self, cb: ChessBoard, color: Literal["white", "black"], pos: Pos
    ) -> None:
        super().__init__(cb, color, "rook", pos)

    def move(self):
        ...


class Queen(Piece):
    def __init__(
        self, cb: ChessBoard, color: Literal["white", "black"], pos: Pos
    ) -> None:
        super().__init__(cb, color, "queen", pos)

    def move(self):
        ...


class King(Piece):
    def __init__(
        self, cb: ChessBoard, color: Literal["white", "black"], pos: Pos
    ) -> None:
        super().__init__(cb, color, "king", pos)

    def move(self):
        ...


# TODO: Fix alive mechanic for better garbage collection
