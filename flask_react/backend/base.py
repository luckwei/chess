from collections import UserString
from itertools import product

from flask import Flask

api = Flask(__name__)

from chess import Board

board = Board()


@api.route("/api/new_random_game")
def new_random_game():
    board.set_fen(random=True)

    return {
        "updates": board.data,
        "available_moves": board.all_move_pos_only,
    }


@api.route("/api/choose_move/<string:frm>_<string:to>")
def choose_move(frm: str, to: str):
    move = board.get_move(frm, to)
    if move is None:
        return "MOVE DOES NOT EXIST"

    board.execute_move_on_board(move)

    return {
        "updates": move.updates,
        "available_moves": board.all_move_pos_only,
    }


@api.route("/api/board")
def home():
    return {"updates": board.data, "available_moves": board.all_move_pos_only}
