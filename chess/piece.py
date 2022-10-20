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
        self.capture_if_exists(new_pos)

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

    def captured(self) -> None:
        """Kills this piece, removes label and piece from chessboard"""
        self._cb.pieces[self._pos.tup] = None
        self._label.destroy()
        self._alive = False
        
    def capture_if_exists(self, pos: Pos) -> None:
        """Kills another piece if exists"""
        if other_piece:=self._cb.pieces[pos.tup]:
            other_piece.captured()
        

    @abstractmethod
    def move(self) -> None:
        """If piece is alive, move it depending on piece"""


class Pawn(Piece):
    """Pawn with ability to promote"""

    def __init__(
        self, _cb: ChessBoard, _color: Literal["white", "black"], _pos: Pos
    ) -> None:
        super().__init__(_cb, _color, "pawn", _pos)

    def move(self) -> None:

        valid_moves = []

        possible_moves: list[
            tuple[Pos, Literal["move", "capture", "pawn_start", "empassant"]]
        ] = [
            (self._pos + (self._dir, 0), "move"),
            (self._pos + (self._dir, -1), "capture"),
            (self._pos + (self._dir, 1), "capture"),
            (self._pos + (self._dir * 2, 0), "pawn_start"),
            (self._pos + (self._dir, -1), "empassant"),
            (self._pos + (self._dir, 1), "empassant"),
        ]

        for pos, type in possible_moves:
            if pos.valid is False:
                continue

            other_piece = self._cb.pieces[pos.tup]
            
            match type:
                case "move":
                    if other_piece is None:
                        valid_moves.append(pos)

                case "capture":
                    if other_piece and other_piece._color != self._color:
                        valid_moves.append(pos)

                case "pawn_start":
                    if (
                        (
                            (self._pos.row == 6 and self._color == "white")
                            or (self._pos.row == 1 and self._color == "black")
                        )
                        and other_piece is None
                        and self._cb.pieces[(self._pos + (self._dir, 0)).tup] is None
                    ):
                        valid_moves.append(pos)

                # code logic, TODO: CODE LOGIC FOR CAPTURE
                case "empassant":
                    enemy_pawn = (self._pos.row, pos.col)
                    if (
                        other_piece is None
                        and (
                            (self._pos.row == 3 and self._color == "white")
                            or (self._pos.row == 4 and self._color == "black")
                        )
                        and isinstance(self._cb.pieces[enemy_pawn], Pawn)
                        and "last move was pawn double push"
                    ):
                        valid_moves.append(pos)

        if valid_moves:
            self.pos = random.choice(valid_moves)

    def promote(self):
        ...


class Bishop(Piece):
    """Bishop moves diagonally"""

    def __init__(
        self, cb: ChessBoard, color: Literal["white", "black"], pos: Pos
    ) -> None:
        super().__init__(cb, color, "bishop", pos)

    def move(self):
        ...


class Knight(Piece):
    """Knight moves in L shapes, able to jump over pieces"""

    def __init__(
        self, cb: ChessBoard, color: Literal["white", "black"], pos: Pos
    ) -> None:
        super().__init__(cb, color, "knight", pos)

    def move(self):
        ...


class Rook(Piece):
    """Rook moves in straight lines"""

    def __init__(
        self, cb: ChessBoard, color: Literal["white", "black"], pos: Pos
    ) -> None:
        super().__init__(cb, color, "rook", pos)

    def move(self):
        ...


class Queen(Piece):
    """Moves perpendicularly and diagonally"""

    def __init__(
        self, cb: ChessBoard, color: Literal["white", "black"], pos: Pos
    ) -> None:
        super().__init__(cb, color, "queen", pos)

    def move(self):
        ...


class King(Piece):
    """Moves into surrounding tiles, objective is to be checkmated"""

    def __init__(
        self, cb: ChessBoard, color: Literal["white", "black"], pos: Pos
    ) -> None:
        super().__init__(cb, color, "king", pos)

    def move(self):
        ...
