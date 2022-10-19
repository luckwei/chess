from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

def pos_inc(pos: tuple[int, int], inc: tuple[int, int]):
    return pos[0]+inc[0], pos[1]+inc[1]

def check_grid(pos: tuple[int, int]):
    return min(pos) >= 0 and max(pos) <= 7



@dataclass
class Pos:
    row: int
    col: int
    valid: bool = field(init=False)

    def __post_init__(self):
        self.valid = 0 <= self.row <= 7 and 0 <= self.col <= 7

    def __getitem__(self, axis: Literal[0,1]) -> int:
        return self.row if axis == 0 else self.col

    def __add__(self, other) -> Pos:
        return Pos(self[0] + other[0], self[1] + other[1])

    def __radd__(self, other) -> Pos:
        return self.__add__(other)