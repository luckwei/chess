import random
from abc import ABC, abstractmethod
from dataclasses import InitVar, dataclass, field
from tkinter import Event, Label
from typing import Literal

from tksvg import SvgImage

from chess.move import Position

# from .board import ChessBoard
from .constants import PIECE_SIZE, THEME, TILE_SIZE#, Color
from .helper import Pos

from enum import Enum

class PieceType(Enum):
    EMPTY = "empty"
    PAWN = "pawn"
    ROOK = "rook"
    KNIGHT = "knight"
    BISHOP = "bishop"
    QUEEN = "queen"
    KING = "king"

class PieceColor(Enum):
    NONE = -1
    WHITE = 0
    BLACK = 1
    
PIECE_STR: dict[PieceType, tuple[str, str]] = {
    PieceType.EMPTY: (" ", " "),
    PieceType.PAWN: ("♙", "♟"),
    PieceType.ROOK: ("♖", "♜"),
    PieceType.BISHOP: ("♗", "♝"),
    PieceType.QUEEN: ("♕", "♛"),
    PieceType.KING: ("♔", "♚"),
    PieceType.KNIGHT: ("♘", "♞"),
}

COLOR_STR: dict[PieceColor, str] = {
    PieceColor.NONE: "none",
    PieceColor.WHITE: "white",
    PieceColor.BLACK: "black",
}

@dataclass
class Piece:
    row: int
    col: int
    color: PieceColor = PieceColor.NONE
    type: PieceType = PieceType.EMPTY
    
    @property
    def image(self) -> str|None:
        if self.type == PieceType.EMPTY:
            return None
        return f"res/{self.type.value}_{COLOR_STR[self.color]}.svg"
    
    @property
    def pos(self) -> Position:
        return (self.row, self.col)
    
    def __str__(self):
        return PIECE_STR[self.type][self.color.value]
    
    def __bool__(self):
        return self.type != PieceType.EMPTY
        

# @dataclass
# class Piece(ABC):
#     """Abstract base class for all following pieces for movement"""

#     _cb: ChessBoard = field(repr=False)
#     _color: Literal[Color.BLACK, Color.WHITE]
#     piece: InitVar[Literal["pawn", "knight", "bishop", "rook", "king", "queen"]]

#     _pos: Pos
#     _theme: tuple[str, str]

#     _alive: bool = field(init=False, default=True)

#     _img: SvgImage = field(init=False, repr=False)
#     _dir: Literal[-1, 1] = field(init=False, repr=False)

#     def __post_init__(
#         self, piece: Literal["pawn", "knight", "bishop", "rook", "king", "queen"]
#     ) -> None:
#         self._dir = -1 if self._color == Color.WHITE else 1
#         self._cb.pieces[self._pos.tup] = self

#         # Create image for the piece
#         self._img = SvgImage(
#             file=f"res/svg/{piece}_{self._color.value}.svg",
#             scaletowidth=PIECE_SIZE,
#         )

#         self.refresh_label()

#     @property
#     def pos(self) -> Pos:
#         return self._pos

#     # When moving the piece
#     @pos.setter
#     def pos(self, new_pos: Pos) -> None:
#         """Setting a new position is akin to moving, logic is carried over to the tile object"""

#         assert new_pos.valid, "values of position can only be from 0-7"

#         # Remove piece from old position
#         self._cb.pieces[self._pos.tup] = None

#         # Kill existing piece on new position if exists
#         self.capture_if_exists(new_pos)

#         # Put piece in new position
#         self._cb.pieces[new_pos.tup] = self

#         # Update position value and refresh image
#         self._pos = new_pos
#         self.refresh_label()

#     def refresh_label(self) -> None:
#         """Remove old label and create new one"""
#         if hasattr(self, "_label"):
#             self._label.destroy()

#         self._label = Label(
#             self._cb.tiles[self._pos.tup],
#             image=self._img,
#             bg=self._theme[sum(self._pos.tup) % 2],
#         )
#         self._label.bind("<Button-1>", self.click_handler, add=True)
#         self._label.place(height=TILE_SIZE, width=TILE_SIZE)

#     def click_handler(self, event: Event) -> None:
#         """Handles logic when clicked"""
#         self.move()
#         print(event)

#     def captured(self) -> None:
#         """Kills this piece, removes label and piece from chessboard"""
#         self._cb.pieces[self._pos.tup] = None
#         self._label.destroy()
#         self._alive = False

#     def capture_if_exists(self, pos: Pos) -> None:
#         """Kills another piece if exists"""
#         if other_piece := self._cb.pieces[pos.tup]:
#             other_piece.captured()

#     @abstractmethod
#     def move(self) -> None:
#         """If piece is alive, move it depending on piece"""


# class Pawn(Piece):
#     """Pawn with ability to promote"""

#     def __init__(
#         self,
#         _cb: ChessBoard,
#         _color: Literal[Color.WHITE, Color.BLACK],
#         _pos: Pos,
#         _theme: tuple[str, str],
#     ) -> None:
#         super().__init__(_cb, _color, "pawn", _pos, _theme)

#     def move(self) -> None:

#         valid_moves: list[tuple[Pos, bool]] = []

