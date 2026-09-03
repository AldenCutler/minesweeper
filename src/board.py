import logging
import random
from enum import Enum

EMPTY_VALUE = 0
MINE_VALUE = -1

SURROUNDING_SQUARE_OFFSETS = [
    (-1, -1), (-1, 0), (-1, 1),
    ( 0, -1),          ( 0, 1),
    ( 1, -1), ( 1, 0), ( 1, 1)
]

logger = logging.getLogger(__name__)


class SquareState(Enum):
    UNREVEALED = 0
    REVEALED = 1
    FLAGGED = 2


class Board:
    """
    The Minesweeper board: the clue grid plus each square's state.

    Sole owner of the board representation. Callers interact through this
    interface (values, states, and copies of square lists); the underlying
    grid and state lists are private. Square coordinates are always (x, y);
    the grid is indexed [y][x].
    """

    def __init__(self, num_rows: int, num_cols: int, num_mines: int):
        if num_mines < 0 or num_mines >= num_rows * num_cols:
            raise ValueError(
                f"mine count {num_mines} does not fit a {num_rows}x{num_cols} board"
            )
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.num_mines = num_mines
        self._grid = self._generate_grid()
        self._revealed: list[tuple[int, int]] = []
        self._flagged: list[tuple[int, int]] = []
        self.detonated_mine: tuple[int, int] | None = None

    @classmethod
    def _from_state(
        cls,
        num_rows: int,
        num_cols: int,
        num_mines: int,
        grid: list[list[int]],
        revealed,
        flagged,
        detonated_mine=None,
    ) -> "Board":
        """Construct a board from existing state (no mine placement)."""
        board = cls.__new__(cls)
        board.num_rows = num_rows
        board.num_cols = num_cols
        board.num_mines = num_mines
        board._grid = [row[:] for row in grid]
        board._revealed = list(revealed)
        board._flagged = list(flagged)
        board.detonated_mine = detonated_mine
        return board

    @classmethod
    def from_grid(
        cls,
        grid: list[list[int]],
        revealed=(),
        flagged=(),
    ) -> "Board":
        """
        Build a board from an explicit clue grid.

        Dimensions and mine count are derived from the grid, which makes
        this the natural way to write small boards in tests and analysis.
        """
        mine_count = sum(row.count(MINE_VALUE) for row in grid)
        return cls._from_state(
            num_rows=len(grid),
            num_cols=len(grid[0]) if grid else 0,
            num_mines=mine_count,
            grid=grid,
            revealed=revealed,
            flagged=flagged,
        )

    @staticmethod
    def generate_mine_pos(num_rows: int, num_cols: int) -> tuple[int, int]:
        """
        Generates a random mine position
        - return: (x, y) coordinates of a square for a mine
        """
        x = random.randint(0, num_cols - 1)
        y = random.randint(0, num_rows - 1)
        return (x, y)

    @staticmethod
    def get_num_mines_for_board_size(num_rows: int, num_cols: int) -> int:
        """
        Returns the standard mine count for a classic Minesweeper size
        (beginner 9x9, intermediate 16x16, expert 16x30).
        - return: number of mines
        """
        if num_rows == 16 and num_cols == 30:
            return 99
        elif num_rows == 9 and num_cols == 9:
            return 10
        elif num_rows == 16 and num_cols == 16:
            return 40
        else:
            raise ValueError(
                f"no standard mine count for a {num_rows}x{num_cols} board; "
                "pass an explicit mine count instead"
            )

    def clone(self) -> "Board":
        """
        Returns an independent deep copy: same layout and state, no shared
        mutable internals.
        """
        return Board._from_state(
            num_rows=self.num_rows,
            num_cols=self.num_cols,
            num_mines=self.num_mines,
            grid=self._grid,
            revealed=self._revealed,
            flagged=self._flagged,
            detonated_mine=self.detonated_mine,
        )

    def _generate_grid(self) -> list[list[int]]:
        """
        Generates the clue grid: mines placed at random, every other square
        holding the count of its surrounding mines.
        """
        grid = [[EMPTY_VALUE for _ in range(self.num_cols)] for _ in range(self.num_rows)]

        # add mines
        mines = []
        for _ in range(self.num_mines):
            x, y = Board.generate_mine_pos(self.num_rows, self.num_cols)
            while (x, y) in mines:
                # if there's already a mine at x, y, generate new x, y
                x, y = Board.generate_mine_pos(self.num_rows, self.num_cols)
            mines.append((x, y))
            grid[y][x] = MINE_VALUE

        # add numbers
        self._grid = grid
        for y in range(self.num_rows):
            for x in range(self.num_cols):
                if grid[y][x] == MINE_VALUE:
                    continue
                grid[y][x] = self.get_num_surrounding_mines(x, y)

        return grid

    def _validate_square(self, x: int, y: int) -> None:
        if not (0 <= x < self.num_cols and 0 <= y < self.num_rows):
            raise IndexError(f"square ({x}, {y}) is outside the board")

    def get_revealed_squares(self) -> list[tuple[int, int]]:
        """
        Returns a copy of the list of revealed squares
        - return: list of (x, y) coordinates of revealed squares
        """
        return list(self._revealed)

    def get_flagged_squares(self) -> list[tuple[int, int]]:
        """
        Returns a copy of the list of flagged squares
        - return: list of (x, y) coordinates of flagged squares
        """
        return list(self._flagged)

    def reveal_square(self, x: int, y: int) -> None:
        """
        Reveal a square on the board
        - x: x coordinate of square
        - y: y coordinate of square
        - return: None
        """
        self._validate_square(x, y)

        if (x, y) in self._revealed:
            logger.debug(f"Warning: Square ({x}, {y}) is revealed, cannot reveal")
            return

        if (x, y) in self._flagged:
            logger.debug(f"Warning: Square ({x}, {y}) is flagged, cannot reveal")
            return

        self._revealed.append((x, y))
        if self.get_square_value(x, y) == MINE_VALUE:
            self.detonated_mine = (x, y)

    def flag_square(self, x: int, y: int) -> None:
        """
        Flag a square on the board
        - x: x coordinate of square
        - y: y coordinate of square
        - return: None
        """
        self._validate_square(x, y)

        if (x, y) in self._revealed:
            logger.debug(f"Warning: Square ({x}, {y}) is revealed, cannot flag")
            return

        if (x, y) in self._flagged:
            logger.debug(f"Warning: Square ({x}, {y}) is already flagged, cannot flag")
            return

        self._flagged.append((x, y))

    def unflag_square(self, x: int, y: int) -> None:
        """
        Unflag a square on the board
        - x: x coordinate of square
        - y: y coordinate of square
        - return: None
        """
        self._validate_square(x, y)

        if (x, y) not in self._flagged:
            logger.debug(f"Warning: Square ({x}, {y}) is not flagged, cannot unflag")
            return

        self._flagged.remove((x, y))

    def get_square_value(self, x: int, y: int) -> int:
        """
        Returns the clue value of the square at (x, y)
        - x: x coordinate of square
        - y: y coordinate of square
        - return: number of surrounding mines, or MINE_VALUE for a mine
        """
        self._validate_square(x, y)
        return self._grid[y][x]

    def get_square_state(self, x: int, y: int) -> SquareState:
        """
        Returns the state of the square at (x, y)
        - x: x coordinate of square
        - y: y coordinate of square
        - return: SquareState of square
        """
        self._validate_square(x, y)
        if (x, y) in self._revealed:
            return SquareState.REVEALED
        elif (x, y) in self._flagged:
            return SquareState.FLAGGED
        else:
            return SquareState.UNREVEALED

    def check_win(self) -> bool:
        """
        Checks if the game is won
        - return: True if game is won, False otherwise
        """
        if len(self._revealed) == (self.num_rows * self.num_cols) - self.num_mines:
            return True
        return False

    def check_lose(self) -> bool:
        """
        Checks if the game is lost
        - return: True if game is lost, False otherwise
        """
        return self.detonated_mine is not None

    def get_num_surrounding_mines(self, x: int, y: int) -> int:
        """
        Counts the mines surrounding a square
        - x: x coordinate of square
        - y: y coordinate of square
        - return: number of mines in surrounding squares
        """
        num_mines = 0
        for new_x, new_y in self.get_surrounding_squares(x, y):
            if self._grid[new_y][new_x] == MINE_VALUE:
                num_mines += 1
        return num_mines

    def get_num_surrounding_flags(self, x: int, y: int) -> int:
        """
        Counts the flags surrounding a square
        - x: x coordinate of square
        - y: y coordinate of square
        - return: number of flags in surrounding squares
        """
        num_flags = 0
        for new_x, new_y in self.get_surrounding_squares(x, y):
            if (new_x, new_y) in self._flagged:
                num_flags += 1
        return num_flags

    def get_surrounding_squares(self, x: int, y: int) -> list[tuple[int, int]]:
        """
        Returns a list of surrounding squares
        - x: x coordinate of square
        - y: y coordinate of square
        - return: list of (x, y) coordinates of surrounding squares
        """
        surrounding_squares = []
        for dx, dy in SURROUNDING_SQUARE_OFFSETS:
            new_x = x + dx
            new_y = y + dy
            if new_y < 0 or new_y > self.num_rows - 1 or new_x < 0 or new_x > self.num_cols - 1:
                continue
            surrounding_squares.append((new_x, new_y))
        return surrounding_squares
