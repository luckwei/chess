from copy import deepcopy

from .board import Board
from .move import Flag, Move, diag_m, lshapes_m, perp_m, pincer_m
from .piece import FEN_MAP, Piece, PieceColor, PieceType
from .types import Position


class KingCheck:
    @staticmethod
    def safe(board: Board, pos: Position, color: PieceColor) -> bool:
        enemy_color = (
            PieceColor.WHITE if color == PieceColor.BLACK else PieceColor.BLACK
        )

        dir = -1 if color == PieceColor.WHITE else 1

        enemy_knight = [
            1
            for move in lshapes_m(pos)
            if Checks.to_pos_in_grid(move)
            and board[move.to] == Piece(enemy_color, PieceType.KNIGHT)
        ]

        # check perpendiculars
        enemy_rook_queen = [
            1
            for move in perp_m(pos)
            if Checks.to_pos_in_grid(move)
            and board[move.to]
            in (Piece(enemy_color, PieceType.ROOK), Piece(enemy_color, PieceType.QUEEN))
            and Checks.no_obstruction(board, pos, move)
        ]

        # check diagonals
        enemy_bishop_queen = [
            1
            for move in diag_m(pos)
            if Checks.to_pos_in_grid(move)
            and board[move.to]
            in (
                Piece(enemy_color, PieceType.BISHOP),
                Piece(enemy_color, PieceType.QUEEN),
            )
            and Checks.no_obstruction(board, pos, move)
        ]

        # check adjacent for king
        enemy_king = [
            1
            for move in perp_m(pos, 1) + diag_m(pos, 1)
            if Checks.to_pos_in_grid(move)
            and board[move.to] == Piece(enemy_color, PieceType.KING)
        ]

        # check pincer for pawn
        enemy_pawn = [
            1
            for move in pincer_m(pos, dir)
            if Checks.to_pos_in_grid(move)
            and board[move.to] == Piece(enemy_color, PieceType.PAWN)
        ]

        all_enemies = (
            enemy_knight
            + enemy_rook_queen
            + enemy_bishop_queen
            + enemy_king
            + enemy_pawn
        )

        return not all_enemies

    # TODO GET ALL POSSIBLE MOVES AND CHECK IF 0, IF YES THEN CHECKMATE, black/grey background?
    # TODO KING IS RED IF CHECKED, OR! WHEN INVALID MOVE DUR TO CHECK
    # TODO: IMPLEMENT DRAW FOR stALEMATE
    @staticmethod
    def castle_long_valid(board: Board) -> bool:
        row = 7 if board.color_turn == PieceColor.WHITE else 0

        pos_pass_long = KingCheck.safe(board, (row, 3), board.color_turn)
        clear_lane = not [
            1
            for btwn_pos in [
                (row, 1),
                (row, 2),
                (row, 3),
            ]
            if board[btwn_pos]
        ]

        king_not_checked = KingCheck.safe(board, (row, 4), board.color_turn)

        priviledge = board.castling_flags[board.color_turn][0]
        return pos_pass_long and clear_lane and king_not_checked and priviledge

    @staticmethod
    def castle_short_valid(board: Board) -> bool:
        row = 7 if board.color_turn == PieceColor.WHITE else 0

        pos_pass_short = KingCheck.safe(board, (row, 5), board.color_turn)
        clear_lane = not [
            1
            for btwn_pos in [
                (row, 5),
                (row, 6),
            ]
            if board[btwn_pos]
        ]

        king_not_checked = KingCheck.safe(board, (row, 4), board.color_turn)

        priviledge = board.castling_flags[board.color_turn][1]
        return pos_pass_short and clear_lane and king_not_checked and priviledge


class PawnCheck:
    @staticmethod
    def enpassant_valid(board: Board, pos: Position, move: Move) -> bool:
        to = move.to
        enemy_pawn = (pos[0], to[1])
        return board.enpassant_target == enemy_pawn

    @staticmethod
    def pincer_valid(board: Board, pos: Position, move: Move) -> bool:
        to = move.to
        if not board[to]:
            return False
        if board[move.to].color != board[pos].color:
            return True
        return False

    @staticmethod
    def front_long_valid(board: Board, pos: Position, move: Move) -> bool:
        to = move.to
        color_turn = board.color_turn

        starting_rank = pos[0] == (6 if color_turn == PieceColor.WHITE else 1)
        to_is_empty = not board[to]
        return starting_rank and to_is_empty

    @staticmethod
    def front_short_valid(board: Board, pos: Position, move: Move) -> bool:
        to = move.to
        to_piece = board[to]

        return to_piece.type == PieceType.EMPTY


class Checks:
    @staticmethod
    def to_pos_in_grid(move: Move) -> bool:
        to = move.to

        return max(to) <= 7 and min(to) >= 0

    @staticmethod
    def is_color_turn(board: Board, pos: Position) -> bool:
        color_turn = board.color_turn
        piece = board[pos]

        return color_turn == piece.color

    @staticmethod
    def to_empty_or_enemy(board: Board, pos: Position, move: Move) -> bool:
        to = move.to
        color_turn = board.color_turn
        to_piece = board[to]

        return to_piece.color != color_turn or to_piece.color == PieceColor.NONE

    @staticmethod
    def no_obstruction(board: Board, pos: Position, move: Move) -> bool:
        to = move.to
        pos_x, pos_y = pos
        to_x, to_y = to

        X = range(pos_x, to_x, 1 if to_x > pos_x else -1)
        Y = range(pos_y, to_y, 1 if to_y > pos_y else -1)

        # short moves and knights have no obstruction
        if min(len(X), len(Y)) == 1:
            return True

        # If both exist, diag move
        if X and Y:
            obstructions = [1 for xy in zip(X, Y) if xy != pos and board[xy]]

        # If x exists, perp col, same column
        elif X:
            obstructions = [1 for x in X if (x, pos_y) != pos and board[x, pos_y]]

        # Else y exists, perp col, same row
        else:
            obstructions = [1 for y in Y if (pos_x, y) != pos and board[pos_x, y]]

        return not obstructions

    @staticmethod
    def king_safe_at_end(board: Board, pos: Position, move: Move) -> bool:
        to, flag = move.to, move.flag

        end_board = deepcopy(board)
        end_board[to] = end_board[pos]
        del end_board[pos]

        if flag == Flag.ENPASSANT:
            del end_board[end_board.enpassant_target]

        return KingCheck.safe(end_board, end_board.king_pos, board.color_turn)

    @staticmethod
    def final(board: Board, pos: Position, move: Move) -> bool:
        return (
            Checks.to_pos_in_grid(move)
            and Checks.is_color_turn(board, pos)
            and Checks.to_empty_or_enemy(board, pos, move)
            and Checks.no_obstruction(board, pos, move)
            and Checks.king_safe_at_end(board, pos, move)
        )
