from collections import UserString
from itertools import product

from flask import Flask

api = Flask(__name__)

from chess import Board

new_board = Board()

all_moves = new_board.all_moves_cache

empty = {}

for pos, moves in all_moves.items():
    empty[pos] = [move.updates for move in moves]


try_this = empty


@api.route("/api/profile")
def my_profile():
    response_body = {"data": try_this}

    return response_body
