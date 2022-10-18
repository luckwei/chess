from abc import ABC, abstractmethod
import random
from tkinter import Label

from tksvg import SvgImage

from .board import ChessBoard
from .constants import PIECE_SIZE, THEME, TILE_SIZE


class Piece(ABC):
    """Abstract base class for all following pieces for movement"""

    def __init__(
        self, cb: ChessBoard, color: bool, piece: str, pos: tuple[int, int]
    ) -> None:
        # Link chessboard to piece
        self.cb = cb
        self.color = color
        self.direction = -1 if self.color else +1
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
        """Setting a new position is akin to moving, logic is carried over to the tile object"""
        # Ressign to new tile
        self.cb.tiles[new_pos].piece = self
        self._pos = new_pos

    def show(self, pos):
        """Display piece"""
        self.label = Label(
            self.cb.tiles[pos],
            image=self.image,
            bg=THEME[sum(pos) % 2],
        )
        self.label.place(height=TILE_SIZE, width=TILE_SIZE)

    def remove(self, kill=False):
        """Remove display or kill piece entirely"""
        self.label.destroy()
        if kill:
            self.alive = False

    @abstractmethod
    def move(self):
        """If piece is alive, move it depending on piece"""
        
    def keypress_handler(self, event):
        if event.char == "t":
            self.move()


class Pawn(Piece):
    def __init__(self, cb: ChessBoard, color: bool, pos: tuple[int, int]) -> None:
        super().__init__(cb, color, "pawn", pos)
        self.cb.master.bind(
            "<KeyPress>",
            self.keypress_handler,
            add=True,
        )

    def move(self):
        if self.alive is False:
            return
        
        
        #check if possible
        normal_move = [(self.pos[0]+self.direction, self.pos[1])]
        capture_moves = [(self.pos[0]+self.direction, self.pos[1]+side) for side in (-1, +1)]
        
        all_moves = normal_move + capture_moves
        
        self.pos = random.choice(all_moves)


class Bishop(Piece):
    def __init__(self, cb: ChessBoard, color: bool, pos: tuple[int, int]) -> None:
        super().__init__(cb, color, "bishop", pos)
        # self.cb.master.bind(
        #     "<KeyPress>",
        #     self.keypress_handler,
        #     add=True,
        # )

    def move(self):
        if self.alive is False:
            return
        row, col = self.pos
        self.pos = (row + (-1 if self.color else 1), col + 1)

    


class Knight(Piece):
    def __init__(self, cb: ChessBoard, color: bool, pos: tuple[int, int]) -> None:
        super().__init__(cb, color, "knight", pos)

    def move(self):
        ...


class Rook(Piece):
    def __init__(self, cb: ChessBoard, color: bool, pos: tuple[int, int]) -> None:
        super().__init__(cb, color, "rook", pos)

    def move(self):
        ...


class Queen(Piece):
    def __init__(self, cb: ChessBoard, color: bool, pos: tuple[int, int]) -> None:
        super().__init__(cb, color, "queen", pos)

    def move(self):
        ...


class King(Piece):
    def __init__(self, cb: ChessBoard, color: bool, pos: tuple[int, int]) -> None:
        super().__init__(cb, color, "king", pos)

    def move(self):
        ...


# TODO: Fix alive mechanic for better garbage collection
