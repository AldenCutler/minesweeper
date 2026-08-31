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
    def __init__(self, num_rows, num_cols):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.num_mines = Board.get_num_mines_for_board_size(num_rows, num_cols)
        self.revealed: list[tuple[int, int]] = []
        self.flagged: list[tuple[int, int]] = []
        self.board = self.generate_internal_board()
        
    @staticmethod
    def generate_mine_pos(num_rows: int, num_cols: int):
        """
        Generates a random mine position
        - return: (y, x) coordinates of mine
        """
        x = random.randint(0, num_cols - 1)
        y = random.randint(0, num_rows - 1)
        return (x, y)
    
    @staticmethod
    def get_num_mines_for_board_size(num_rows: int, num_cols: int):
        """
        Returns the number of mines based on the board size
        - return: number of mines
        """
        if num_rows == 16 and num_cols == 30:
            return 99
        elif num_rows == 9 and num_cols == 9:
            return 10
        elif num_rows == 16 and num_cols == 16:
            return 40
        else:
            raise ValueError("Invalid board size")

    def generate_internal_board(self):
        """
        Generates the board
        - return: 2D list of that represents the board
        """
        board = []
        # set all squares to empty
        for y in range(self.num_rows):
            row = []
            for x in range(self.num_cols):
                row.append(EMPTY_VALUE)
            board.append(row)
        
        # add mines
        mines = []
        for _ in range(self.num_mines):
            x, y = Board.generate_mine_pos(self.num_rows, self.num_cols)
            while (x, y) in mines:      
                # if there's already a mine at x, y, generate new x, y
                x, y = Board.generate_mine_pos(self.num_rows, self.num_cols)
            mines.append((x, y))
            board[y][x] = MINE_VALUE
        
        # add numbers
        for y in range(self.num_rows):
            for x in range(self.num_cols):
                if board[y][x] == MINE_VALUE:
                    continue
                board[y][x] = self.get_num_surrounding_mines(x, y, board)
        
        return board

    def get_revealed_squares(self) -> list[tuple[int, int]]:
        """
        Returns a list of revealed squares
        - return: list of (x, y) coordinates of revealed squares
        """
        return self.revealed
    
    def get_flagged_squares(self) -> list[tuple[int, int]]:
        """
        Returns a list of flagged squares
        - return: list of (x, y) coordinates of flagged squares
        """
        return self.flagged

    def reveal_square(self, x: int, y: int) -> None:
        """
        Reveal a square on the board
        - x: x coordinate of square
        - y: y coordinate of square
        - return: None
        """
        if (x, y) in self.revealed:
            logger.debug(f"Warning: Square ({x}, {y}) is revealed, cannot reveal")
            return
        
        if (x, y) in self.flagged:
            logger.debug(f"Warning: Square ({x}, {y}) is flagged, cannot reveal")
            return

        self.revealed.append((x, y))
    
    def flag_square(self, x: int, y: int) -> None:
        """
        Flag a square on the board
        - x: x coordinate of square
        - y: y coordinate of square
        - return: None
        """
        if (x, y) in self.revealed:
            logger.debug(f"Warning: Square ({x}, {y}) is revealed, cannot flag")
            return
        
        if (x, y) in self.flagged:
            logger.debug(f"Warning: Square ({x}, {y}) is already flagged, cannot flag")
            return
        
        self.flagged.append((x, y))
        
    def unflag_square(self, x: int, y: int) -> None:
        """
        Unflag a square on the board
        - x: x coordinate of square
        - y: y coordinate of square
        - return: None
        """
        if (x, y) not in self.flagged:
            logger.debug(f"Warning: Square ({x}, {y}) is not flagged, cannot unflag")
            return
        
        self.flagged.remove((x, y))

    def get_square_value(self, x: int, y: int) -> int:
        """
        Returns the value of the square at (x, y)
        - x: x coordinate of square
        - y: y coordinate of square
        - return: int value of square
        """
        return self.board[y][x]
    
    def get_square_state(self, x: int, y: int) -> SquareState:
        """
        Returns the state of the square at (x, y)
        - x: x coordinate of square
        - y: y coordinate of square
        - return: SquareState of square
        """
        if (x, y) in self.revealed:
            return SquareState.REVEALED
        elif (x, y) in self.flagged:
            return SquareState.FLAGGED
        else:
            return SquareState.UNREVEALED
        
    def check_win(self) -> bool:
        """
        Checks if the game is won
        - return: True if game is won, False otherwise
        """
        if len(self.revealed) == (self.num_rows * self.num_cols) - self.num_mines:
            return True
        return False
    
    def check_lose(self) -> bool:
        """
        Checks if the game is lost
        - return: True if game is lost, False otherwise
        """
        for square in self.revealed:
            square_value = self.get_square_value(square[0], square[1])
            if square_value == MINE_VALUE:
                return True
        return False

    def get_num_surrounding_mines(self, x: int, y: int, board: list[list[int]]) -> int:
        """
        Checks surrounding squares for mines
        - board: 2D list that represents the board
        - y: y coordinate of square
        - x: x coordinate of square
        - return: number of mines in surrounding squares
        
        This function is only called during board generation.
        At the time it is called, the board is not fully generated, 
        which is why the board is passed in rather than using self.board, 
        """
        num_mines = 0
        for dx, dy in SURROUNDING_SQUARE_OFFSETS:
            new_x = x + dx
            new_y = y + dy
            if new_y < 0 or new_y > self.num_rows - 1 or new_x < 0 or new_x > self.num_cols - 1:
                continue
            if board[new_y][new_x] == MINE_VALUE:
                num_mines += 1
        return num_mines
    
    def get_num_surrounding_flags(self, x: int, y: int) -> int:
        """
        Checks surrounding squares for flags
        - y: y coordinate of square
        - x: x coordinate of square
        - return: number of flags in surrounding squares
        """
        num_flags = 0
        for dx, dy in SURROUNDING_SQUARE_OFFSETS:
            new_x = x + dx
            new_y = y + dy
            if new_y < 0 or new_y > self.num_rows - 1 or new_x < 0 or new_x > self.num_cols - 1:
                continue
            if (new_x, new_y) in self.flagged:
                num_flags += 1
        return num_flags

    def get_surrounding_squares(self, x: int, y: int) -> list[tuple[int, int]]:
        """
        Returns a list of surrounding squares
        - y: y coordinate of square
        - x: x coordinate of square
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
    