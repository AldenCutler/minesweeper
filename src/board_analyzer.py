from src.board import Board, EMPTY_VALUE, SURROUNDING_SQUARE_OFFSETS
from src.solver_hybrid import HybridMinesweeperSolver
from typing import Optional


class BoardAnalyzer:
    """
    Analyzes Minesweeper boards to determine solvability and find good starting moves.
    """

    @staticmethod
    def is_solvable(board: Board) -> bool:
        """
        Check if a board can be solved without guessing.
        
        Args:
            board: The board to check (will not be modified)
            
        Returns:
            True if the board is solvable, False otherwise
        """
        # Create a copy of the board state
        board_copy = BoardAnalyzer._copy_board_state(board)
        
        # Create a mock game object
        class MockGame:
            def __init__(self, board):
                self.board = board
        
        solver = HybridMinesweeperSolver(MockGame(board_copy), headless=True)
        return solver.solve_board()

    @staticmethod
    def find_best_starting_square(board: Board) -> Optional[tuple[int, int]]:
        """
        Find the best starting square for a no-guessing game.
        
        Tries each empty square (0 mines) as a starting position.
        Returns the first one that leads to a fully solvable board.
        
        Args:
            board: The board to analyze (will not be modified)
            
        Returns:
            (x, y) of the best starting square, or None if no good starting square exists
        """
        # Collect all empty squares
        empty_squares = []
        for y in range(board.num_rows):
            for x in range(board.num_cols):
                if board.get_square_value(x, y) == EMPTY_VALUE:
                    empty_squares.append((x, y))

        # Try each empty square as a starting position
        for start_x, start_y in empty_squares:
            # Create a copy of the board
            board_copy = BoardAnalyzer._copy_board_state(board)
            
            # Reveal the empty square and chord from it
            board_copy.reveal_square(start_x, start_y)
            BoardAnalyzer._chord_from_square(board_copy, start_x, start_y)
            
            # Check if this leads to a solvable board
            class MockGame:
                def __init__(self, board):
                    self.board = board
            
            solver = HybridMinesweeperSolver(MockGame(board_copy), headless=True)
            if solver.solve_board():
                return (start_x, start_y)
        
        return None

    @staticmethod
    def _copy_board_state(board: Board) -> Board:
        """Create a deep copy of a board's state."""
        board_copy = Board(board.num_rows, board.num_cols)
        board_copy.board = [row[:] for row in board.board]
        board_copy.num_mines = board.num_mines
        board_copy.revealed = board.revealed[:]
        board_copy.flagged = board.flagged[:]
        return board_copy

    @staticmethod
    def _chord_from_square(board: Board, x: int, y: int) -> None:
        """
        Reveal all surrounding squares of an empty square.
        Similar to the game's chord_from_square but for headless mode.
        """
        if board.get_square_value(x, y) != EMPTY_VALUE:
            return
        
        for dx, dy in SURROUNDING_SQUARE_OFFSETS:
            new_x = x + dx
            new_y = y + dy
            
            # Out of bounds check
            if new_y < 0 or new_y >= board.num_rows or new_x < 0 or new_x >= board.num_cols:
                continue
            
            # Already revealed or flagged
            if (new_x, new_y) in board.revealed or (new_x, new_y) in board.flagged:
                continue
            
            board.reveal_square(new_x, new_y)
            
            # Recursively chord if the revealed square is also empty
            if board.get_square_value(new_x, new_y) == EMPTY_VALUE:
                BoardAnalyzer._chord_from_square(board, new_x, new_y)
