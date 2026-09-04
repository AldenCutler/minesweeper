"""
Analyzer tests: certifying no-guessing boards. The certification solver
works on a clone, so the board under test is never modified.
"""
import pytest

from src.board import Board, MINE_VALUE, SquareState
from src.board_analyzer import BoardAnalyzer, UnsolvableBoardError

M = MINE_VALUE


def test_certifies_solvable_board_without_touching_it():
    board = Board.from_grid(
        grid=[
            [M, 1, 0, 0],
            [1, 1, 0, 0],
            [0, 0, 1, 1],
            [0, 0, 1, M],
        ],
    )

    assert BoardAnalyzer.is_solvable(board) is True
    # (2,0) is the first empty square in scan order, and floods to a win
    assert BoardAnalyzer.find_best_starting_square(board) == (2, 0)

    # The analysis must leave the board exactly as it found it
    assert board.get_revealed_squares() == []
    assert board.get_flagged_squares() == []


def test_rejects_board_where_every_first_click_is_a_guess():
    # 1 mine in a 1x2 strip: no empty square exists, so a player must
    # guess from the first click. Not a no-guessing board.
    board = Board.from_grid(grid=[[M, 1]])

    assert BoardAnalyzer.find_best_starting_square(board) is None
    assert BoardAnalyzer.is_solvable(board) is False


def test_generate_solvable_board_raises_when_capped():
    with pytest.raises(UnsolvableBoardError):
        BoardAnalyzer.generate_solvable_board(1, 2, 1, max_attempts=3)
