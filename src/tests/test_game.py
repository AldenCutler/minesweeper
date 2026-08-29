import types
import pytest

from ..board import Board, MINE_VALUE, EMPTY_VALUE
from ..game import MinesweeperGame, MouseButton


class DummySurface:
	def fill(self, *args, **kwargs):
		return None

	def blit(self, *args, **kwargs):
		return None


def setup_dummy_pygame(monkeypatch):
	"""Monkeypatch the pygame API used by src.game to avoid opening a real window."""
	import src.game as game_mod

	# simple no-op implementations for the pieces used by MinesweeperGame
	monkeypatch.setattr(game_mod.pygame, "init", lambda: None)
	monkeypatch.setattr(game_mod.pygame.display, "set_mode", lambda size: DummySurface())
	monkeypatch.setattr(game_mod.pygame.display, "set_caption", lambda *a, **k: None)
	monkeypatch.setattr(game_mod.pygame.draw, "line", lambda *a, **k: None)
	monkeypatch.setattr(game_mod.pygame.draw, "rect", lambda *a, **k: None)
	monkeypatch.setattr(game_mod.pygame.image, "load", lambda *a, **k: DummySurface())
	monkeypatch.setattr(game_mod.pygame.transform, "scale", lambda img, size: img)
	monkeypatch.setattr(game_mod.pygame.display, "flip", lambda: None)
	monkeypatch.setattr(game_mod.pygame.display, "update", lambda *a, **k: None)
	monkeypatch.setattr(game_mod.pygame, "Rect", lambda *args: args)
	# default mouse pos; tests will override as needed
	monkeypatch.setattr(game_mod.pygame.mouse, "get_pos", lambda: (0, 0))


def make_small_board():
	# create a 9x9 board but we'll shrink it to a 3x3 logical board for tests
	board = Board(num_rows=9, num_cols=9)
	board.num_rows = 3
	board.num_cols = 3
	board.num_mines = 0
	board.board = [[EMPTY_VALUE for _ in range(3)] for _ in range(3)]
	board.revealed = []
	board.flagged = []
	return board


def test_reveal_square_and_set_square_called(monkeypatch):
	setup_dummy_pygame(monkeypatch)
	board = make_small_board()

	calls = []
	monkeypatch.setattr(MinesweeperGame, "set_square", lambda self, x, y, v: calls.append((x, y, v)))

	game = MinesweeperGame(board, width=120, height=120, num_mines=0, num_rows=3, num_cols=3)
	# reveal (1,1)
	game.reveal_square(1, 1)
	assert (1, 1) in board.revealed
	assert calls and calls[-1] == (1, 1, str(board.get_square_value(1, 1)))


def test_toggle_flag_square(monkeypatch):
	setup_dummy_pygame(monkeypatch)
	board = make_small_board()

	calls = []
	monkeypatch.setattr(MinesweeperGame, "set_square", lambda self, x, y, v: calls.append((x, y, v)))

	game = MinesweeperGame(board, width=120, height=120, num_mines=0, num_rows=3, num_cols=3)
	game.toggle_flag_square(0, 0)
	assert (0, 0) in board.flagged
	assert calls[-1] == (0, 0, "flag")

	# toggle again to remove flag
	game.toggle_flag_square(0, 0)
	assert (0, 0) not in board.flagged
	assert calls[-1] == (0, 0, "unrevealed")


def test_chord_from_square_reveals_neighbors(monkeypatch):
	setup_dummy_pygame(monkeypatch)
	board = make_small_board()
	# make center an empty square and mark it revealed
	board.board = [[EMPTY_VALUE for _ in range(3)] for _ in range(3)]
	board.num_mines = 0
	board.revealed = [(1, 1)]

	game = MinesweeperGame(board, width=120, height=120, num_mines=0, num_rows=3, num_cols=3)
	# avoid image operations
	monkeypatch.setattr(MinesweeperGame, "set_square", lambda self, x, y, v: None)

	game.chord_from_square(1, 1)
	# every square should be revealed after chording an empty center
	assert len(board.revealed) == 9


def test_reset_button_clicked_bounds(monkeypatch):
	setup_dummy_pygame(monkeypatch)
	board = make_small_board()
	game = MinesweeperGame(board, width=120, height=120, num_mines=0, num_rows=3, num_cols=3)

	# center reset button is at (width//2, ~670)
	assert game.reset_button_clicked((game.width // 2, 660)) is True
	assert game.reset_button_clicked((0, 0)) is False


def test_handle_mouse_click_left_and_right(monkeypatch):
	setup_dummy_pygame(monkeypatch)
	board = make_small_board()

	# patch mouse position to be within the first tile
	import src.game as game_mod
	monkeypatch.setattr(game_mod.pygame.mouse, "get_pos", lambda: (10, 10))

	game = MinesweeperGame(board, width=120, height=120, num_mines=0, num_rows=3, num_cols=3)

	# right click should flag
	event = types.SimpleNamespace(button=MouseButton.RIGHT.value)
	game.handle_mouse_click(event)
	assert (0, 0) in board.flagged

	# left click on flagged square should do nothing (no additional reveals)
	prev_revealed = list(board.revealed)
	event = types.SimpleNamespace(button=MouseButton.LEFT.value)
	game.handle_mouse_click(event)
	assert board.revealed == prev_revealed

