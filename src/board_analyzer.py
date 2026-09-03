"""
Board analysis: certifying that a Minesweeper board can be solved
without guessing, and choosing a starting square.

The analyzer works on Board clones: the board handed in is never
modified, and the certification solver plays by the same rules a player
would — it only sees revealed information.
"""
from typing import Optional

from src.board import Board, SquareState, EMPTY_VALUE
from src.solver import HybridMinesweeperSolver


class BoardAnalyzer:
    """
    Analyzes Minesweeper boards to determine solvability and find good
    starting moves.
    """

    @staticmethod
    def is_solvable(board: Board) -> bool:
        """
        Check if a board can be solved without guessing.

        Args:
            board: The board to check (will not be modified)

        Returns:
            True if a starting square exists from which the board is
            solvable with deterministic logic, False otherwise
        """
        return BoardAnalyzer.find_best_starting_square(board) is not None

    @staticmethod
    def find_best_starting_square(board: Board) -> Optional[tuple[int, int]]:
        """
        Find the best starting square for a no-guessing game.

        Tries each empty square (0 mines) as a starting position.
        Returns the first one that leads to a fully solvable board.

        Args:
            board: The board to analyze (will not be modified)

        Returns:
            (x, y) of the best starting square, or None if no good
            starting square exists
        """
        for start_x, start_y in BoardAnalyzer._empty_squares(board):
            # Solve a clone so the original board is never modified.
            work = board.clone()

            # Reveal the empty square and chord from it, mimicking a
            # player's first click.
            work.reveal_square(start_x, start_y)
            BoardAnalyzer._chord_from_square(work, start_x, start_y)

            if HybridMinesweeperSolver(work).solve():
                return (start_x, start_y)

        return None

    @staticmethod
    def _empty_squares(board: Board) -> list[tuple[int, int]]:
        squares = []
        for y in range(board.num_rows):
            for x in range(board.num_cols):
                if board.get_square_value(x, y) == EMPTY_VALUE:
                    squares.append((x, y))
        return squares

    @staticmethod
    def _chord_from_square(board: Board, x: int, y: int) -> None:
        """
        Flood-reveal from an empty square: reveal its neighbors, and
        recurse from any neighbor that is also empty. Used to simulate a
        player's first click on a board clone.
        """
        if board.get_square_value(x, y) != EMPTY_VALUE:
            return

        for new_x, new_y in board.get_surrounding_squares(x, y):
            if board.get_square_state(new_x, new_y) != SquareState.UNREVEALED:
                continue

            board.reveal_square(new_x, new_y)

            # Recursively chord if the revealed square is also empty
            if board.get_square_value(new_x, new_y) == EMPTY_VALUE:
                BoardAnalyzer._chord_from_square(board, new_x, new_y)