#         possible_moves: list[
#             tuple[Pos, Literal["move", "capture", "pawn_start", "empassant"]]
#         ] = list(
#             filter(
#                 lambda move: move[0].valid,
#                 [
#                     (self._pos + (self._dir, 0), "move"),
#                     (self._pos + (self._dir, -1), "capture"),
#                     (self._pos + (self._dir, 1), "capture"),
#                     (self._pos + (self._dir * 2, 0), "pawn_start"),
#                     (self._pos + (self._dir, -1), "empassant"),
#                     (self._pos + (self._dir, 1), "empassant"),
#                 ],
#             )
#         )

#         for pos, type in possible_moves:
#             other_piece = self._cb.pieces[pos.tup]

#             match type:
#                 case "move":
#                     if other_piece is None:
#                         valid_moves.append((pos, False))

#                 case "capture":
#                     if other_piece and other_piece._color != self._color:
#                         valid_moves.append((pos, False))

#                 case "pawn_start":
#                     if (
#                         (
#                             (self._pos.row == 6 and self._color == Color.WHITE)
#                             or (self._pos.row == 1 and self._color == Color.BLACK)
#                         )
#                         and other_piece is None
#                         and self._cb.pieces[(self._pos + (self._dir, 0)).tup] is None
#                     ):
#                         valid_moves.append((pos, False))

#                 # code logic, TODO: CODE LOGIC FOR CAPTURE
#                 case "empassant":
#                     enemy_pawn = Pos(self._pos.row, pos.col)
#                     if (
#                         other_piece is None
#                         and (
#                             (self._pos.row == 3 and self._color == Color.WHITE)
#                             or (self._pos.row == 4 and self._color == Color.BLACK)
#                         )
#                         and isinstance(self._cb.pieces[enemy_pawn.tup], Pawn)
#                         and "last move was pawn double push" "save the move in cb"
#                     ):
#                         valid_moves.append((pos, True))

#         if valid_moves:
#             choice = random.choice(valid_moves)
#             if choice[1]:
#                 self.empassat(choice[0])
#             else:
#                 self.pos = choice[0]

#     # TODO: Bring logic to pos setter in Pawn
#     def empassat(self, pos: Pos) -> None:
#         if other_pawn := self._cb.pieces[(pos - (self._dir, 0)).tup]:
#             self.pos = pos
#             other_pawn.captured()

#     def promote(self):
#         ...


# class Bishop(Piece):
#     """Bishop moves diagonally"""

#     def __init__(
#         self,
#         cb: ChessBoard,
#         color: Literal[Color.WHITE, Color.BLACK],
#         pos: Pos,
#         _theme: tuple[str, str],
#     ) -> None:
#         super().__init__(cb, color, "bishop", pos, _theme)

#     def move(self):
#         possible_moves: list[Pos] = [
#             self._pos + Pos(1, 1) * n for n in range(-7, 7)
#         ] + [self._pos + Pos(-1, 1) * n for n in range(-7, 7)]

#         possible_moves = [move for move in possible_moves if move.valid]
#         print(possible_moves)

#         valid_moves = []
#         for pos in possible_moves:
#             # TODO: implement pieces object for better slicing with pos
#             if (
#                 other_piece := self._cb.pieces[pos.tup]
#             ) is None or other_piece._color != self._color:
#                 valid_moves.append(pos)

#         # TODO: Time to make move class with from and to, with dynamic valid move getter, these checkers may be connected to chessboard and not moves and will help with legal/illegal move logic
#         # TODO:No hop overs
#         if valid_moves:
#             self.pos = random.choice(valid_moves)


# class Knight(Piece):
#     """Knight moves in L shapes, able to jump over pieces"""

#     def __init__(
#         self,
#         cb: ChessBoard,
#         color: Literal[Color.WHITE, Color.BLACK],
#         pos: Pos,
#         _theme: tuple[str, str],
#     ) -> None:
#         super().__init__(cb, color, "knight", pos, _theme)

#     def move(self):
#         ...


# class Rook(Piece):
#     """Rook moves in straight lines"""

#     def __init__(
#         self,
#         cb: ChessBoard,
#         color: Literal[Color.WHITE, Color.BLACK],
#         pos: Pos,
#         _theme: tuple[str, str],
#     ) -> None:
#         super().__init__(cb, color, "rook", pos, _theme)

#     def move(self):
#         ...


# class Queen(Piece):
#     """Moves perpendicularly and diagonally"""

#     def __init__(
#         self,
#         cb: ChessBoard,
#         color: Literal[Color.WHITE, Color.BLACK],
#         pos: Pos,
#         _theme: tuple[str, str],
#     ) -> None:
#         super().__init__(cb, color, "queen", pos, _theme)

#     def move(self):
#         ...


# class King(Piece):
#     """Moves into surrounding tiles, objective is to be checkmated"""

#     def __init__(
#         self,
#         cb: ChessBoard,
#         color: Literal[Color.WHITE, Color.BLACK],
#         pos: Pos,
#         _theme: tuple[str, str],
#     ) -> None:
#         super().__init__(cb, color, "king", pos, _theme)

#     def move(self):
#         ...
