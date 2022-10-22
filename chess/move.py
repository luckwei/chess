from chess.board import Board


Position = tuple[int, int]

def get_valid_moves_rook(board: Board, row:int, col:int)->list[Position]:
    ...