from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class Pos:
    """Chessboard position for tuple addition and grid validity checks"""

    row: int
    col: int
    valid: bool = field(init=False)
    tup: tuple[int, int] = field(init=False, repr=False)

    def __post_init__(self):
        object.__setattr__(self, "valid", 0 <= self.row <= 7 and 0 <= self.col <= 7)
        object.__setattr__(self, "tup", (self.row, self.col))

    def __getitem__(self, axis: Literal[0, 1]) -> int:
        return self.row if axis == 0 else self.col

    def __add__(self, other: tuple[int, int] | Pos) -> Pos:
        return Pos(self.row + other[0], self.col + other[1])

    def __radd__(self, other: tuple[int, int] | Pos) -> Pos:
        return self.__add__(other)
    
    def __sub__(self, other: tuple[int, int] |Pos) -> Pos:
        return Pos(self.row - other[0], self.col-other[1])
    
    def __mul__(self, n: int):
        return Pos(self.row*n, self.col*n)
