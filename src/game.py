import pygame
import logging
from src.board import (
    MINE_VALUE,
    EMPTY_VALUE,
    Board,
)
from src.board_analyzer import BoardAnalyzer, UnsolvableBoardError
from src.solver import HybridMinesweeperSolver, REVEAL
from enum import Enum

TILE_SIZE = 40
CHROME_HEIGHT = 60
CONTROL_BAR_Y = 10


logger = logging.getLogger(__name__)

class MouseButton(Enum):
    LEFT = 1
    MIDDLE = 2
    RIGHT = 3

class MinesweeperGame:
    def __init__(self, board: Board, recommended_start_square=None):
        self.board: Board = board
        self.recommended_start_square: tuple[int, int] | None = recommended_start_square
        self.width = board.num_cols * TILE_SIZE
        self.height = board.num_rows * TILE_SIZE + CHROME_HEIGHT
        self._control_y = board.num_rows * TILE_SIZE + CONTROL_BAR_Y
        self._tiles: dict[str, pygame.Surface] = {}

        pygame.init()
        self.window: pygame.Surface = pygame.display.set_mode((self.width, self.height))
        self._load_tiles()
        self.init_window()

    def _load_tiles(self) -> None:
        names = [
            "0", "1", "2", "3", "4", "5", "6", "7", "8",
            "-1", "mine", "flag", "unrevealed",
            "reset", "reset_pressed", "solve", "solve_pressed", "win",
        ]
        for name in names:
            img = pygame.image.load(f"assets/{name}.png")
            self._tiles[name] = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))

    def _reset_button_rect(self) -> pygame.Rect:
        return pygame.Rect(self.width // 2 - 60, self._control_y, TILE_SIZE, TILE_SIZE)

    def _solver_button_rect(self) -> pygame.Rect:
        return pygame.Rect(self.width // 2 + 20, self._control_y, TILE_SIZE, TILE_SIZE)

    def init_window(self):
        self.window.fill((200, 200, 200))

        pygame.display.set_caption("MineSweeper")
        grid_bottom = self.board.num_rows * TILE_SIZE
        pygame.draw.line(self.window, (0, 0, 0), (0, grid_bottom), (self.width, grid_bottom), 2)

        self.window.blit(self._tiles["reset"], self._reset_button_rect())
        self.window.blit(self._tiles["solve"], self._solver_button_rect())

        unrevealed = self._tiles["unrevealed"]
        for y in range(self.board.num_rows):
            for x in range(self.board.num_cols):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(self.window, (255, 255, 255), rect, 1)
                self.window.blit(unrevealed, (x * TILE_SIZE, y * TILE_SIZE))

        if self.recommended_start_square:
            x, y = self.recommended_start_square
            rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(self.window, (0, 255, 0), rect, 4)

        pygame.display.flip()
        return self.window

    def show_win(self) -> None:
        self.window.blit(self._tiles["win"], self._reset_button_rect())
        pygame.display.update(self._reset_button_rect())

    def chord_from_square(self, x: int, y: int):
        """
        Reveal surrounding unflagged squares if the chord is legal.

        A chord is legal only when every surrounding flag is actually a
        mine — otherwise it would lose, so it is refused (does nothing),
        like a king move into check.
        """
        if self.board.get_num_surrounding_flags(x, y) != self.board.get_square_value(x, y):
            logger.debug(f"Square ({x}, {y}) is not satisfied, cannot chord")
            return

        neighbors = self.board.get_surrounding_squares(x, y)
        flagged = self.board.get_flagged_squares()
        revealed = self.board.get_revealed_squares()

        for nx, ny in neighbors:
            if (nx, ny) in flagged and self.board.get_square_value(nx, ny) != MINE_VALUE:
                logger.debug(f"Square ({nx}, {ny}) is flagged but not a mine, cannot chord")
                return

        for nx, ny in neighbors:
            if (nx, ny) in revealed or (nx, ny) in flagged:
                continue
            if self.board.get_square_value(nx, ny) == EMPTY_VALUE:
                self.reveal_square(nx, ny)
                self.chord_from_square(nx, ny)
            elif self.board.get_square_value(nx, ny) != MINE_VALUE:
                self.reveal_square(nx, ny)

    def reveal_square(self, x: int, y: int) -> None:
        """
        Reveal a square on the board
        - x: x coordinate of square
        - y: y coordinate of square
        - return: None
        """
        if (x, y) in self.board.get_revealed_squares():
            logger.debug(f"Warning: Square ({x}, {y}) is revealed, cannot reveal")
            return

        if (x, y) in self.board.get_flagged_squares():
            logger.debug(f"Warning: Square ({x}, {y}) is flagged, cannot reveal")
            return

        value = self.board.get_square_value(x, y)
        self.board.reveal_square(x, y)
        self.set_square(x, y, str(value))

    def set_square(self, x: int, y: int, value: str) -> None:
        """
        Draw a square on the board
        - x: x coordinate of square
        - y: y coordinate of square
        - value: asset key of square
        - return: None
        """
        img = self._tiles[value]
        self.window.blit(img, (x * TILE_SIZE, y * TILE_SIZE))
        pygame.display.update(pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))

    def reveal_all_mines(self):
        """
        Reveal all mines on the board when the game is over
        """
        for y in range(self.board.num_rows):
            for x in range(self.board.num_cols):
                square_value = self.board.get_square_value(x, y)
                if square_value != MINE_VALUE:
                    continue
                if (x, y) == self.board.detonated_mine:
                    self.set_square(x, y, "-1")
                else:
                    self.set_square(x, y, "mine")

    def toggle_flag_square(self, x: int, y: int) -> None:
        """
        Toggle a flag on a square on the board
        - x: x coordinate of square
        - y: y coordinate of square
        - return: None
        """
        if (x, y) in self.board.get_revealed_squares():
            logger.debug(f"Square ({x}, {y}) is revealed, cannot flag")
            return

        if (x, y) in self.board.get_flagged_squares():
            self.board.unflag_square(x, y)
            self.set_square(x, y, "unrevealed")
        else:
            self.board.flag_square(x, y)
            self.set_square(x, y, "flag")

    def _pump_generation(self, attempt: int) -> None:
        pygame.event.pump()
        pygame.display.set_caption(f"MineSweeper — generating ({attempt})")

    def reset_game(self) -> None:
        """
        Reset the board to the initial state with a new solvable board.
        """
        logger.debug("Resetting game")
        self.window.blit(self._tiles["reset_pressed"], self._reset_button_rect())
        pygame.display.update(self._reset_button_rect())

        logger.debug("Generating solvable board...")
        try:
            self.board, start_square = BoardAnalyzer.generate_solvable_board(
                num_rows=self.board.num_rows,
                num_cols=self.board.num_cols,
                num_mines=self.board.num_mines,
                on_attempt=self._pump_generation,
            )
            self.recommended_start_square = start_square
            logger.debug(f"Generated solvable board! Starting square: {start_square}")
        except UnsolvableBoardError:
            logger.debug("Could not generate a solvable board; keeping the current one")
            pygame.display.set_caption("MineSweeper")
            self.window.blit(self._tiles["reset"], self._reset_button_rect())
            pygame.display.update(self._reset_button_rect())
            return

        pygame.display.set_caption("MineSweeper")
        self.window = self.init_window()
        pygame.display.update()

    def reset_button_clicked(self, pos) -> bool:
        """
        Checks if the reset button is clicked
        - pos: (x, y) coordinates of mouse click
        - return: True if reset button is clicked, False otherwise
        """
        return self._reset_button_rect().collidepoint(pos)

    def solver_button_clicked(self, pos) -> bool:
        """
        Checks if the solver button is clicked
        - pos: (x, y) coordinates of mouse click
        - return: True if solver button is clicked, False otherwise
        """
        return self._solver_button_rect().collidepoint(pos)

    def run_solver(self):
        """
        Runs the automated solver on the current board state
        """
        logger.debug("Running solver...")
        self.window.blit(self._tiles["solve_pressed"], self._solver_button_rect())
        pygame.display.update(self._solver_button_rect())
        solver = HybridMinesweeperSolver(self.board)
        solver.solve(on_move=self._render_move)
        self.window.blit(self._tiles["solve"], self._solver_button_rect())
        pygame.display.update()

    def _render_move(self, x: int, y: int, action: str) -> None:
        """
        The UI adapter at the solver seam: render a move as it is
        applied to the board.
        """
        if action == REVEAL:
            self.set_square(x, y, str(self.board.get_square_value(x, y)))
        else:
            self.set_square(x, y, "flag")

    def handle_mouse_click(self, event):
        pos = pygame.mouse.get_pos()

        if self.reset_button_clicked(pos):
            self.reset_game()
            return

        if self.solver_button_clicked(pos):
            self.run_solver()
            return

        x = pos[0] // TILE_SIZE
        y = pos[1] // TILE_SIZE
        if y > self.board.num_rows - 1 or y < 0 or x > self.board.num_cols - 1 or x < 0:
            return

        if event.button == MouseButton.RIGHT.value:
            self.toggle_flag_square(x, y)

        elif event.button == MouseButton.LEFT.value:
            if (x, y) in self.board.get_flagged_squares():
                logger.debug(f"Square ({x}, {y}) is flagged, cannot reveal")
                return
            if (x, y) in self.board.get_revealed_squares():
                self.chord_from_square(x, y)
                return

            self.reveal_square(x, y)
            if self.board.get_square_value(x, y) == EMPTY_VALUE:
                self.chord_from_square(x, y)
