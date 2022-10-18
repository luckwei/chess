# from __future__ import annotations
from abc import abstractmethod
from tkinter import Label

from tksvg import SvgImage

from .board import ChessBoard
from .constants import BLACK, DARK, LIGHT, PIECE_SIZE, THEME, TILE_SIZE, WHITE


class Piece:
    def __init__(
        self, cb: ChessBoard, color: bool, piece, pos: tuple[int, int]
    ) -> None:
        # Link chessboard to piece
        self.cb = cb
        self.color = color

        # Create image for the piece and save it in cb global
        self.image = SvgImage(
            file=f"res/svg/{piece}_{'white' if color else 'black'}.svg", scaletowidth=PIECE_SIZE
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
        # Deassign from old tile and remove image
        self.cb.tiles[self.pos].piece = None
        self.label.destroy()

        # Reassign to new tile and create image
        self.cb.tiles[new_pos[0], new_pos[1]].piece = self
        
        self.show(new_pos)

        # Update new position of piece
        self._pos = new_pos
    
    def show(self, pos):
        self.label = Label(
            self.cb.tiles[pos],
            image=self.image,
            bg=THEME[sum(pos) % 2],
        )
        self.label.place(height=TILE_SIZE, width=TILE_SIZE)
    
    def remove(self):
        self.label.destroy()

    @abstractmethod
    def move(self):
        ...


class Pawn(Piece):
    def __init__(self, cb: ChessBoard, color, pos) -> None:
        super().__init__(cb, color, "pawn", pos)
        self.cb.master.bind(
            "<KeyPress>",
            lambda event: self.move() if event.char == "t" else None,
            add=True,
        )

    def move(self):
        row, col = self.pos
        self.pos = (row + (-1 if self.color else 1), col)


class Bishop(Piece):
    def __init__(self, cb: ChessBoard, color, pos) -> None:
        super().__init__(cb, color, "bishop", pos)


class Knight(Piece):
    def __init__(self, cb: ChessBoard, color, pos) -> None:
        super().__init__(cb, color, "knight", pos)


class Rook(Piece):
    def __init__(self, cb: ChessBoard, color, pos) -> None:
        super().__init__(cb, color, "rook", pos)


class Queen(Piece):
    def __init__(self, cb: ChessBoard, color, pos) -> None:
        super().__init__(cb, color, "queen", pos)


class King(Piece):
    def __init__(self, cb: ChessBoard, color, pos) -> None:
        super().__init__(cb, color, "king", pos)


# PAWN_W = open_image("res/pawn_white.png")
# PAWN_B = open_image("res/pawn_black.png")
# BISHOP_W = open_image("res/bishop_white.png")
# BISHOP_B = open_image("res/bishop_black.png")
# KNIGHT_W = open_image("res/knight_white.png")
# KNIGHT_B = open_image("res/knight_black.png")
# ROOK_W = open_image("res/rook_white.png")
# ROOK_B = open_image("res/rook_black.png")
# QUEEN_W = open_image("res/queen_white.png")
# QUEEN_B = open_image("res/queen_black.png")
# KING_W = open_image("res/king_white.png")
# KING_B = open_image("res/king_black.png")
