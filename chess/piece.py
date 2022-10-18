from abc import ABC, abstractmethod
from tkinter import Label

from tksvg import SvgImage

from .board import ChessBoard
from .constants import PIECE_SIZE, THEME, TILE_SIZE


class Piece(ABC):
    def __init__(
        self, cb: ChessBoard, color: bool, piece: str, pos: tuple[int, int]
    ) -> None:
        # Link chessboard to piece
        self.cb = cb
        self.color = color
        self.alive = True

        # Create image for the piece and save it in cb global
        self.image = SvgImage(
            file=f"res/svg/{piece}_{'white' if color else 'black'}.svg",
            scaletowidth=PIECE_SIZE,
        )

        # Place the piece on the board using setter
        self._pos = pos
        self.show(pos)

    @property
    def pos(self) -> tuple[int, int]:
        return self._pos

    # When moving the piece
    @pos.setter
    def pos(self, new_pos: tuple[int, int]) -> None:
        # Ressign to new tile
        self.cb.tiles[new_pos].piece = self
        self._pos = new_pos

    def show(self, pos):
        self.label = Label(
            self.cb.tiles[pos],
            image=self.image,
            bg=THEME[sum(pos) % 2],
        )
        self.label.place(height=TILE_SIZE, width=TILE_SIZE)

    def remove(self, kill=False):
        self.label.destroy()
        if kill:
            self.alive = False

    def move(self):
        if self.alive is False:
            return
        row, col = self.pos
        self.pos = (row + (-1 if self.color else 1), col)


class Pawn(Piece):
    def __init__(self, cb: ChessBoard, color: bool, pos: tuple[int, int]) -> None:
        super().__init__(cb, color, "pawn", pos)

    def move(self):
        row, col = self.pos
        self.pos = (row + (-1 if self.color else 1), col + 1)


class Bishop(Piece):
    def __init__(self, cb: ChessBoard, color: bool, pos: tuple[int, int]) -> None:
        super().__init__(cb, color, "bishop", pos)
        self.cb.master.bind(
            "<KeyPress>",
            lambda event: self.move() if event.char == "t" else None,
            add=True,
        )


class Knight(Piece):
    def __init__(self, cb: ChessBoard, color: bool, pos: tuple[int, int]) -> None:
        super().__init__(cb, color, "knight", pos)


class Rook(Piece):
    def __init__(self, cb: ChessBoard, color: bool, pos: tuple[int, int]) -> None:
        super().__init__(cb, color, "rook", pos)


class Queen(Piece):
    def __init__(self, cb: ChessBoard, color: bool, pos: tuple[int, int]) -> None:
        super().__init__(cb, color, "queen", pos)


class King(Piece):
    def __init__(self, cb: ChessBoard, color: bool, pos: tuple[int, int]) -> None:
        super().__init__(cb, color, "king", pos)


# TODO: Fix alive mechanic for better garbage collection
