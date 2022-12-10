from collections import UserString
from itertools import product

from flask import Flask

api = Flask(__name__)

from chess import Board

new_board = Board()



try_this = new_board.all_moves_cache



@api.route("/api/profile")
def my_profile():
    response_body = {"data": try_this}

    return response_body
