from src.board import Board
from src.game import MinesweeperGame
from src.solver import MinesweeperSolver

board = Board(num_rows=16, num_cols=30)
game = MinesweeperGame(board=board)
solver = MinesweeperSolver(game=game)









def test_is_safe_to_reveal():
    pass

