import random
from abc import ABC, abstractmethod
from tkinter import Label, Event

from tksvg import SvgImage

from .board import ChessBoard
from .constants import PIECE_SIZE, THEME, TILE_SIZE
from .helper import pos_inc


class Piece(ABC):
    """Abstract base class for all following pieces for movement"""

    def __init__(
        self, cb: ChessBoard, color: bool, piece: str, pos: tuple[int, int]
    ) -> None:
        self._alive = True
        
        # Link chessboard to piece
        self._cb = cb
        self._tile = cb.tiles[pos]
        self._color = color
        self._dir = -1 if color else +1
        self._pos = pos

        # Create image for the piece
        self._img = SvgImage(
            file=f"res/svg/{piece}_{'white' if color else 'black'}.svg",
            scaletowidth=PIECE_SIZE,
        )
        
        self._label: Label

        self.show()

        self._cb.master.bind(
            "<KeyPress>",
            self.keypress_handler,
            add=True,
        )
    
        
    @property
    def pos(self) -> tuple[int, int]:
        return self._pos

    # When moving the piece
    @pos.setter
    def pos(self, new_pos: tuple[int, int]) -> None:
        """Setting a new position is akin to moving, logic is carried over to the tile object"""
        # Kill other piece
        new_tile = self._cb.tiles[new_pos]
        if new_tile.piece:
            new_tile.piece.remove(kill=True)
        # Remove this piece from previous position
        
        # Transfer piece to new position
        self.remove()
        self._tile = new_tile
        self._tile.piece = self
        self._pos = new_pos
        self.show()

    def show(self):
        """Display piece"""
        self.label = Label(
            self._tile,
            image=self._img,
            bg=THEME[sum(self._pos) % 2],
        )
        self.label.bind("<Button-1>", self.click_handler, add=True)
        self.label.place(height=TILE_SIZE, width=TILE_SIZE)

    def click_handler(self, event: Event) -> None:
        print(event)
        self.move()
        
    def remove(self, kill=False):
        """Remove display or kill piece entirely"""
        self._tile.piece = None
        self.label.destroy()
        if kill:
            self._alive = False

    @abstractmethod
    def move(self):
        """If piece is alive, move it depending on piece"""
        
    def keypress_handler(self, event):
        if event.char == "t":
            self.move()


class Pawn(Piece):
    def __init__(self, cb: ChessBoard, color: bool, pos: tuple[int, int]) -> None:
        super().__init__(cb, color, "pawn", pos)

    def move(self):
        if self._alive is False:
            return
        
        try:
            available_moves = []
            # normal_move
            normal_move = pos_inc(self._pos, self._dir, 0)
            if self._cb.tiles[normal_move].piece is None:
                available_moves.append(normal_move)
                
            
            capture_moves = [pos_inc(self._pos, self._dir, -1), pos_inc(self._pos, self._dir, 1)]
            
            capture_moves = [move for move in capture_moves if min(move) >= 0 and max(move) <= 7]
            
            for move in capture_moves:
                if (other := self._cb.tiles[move].piece) and other._color != self._color:
                    available_moves.append(move)

            if available_moves:
                self.pos = random.choice(available_moves)
        except KeyError:
            return


class Bishop(Piece):
    def __init__(self, cb: ChessBoard, color: bool, pos: tuple[int, int]) -> None:
        super().__init__(cb, color, "bishop", pos)


    def move(self):
        ...
        # if self.alive is False:
        #     return
        # row, col = self.pos
        # self.pos = (row + (-1 if self.color else 1), col + 1)

    


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
