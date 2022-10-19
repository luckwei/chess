from dataclasses import dataclass


def check_grid(pos: tuple[int, int]):
    return min(pos) >= 0 and max(pos) <= 7


@dataclass
class Inc:
    row: int
    col: int

    def __add__(self, other: tuple[int, int]):
        return self.row + other[0], self.col + other[1]

    def __radd__(self, other: tuple[int, int]):
        return self.__add__(other)

    def __sub__(self, other: tuple[int, int]):
        return self.row - other[0], self.col - other[1]
