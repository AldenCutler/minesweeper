from src.board import Board, MINE_VALUE, EMPTY_VALUE
from src.game import MinesweeperGame
from src.solver import MinesweeperSolver
import pytest

def test_solver_set_logic_pattern():
    # Setup a scenario to test set-based logic
    class MockBoard(Board):
        def __init__(self):
            self.num_rows = 3
            self.num_cols = 3
            self.num_mines = 3
            self.revealed = [(0,0), (1,1), (1,2)]
            self.flagged = [(1,0), (0,2)]
            self.board = [
                [1, 1, 1],
                [2, 4, 2],
                [1, 2, 1]
            ]
        def get_square_state(self, x, y):
            from src.board import SquareState
            if (x, y) in self.revealed:
                return SquareState.REVEALED
            if (x, y) in self.flagged:
                return SquareState.FLAGGED
            return SquareState.UNREVEALED

    mock_board = MockBoard()
    game = MinesweeperGame(board=mock_board)
    solver = MinesweeperSolver(game=game)
    
    solver.solve_board()
    
    # Based on the logic: (2,0) should be flagged as a mine
    assert (2,0) in mock_board.flagged

def test_solver_subset_safe_square():
    """
    Test that the solver can identify a safe square by comparing the
    mine requirements of a square and its subset.
    
    Scenario 1:
    1 | 2 | U
    1 | 2 | U
    F | 4 | U
    2 | F | F
    Top unrevealed square (2,0) is safe because the bottom unrevealed 
    squares (2,1) and (2,2) must contain all remaining mines.
    """
    class MockBoardSubset(Board):
        def __init__(self):
            self.num_rows = 4
            self.num_cols = 3
            self.num_mines = 5
            self.revealed = [(0,0), (1,0), (0,1), (1,1), (1,2), (0,3)]
            self.flagged = [(0,2), (1,3), (2,3)]
            self.board = [
                [1, 2, 0], # row 0
                [1, 2, 0], # row 1
                [-1, 4, 0],# row 2
                [2, -1, -1] # row 3
            ]
        def get_square_state(self, x, y):
            from src.board import SquareState
            if (x, y) in self.revealed:
                return SquareState.REVEALED
            if (x, y) in self.flagged:
                return SquareState.FLAGGED
            return SquareState.UNREVEALED

    mock_board = MockBoardSubset()
    game = MinesweeperGame(board=mock_board)
    solver = MinesweeperSolver(game=game)
    
    solver.solve_board()
    
    assert (2,0) in mock_board.revealed

def test_solver_subset_safe_right_square():
    """
    Test subset logic where a square on the edge of a set is 
    identified as safe.
    
    3 | U | U | U
    F | 2 | 2 | F
    """
    class MockBoardSubset2(Board):
        def __init__(self):
            self.num_rows = 2
            self.num_cols = 4
            self.num_mines = 4
            self.revealed = [(0,0), (1,1), (2,1)]
            self.flagged = [(0,1), (3,1)]
            self.board = [
                [3, 0, 0, 0],
                [-1, 2, 2, -1]
            ]
        def get_square_state(self, x, y):
            from src.board import SquareState
            if (x, y) in self.revealed:
                return SquareState.REVEALED
            if (x, y) in self.flagged:
                return SquareState.FLAGGED
            return SquareState.UNREVEALED

    mock_board = MockBoardSubset2()
    game = MinesweeperGame(board=mock_board)
    solver = MinesweeperSolver(game=game)
    
    solver.solve_board()
    
    assert (3,0) in mock_board.revealed
