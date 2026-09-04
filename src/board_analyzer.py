"""
Board analysis: certifying that a Minesweeper board can be solved
without guessing, and choosing a starting square.

The analyzer works on Board clones: the board handed in is never
modified, and the certification solver plays by the same rules a player
would — it only sees revealed information.
"""
from typing import Callable, Optional

from src.board import Board, SquareState, EMPTY_VALUE
from src.solver import HybridMinesweeperSolver

DEFAULT_GENERATION_ATTEMPTS = 200


class UnsolvableBoardError(Exception):
    """Raised when no no-guessing board is found within the attempt cap."""


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

        Tries unique openings, largest first (a bigger flood is more
        likely to leave a solvable frontier). Returns the first that
        leads to a fully solvable board.

        Args:
            board: The board to analyze (will not be modified)

        Returns:
            (x, y) of the best starting square, or None if no good
            starting square exists
        """
        for start_x, start_y in BoardAnalyzer._unique_openings(board):
            work = board.clone()
            work.reveal_square(start_x, start_y)
            BoardAnalyzer._chord_from_square(work, start_x, start_y)
            if work.check_win() or HybridMinesweeperSolver(work).solve():
                return (start_x, start_y)
        return None

    @staticmethod
    def generate_solvable_board(
        num_rows: int,
        num_cols: int,
        num_mines: int,
        max_attempts: int = DEFAULT_GENERATION_ATTEMPTS,
        on_attempt: Optional[Callable[[int], None]] = None,
    ) -> tuple[Board, tuple[int, int]]:
        """
        Generate boards until one is solvable without guessing.

        Args:
            on_attempt: optional callback(attempt_number) after each miss,
                used by the UI to pump the event queue.

        Returns:
            (board, starting_square)

        Raises:
            UnsolvableBoardError: if no board is found within max_attempts.
        """
        for attempt in range(1, max_attempts + 1):
            board = Board(num_rows=num_rows, num_cols=num_cols, num_mines=num_mines)
            start_square = BoardAnalyzer.find_best_starting_square(board)
            if start_square:
                return board, start_square
            if on_attempt:
                on_attempt(attempt)
        raise UnsolvableBoardError(
            f"no no-guessing {num_rows}x{num_cols}/{num_mines} board "
            f"in {max_attempts} attempts"
        )

    @staticmethod
    def _unique_openings(board: Board) -> list[tuple[int, int]]:
        """
        One representative empty square per flood region, largest
        openings first so certification tries the most informative
        first click before smaller ones.
        """
        seen: set[tuple[int, int]] = set()
        openings: list[tuple[int, tuple[int, int]]] = []
        for y in range(board.num_rows):
            for x in range(board.num_cols):
                if (x, y) in seen:
                    continue
                if board.get_square_value(x, y) != EMPTY_VALUE:
                    continue
                region = BoardAnalyzer._flood_region(board, x, y)
                seen.update(region)
                openings.append((len(region), (x, y)))
        openings.sort(key=lambda item: item[0], reverse=True)
        return [start for _, start in openings]

    @staticmethod
    def _flood_region(board: Board, start_x: int, start_y: int) -> set[tuple[int, int]]:
        stack = [(start_x, start_y)]
        region: set[tuple[int, int]] = set()
        while stack:
            x, y = stack.pop()
            if (x, y) in region:
                continue
            if board.get_square_value(x, y) != EMPTY_VALUE:
                continue
            region.add((x, y))
            for nx, ny in board.get_surrounding_squares(x, y):
                if (nx, ny) not in region:
                    stack.append((nx, ny))
        return region

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

            if board.get_square_value(new_x, new_y) == EMPTY_VALUE:
                BoardAnalyzer._chord_from_square(board, new_x, new_y)
