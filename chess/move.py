from dataclasses import dataclass
from enum import Enum, auto

import numpy as np

from .types import Position


class Flag(Enum):
    NONE = auto()
    ENPASSANT_TRGT = auto()
    ENPASSANT = auto()
    CASTLE_LONG = auto()
    CASTLE_SHORT = auto()
    LOSE_KING_PRIV = auto()
    LOSE_ROOK_PRIV = auto()


@dataclass
class Move:
    to: Position
    flag: Flag = Flag.NONE


def diag_m(pos: Position, n=7) -> list[Move]:
    moves = []
    for i in range(1, n + 1):
        NE = Move((pos[0] + i, pos[1] + i))
        NW = Move((pos[0] + i, pos[1] - i))
        SE = Move((pos[0] - i, pos[1] + i))
        SW = Move((pos[0] - i, pos[1] - i))
        moves.extend([NE, NW, SE, SW])
    return moves


def perp_m(pos: Position, n=7) -> list[Move]:
    moves = []
    for i in range(1, n + 1):
        N = Move((pos[0] + i, pos[1]))
        S = Move((pos[0] - i, pos[1]))
        E = Move((pos[0], pos[1] + i))
        W = Move((pos[0], pos[1] - i))
        moves.extend([N, S, E, W])
    return moves


def lshapes_m(pos: Position) -> list[Move]:
    moves = []
    for quadrant in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
        for magnitude in [(1, 2), (2, 1)]:
            x, y = np.multiply(quadrant, magnitude)
            moves.append(Move((pos[0] + x, pos[1] + y)))
    return moves


def castle_short_m(pos: Position) -> list[Move]:
    return [Move((pos[0], pos[1] + 2), Flag.CASTLE_SHORT)]


def castle_long_m(pos: Position) -> list[Move]:
    return [Move((pos[0], pos[1] - 2), Flag.CASTLE_LONG)]


def pincer_m(pos: Position, dir: int) -> list[Move]:
    L = Move((pos[0] + dir, pos[1] + 1))
    R = Move((pos[0] + dir, pos[1] - 1))
    return [L, R]


def enpassant_m(pos: Position, dir: int) -> list[Move]:
    L = Move((pos[0] + dir, pos[1] + 1), Flag.ENPASSANT)
    R = Move((pos[0] + dir, pos[1] - 1), Flag.ENPASSANT)
    return [L, R]


def front_short_m(pos: Position, dir: int) -> list[Move]:
    return [Move((pos[0] + dir, pos[1]))]


def front_long_m(pos: Position, dir: int) -> list[Move]:
    return [Move((pos[0] + 2 * dir, pos[1]), Flag.ENPASSANT_TRGT)]
