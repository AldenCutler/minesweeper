from src.board import Board
from src.solver import MinesweeperSolver
from src.solver_gauss import GaussianMinesweeperSolver
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.game import MinesweeperGame


class HybridMinesweeperSolver:
    """
    A hybrid solver that combines basic deterministic logic with Gaussian elimination.

    Strategy:
    1. Start with the basic solver (simple rules + subset logic)
    2. If it makes progress, continue with the basic solver
    3. When it gets stuck, switch to the Gaussian solver (linear algebra)
    4. If Gaussian makes progress, go back to the basic solver
    5. Repeat until the board is solved or no solver can make progress
    """

    def __init__(self, game: Any, headless: bool = False):
        self.game = game
        self.board: Board = game.board
        self.headless = headless
        self.basic_solver = MinesweeperSolver(game, headless=headless)
        self.gaussian_solver = GaussianMinesweeperSolver(game, headless=headless)

    def solve_board(self) -> bool:
        """
        Solve the Minesweeper game using a hybrid approach.

        The solver repeatedly alternates between:
        1. Basic solver - fast, handles simple patterns
        2. Gaussian solver - powerful, handles complex constraints

        Stops when the game is won/lost or neither solver can make progress.
        
        Returns:
            True if the board was solved, False if it got stuck or lost.
        """
        while not self.board.check_win() and not self.board.check_lose():
            # Try basic solver first (it's faster for simple patterns)
            basic_progress = self._run_basic_solver_once()

            if self.board.check_win() or self.board.check_lose():
                break

            if basic_progress:
                # Basic solver made progress, continue with it
                continue

            # Basic solver got stuck, try Gaussian solver
            gaussian_progress = self._run_gaussian_solver_once()

            if self.board.check_win() or self.board.check_lose():
                break

            if not gaussian_progress:
                # Neither solver could make progress
                break

        # Return True only if the board was won
        return self.board.check_win()

    def _run_basic_solver_once(self) -> bool:
        """
        Run one iteration of the basic solver's logic.

        Returns:
            True if progress was made, False otherwise.
        """
        progress_made = False

        # Apply simple local rules
        for y in range(self.board.num_rows):
            for x in range(self.board.num_cols):
                if self.basic_solver.simple_resolve_surrounding(x, y):
                    progress_made = True

        if self.board.check_win() or self.board.check_lose():
            return progress_made

        # Apply subset/set-difference logic
        if not progress_made:
            if self.basic_solver.apply_set_logic():
                progress_made = True

        return progress_made

    def _run_gaussian_solver_once(self) -> bool:
        """
        Run one iteration of the Gaussian solver's logic.

        Returns:
            True if progress was made, False otherwise.
        """
        return self.gaussian_solver.matrix_resolve()
