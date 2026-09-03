"""
Solver tests run fully headless: strategies operate on a Board, and the
driver applies moves to it. No pygame, no game object.
"""
import pytest

from src.board import Board, MINE_VALUE, SquareState
from src.solver import (
    Solver,
    HybridMinesweeperSolver,
    SimpleRulesStrategy,
    SetLogicStrategy,
    REVEAL,
    FLAG,
)

M = MINE_VALUE


def basic_solver(board: Board) -> Solver:
    """The fast chain: basic rules + subset logic, no linear algebra."""
    return Solver(board, [SimpleRulesStrategy(), SetLogicStrategy()])


def test_solver_set_logic_pattern():
    board = Board.from_grid(
        grid=[
            [1, 1, 1],
            [2, 4, 2],
            [1, 2, 1],
        ],
        revealed=[(0, 0), (1, 1), (1, 2)],
        flagged=[(1, 0), (0, 2)],
    )
    basic_solver(board).solve()

    # Based on the logic: (2,0) should be flagged as a mine
    assert board.get_square_state(2, 0) == SquareState.FLAGGED


def test_solver_subset_safe_square():
    """
    Subset logic: one revealed square constrains squares A, and a second
    revealed square constrains A plus squares B — so B must be safe.

    Revealed squares (1,0) and (1,1) are both "1". The squares
    {(0,0),(2,0),(0,1),(2,1)} form A; B adds {(0,2),(1,2),(2,2)}, which
    therefore contains no mines.
    """
    board = Board.from_grid(
        grid=[
            [0, 1, M],
            [0, 1, 1],
            [0, 0, 0],
        ],
        revealed=[(1, 0), (1, 1)],
    )
    basic_solver(board).solve()

    assert board.get_square_state(0, 2) == SquareState.REVEALED
    assert board.get_square_state(1, 2) == SquareState.REVEALED
    assert board.get_square_state(2, 2) == SquareState.REVEALED


def test_solver_subset_safe_right_square():
    """
    Subset logic where a square on the edge of a set is identified as
    safe.

    3 | U | U | U
    F | 2 | 2 | F
    """
    board = Board.from_grid(
        grid=[
            [3, 0, 0, 0],
            [M, 2, 2, M],
        ],
        revealed=[(0, 0), (1, 1), (2, 1)],
        flagged=[(0, 1), (3, 1)],
    )
    basic_solver(board).solve()

    assert board.get_square_state(3, 0) == SquareState.REVEALED


def test_strategies_are_pure():
    """deduce() must not mutate the board, and must be deterministic."""
    board = Board.from_grid(
        grid=[
            [3, 0, 0, 0],
            [M, 2, 2, M],
        ],
        revealed=[(0, 0), (1, 1), (2, 1)],
        flagged=[(0, 1), (3, 1)],
    )
    revealed_before = board.get_revealed_squares()
    flagged_before = board.get_flagged_squares()

    first = SetLogicStrategy().deduce(board)
    second = SetLogicStrategy().deduce(board)
    SimpleRulesStrategy().deduce(board)

    assert board.get_revealed_squares() == revealed_before
    assert board.get_flagged_squares() == flagged_before
    assert first == second


def test_gaussian_strategy_deduces_without_touching_the_board():
    """The Gaussian strategy finds the forced safe square and stays pure."""
    from src.solver_gauss import GaussianStrategy

    board = Board.from_grid(
        grid=[
            [3, 0, 0, 0],
            [M, 2, 2, M],
        ],
        revealed=[(0, 0), (1, 1), (2, 1)],
        flagged=[(0, 1), (3, 1)],
    )
    moves = GaussianStrategy().deduce(board)

    assert (3, 0, REVEAL) in moves
    assert board.get_square_state(3, 0) == SquareState.UNREVEALED


def test_solver_reports_moves_as_they_are_applied():
    """The on_move seam gives the UI (and tests) every move as data."""
    board = Board.from_grid(
        grid=[
            [3, 0, 0, 0],
            [M, 2, 2, M],
        ],
        revealed=[(0, 0), (1, 1), (2, 1)],
        flagged=[(0, 1), (3, 1)],
    )
    seen = []
    basic_solver(board).solve(on_move=lambda x, y, action: seen.append((x, y, action)))

    assert seen == [(3, 0, REVEAL)]


def test_hybrid_solver_never_acts_on_hidden_information():
    """
    Regression: the hybrid driver once called the basic rules on every
    square instead of only REVEALED ones, so an unrevealed 0-value square
    would flood-reveal its neighbors — the solver played with information
    no player can see, and the no-guessing certification cheated.

    Here the only revealed square is (1,0), a "1". Nothing is deducible,
    so the correct behavior is to make no moves at all.
    """
    board = Board.from_grid(
        grid=[
            [M, 1, 0],
            [1, 1, 0],
        ],
        revealed=[(1, 0)],
    )
    solved = HybridMinesweeperSolver(board).solve()

    assert solved is False
    assert board.get_square_state(2, 0) == SquareState.UNREVEALED
    assert board.get_square_state(2, 1) == SquareState.UNREVEALED
    assert board.get_square_state(1, 1) == SquareState.UNREVEALED
    assert board.get_square_state(0, 0) == SquareState.UNREVEALED
    assert board.check_lose() is False


def test_hybrid_solver_solves_deterministic_board():
    """End-to-end: the chain reveals the safe square and flags both mines.
    (All non-mine squares except (3,0) start revealed; the solver must
    reveal (3,0) and flag (0,0) and (3,3).)"""
    non_mine_squares = [
        (1, 0), (2, 0),  # (3, 0) intentionally left for the solver
        (0, 1), (1, 1), (2, 1), (3, 1),
        (0, 2), (1, 2), (2, 2), (3, 2),
        (0, 3), (1, 3), (2, 3),
    ]
    board = Board.from_grid(
        grid=[
            [M, 1, 0, 0],
            [1, 1, 0, 0],
            [0, 0, 1, 1],
            [0, 0, 1, M],
        ],
        revealed=non_mine_squares,
    )
    solved = HybridMinesweeperSolver(board).solve()

    assert solved is True
    assert board.check_win() is True
    # The safe square was revealed and both mines ended up flagged
    assert board.get_square_state(3, 0) == SquareState.REVEALED
    assert board.get_square_state(0, 0) == SquareState.FLAGGED
    assert board.get_square_state(3, 3) == SquareState.FLAGGED
