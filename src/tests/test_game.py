import os
import types
import pytest

from ..board import Board, MINE_VALUE, EMPTY_VALUE, SquareState
from ..game import MinesweeperGame, MouseButton


def test_all_referenced_assets_exist():
	"""set_square() loads assets/{value}.png — every drawable value must exist."""
	repo_root = os.path.join(os.path.dirname(__file__), "..", "..")
	for value in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "-1", "mine",
				  "flag", "unrevealed", "reset", "reset_pressed", "solve",
				  "solve_pressed", "win"]:
		path = os.path.join(repo_root, "assets", f"{value}.png")
		assert os.path.exists(path), f"missing asset: {path}"


class DummySurface:
	def fill(self, *args, **kwargs):
		return None

	def blit(self, *args, **kwargs):
		return None


class DummyRect:
	def __init__(self, *args):
		if len(args) == 4:
			self.x, self.y, self.w, self.h = args
		else:
			self.x = self.y = self.w = self.h = 0

	def collidepoint(self, pos):
		px, py = pos
		return self.x <= px < self.x + self.w and self.y <= py < self.y + self.h


def setup_dummy_pygame(monkeypatch):
	"""Monkeypatch the pygame API used by src.game to avoid opening a real window."""
	import src.game as game_mod

	monkeypatch.setattr(game_mod.pygame, "init", lambda: None)
	monkeypatch.setattr(game_mod.pygame.display, "set_mode", lambda size: DummySurface())
	monkeypatch.setattr(game_mod.pygame.display, "set_caption", lambda *a, **k: None)
	monkeypatch.setattr(game_mod.pygame.draw, "line", lambda *a, **k: None)
	monkeypatch.setattr(game_mod.pygame.draw, "rect", lambda *a, **k: None)
	monkeypatch.setattr(game_mod.pygame.image, "load", lambda *a, **k: DummySurface())
	monkeypatch.setattr(game_mod.pygame.transform, "scale", lambda img, size: img)
	monkeypatch.setattr(game_mod.pygame.display, "flip", lambda: None)
	monkeypatch.setattr(game_mod.pygame.display, "update", lambda *a, **k: None)
	monkeypatch.setattr(game_mod.pygame, "Rect", DummyRect)
	monkeypatch.setattr(game_mod.pygame.mouse, "get_pos", lambda: (0, 0))
	monkeypatch.setattr(game_mod.pygame.event, "pump", lambda: None)


def make_small_board(revealed=()):
	"""A 3x3 mine-free board built from an explicit grid."""
	return Board.from_grid(
		grid=[[EMPTY_VALUE for _ in range(3)] for _ in range(3)],
		revealed=list(revealed),
	)


def test_reveal_square_and_set_square_called(monkeypatch):
	setup_dummy_pygame(monkeypatch)
	board = make_small_board()

	calls = []
	monkeypatch.setattr(MinesweeperGame, "set_square", lambda self, x, y, v: calls.append((x, y, v)))

	game = MinesweeperGame(board)
	game.reveal_square(1, 1)
	assert board.get_square_state(1, 1) == SquareState.REVEALED
	assert calls and calls[-1] == (1, 1, str(board.get_square_value(1, 1)))


def test_toggle_flag_square(monkeypatch):
	setup_dummy_pygame(monkeypatch)
	board = make_small_board()

	calls = []
	monkeypatch.setattr(MinesweeperGame, "set_square", lambda self, x, y, v: calls.append((x, y, v)))

	game = MinesweeperGame(board)
	game.toggle_flag_square(0, 0)
	assert board.get_square_state(0, 0) == SquareState.FLAGGED
	assert calls[-1] == (0, 0, "flag")

	game.toggle_flag_square(0, 0)
	assert board.get_square_state(0, 0) == SquareState.UNREVEALED
	assert calls[-1] == (0, 0, "unrevealed")


def test_chord_from_square_reveals_neighbors(monkeypatch):
	setup_dummy_pygame(monkeypatch)
	board = make_small_board(revealed=[(1, 1)])

	game = MinesweeperGame(board)
	monkeypatch.setattr(MinesweeperGame, "set_square", lambda self, x, y, v: None)

	game.chord_from_square(1, 1)
	assert len(board.get_revealed_squares()) == 9


def test_illegal_chord_does_nothing(monkeypatch):
	"""A chord that would hit a mine (wrong flag) is refused, not a loss."""
	setup_dummy_pygame(monkeypatch)
	board = Board.from_grid(
		grid=[
			[1, MINE_VALUE],
			[1, 1],
		],
		revealed=[(0, 0)],
		flagged=[(0, 1)],
	)
	game = MinesweeperGame(board)
	monkeypatch.setattr(MinesweeperGame, "set_square", lambda self, x, y, v: None)

	game.chord_from_square(0, 0)

	assert board.get_square_state(1, 0) == SquareState.UNREVEALED
	assert board.check_lose() is False


def test_reset_button_clicked_bounds(monkeypatch):
	setup_dummy_pygame(monkeypatch)
	board = make_small_board()
	game = MinesweeperGame(board)

	rect = game._reset_button_rect()
	assert game.reset_button_clicked((rect.x + 5, rect.y + 5)) is True
	assert game.reset_button_clicked((0, 0)) is False


def test_handle_mouse_click_left_and_right(monkeypatch):
	setup_dummy_pygame(monkeypatch)
	board = make_small_board()

	import src.game as game_mod
	monkeypatch.setattr(game_mod.pygame.mouse, "get_pos", lambda: (10, 10))

	game = MinesweeperGame(board)

	event = types.SimpleNamespace(button=MouseButton.RIGHT.value)
	game.handle_mouse_click(event)
	assert board.get_square_state(0, 0) == SquareState.FLAGGED

	prev_revealed = board.get_revealed_squares()
	event = types.SimpleNamespace(button=MouseButton.LEFT.value)
	game.handle_mouse_click(event)
	assert board.get_revealed_squares() == prev_revealed


def test_run_solver_applies_moves_through_the_render_seam(monkeypatch):
	setup_dummy_pygame(monkeypatch)
	board = Board.from_grid(
		grid=[
			[3, 0, 0, 0],
			[MINE_VALUE, 2, 2, MINE_VALUE],
		],
		revealed=[(0, 0), (1, 1), (2, 1)],
		flagged=[(0, 1), (3, 1)],
	)

	calls = []
	monkeypatch.setattr(MinesweeperGame, "set_square", lambda self, x, y, v: calls.append((x, y, v)))

	game = MinesweeperGame(board)
	game.run_solver()

	assert board.get_square_state(3, 0) == SquareState.REVEALED
	assert (3, 0, "0") in calls
