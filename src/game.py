import pygame
import logging
import time
from src.board import (
    MINE_VALUE, 
    EMPTY_VALUE, 
    SURROUNDING_SQUARE_OFFSETS, 
    Board
)
from src.board_analyzer import BoardAnalyzer
from src.solver_hybrid import HybridMinesweeperSolver
from enum import Enum

TILE_SIZE = 40


logger = logging.getLogger(__name__)

class MouseButton(Enum):
    LEFT = 1
    MIDDLE = 2
    RIGHT = 3

class MinesweeperGame:
    def __init__(self, board: Board, width=1200, height=700, num_mines=99, num_rows=16, num_cols=30, recommended_start_square=None):
        self.width:     int            = width
        self.height:    int            = height
        self.board:     Board          = board
        self.num_mines: int            = num_mines
        self.num_rows:  int            = num_rows
        self.num_cols:  int            = num_cols
        self.recommended_start_square: tuple[int, int] | None = recommended_start_square
        
        pygame.init()
        self.window:    pygame.Surface = pygame.display.set_mode((self.width, self.height))
        self.init_window()
        
    def init_window(self):
        self.window.fill((200, 200, 200))
        
        pygame.display.set_caption("MineSweeper")
        pygame.draw.line(self.window, (0, 0, 0), (0, 640), (self.width, 640), 2)

        # draw reset button
        reset = pygame.image.load("assets/reset.png")
        reset = pygame.transform.scale(reset, (TILE_SIZE, TILE_SIZE))
        self.window.blit(reset, (self.width // 2 - 60, 650))
        
        # draw solver button
        solver_btn = pygame.image.load("assets/solve.png")
        solver_btn = pygame.transform.scale(solver_btn, (TILE_SIZE, TILE_SIZE))
        self.window.blit(solver_btn, (self.width // 2 + 20, 650))
        
        # draw grid
        for y in range(self.num_rows):
            for x in range(self.num_cols):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(self.window, (255, 255, 255), rect, 1)
                
                unrevealed = pygame.image.load("assets/unrevealed.png")
                unrevealed = pygame.transform.scale(unrevealed, (TILE_SIZE, TILE_SIZE))
                self.window.blit(unrevealed, (x * TILE_SIZE, y * TILE_SIZE))
        
        # Highlight recommended starting square with a colored border
        if self.recommended_start_square:
            x, y = self.recommended_start_square
            rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            # Draw a bright green border to highlight the recommended square
            pygame.draw.rect(self.window, (0, 255, 0), rect, 4)

        pygame.display.flip()

        return self.window
        
    def chord_from_square(self, x: int, y: int):
        """
        Reveal all surrounding squares except for flagged squares
        """
        # can only chord from a satisfied square
        # a square is satisfied when the number of surrounding flags is equal
        # to the number on the square
        if self.board.get_num_surrounding_flags(x, y) != self.board.get_square_value(x, y):
            logger.debug(f"Square ({x}, {y}) is not satisfied, cannot chord")
            return
        
        for offset in SURROUNDING_SQUARE_OFFSETS:
            new_x = x + offset[0]
            new_y = y + offset[1]
            # out of bounds checks
            if new_y < 0 or new_y > self.num_rows - 1 or new_x < 0 or new_x > self.num_cols - 1:
                continue
            if (new_x, new_y) in self.board.get_revealed_squares():
                continue
            if (new_x, new_y) in self.board.get_flagged_squares():
                continue
            
            # check that flagged squares are actually mines, if not, do not chord
            if (new_x, new_y) in self.board.get_flagged_squares():
                if self.board.get_square_value(new_x, new_y) != MINE_VALUE:
                    logger.debug(f"Square ({new_x}, {new_y}) is flagged but not a mine, cannot chord")
                    return
            
            # if the square is empty, reveal it and chord from it
            if self.board.get_square_value(new_x, new_y) == EMPTY_VALUE:
                self.reveal_square(new_x, new_y)
                self.chord_from_square(new_x, new_y)
            elif self.board.get_square_value(new_x, new_y) != MINE_VALUE:
                self.reveal_square(new_x, new_y)
             
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
        Reveal a square on the board
        - x: x coordinate of square
        - y: y coordinate of square
        - value: value of square
        - return: None
        """
        img = pygame.image.load(f"assets/{value}.png")
        img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
        self.window.blit(img, (x * TILE_SIZE, y * TILE_SIZE))
        pygame.display.update(pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
                
    def reveal_all_mines(self):
        """
        Reveal all mines on the board when the game is over
        """
        for y in range(self.num_rows):
            for x in range(self.num_cols):
                square_value = self.board.get_square_value(x, y)
                if square_value != MINE_VALUE:
                    continue
                if (x, y) == self.board.get_revealed_squares()[-1]:
                    # keep the last revealed mine as a red mine
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
    
    def reset_game(self) -> None:
        """
        Reset the board to the initial state with a new solvable board.
        Generates boards until one is found that can be solved without guessing.
        """
        logger.debug("Resetting game")
        reset_pressed = pygame.image.load("assets/reset_pressed.png")
        reset_pressed = pygame.transform.scale(reset_pressed, (TILE_SIZE, TILE_SIZE))
        self.window.blit(reset_pressed, (self.width // 2 - 60, 650))
        pygame.display.update()
        
        time.sleep(0.1)
        
        # Generate a solvable board with a recommended starting square
        logger.debug("Generating solvable board...")
        while True:
            self.board = Board(num_rows=self.num_rows, num_cols=self.num_cols)
            
            if BoardAnalyzer.is_solvable(self.board):
                start_square = BoardAnalyzer.find_best_starting_square(self.board)
                if start_square:
                    logger.debug(f"Generated solvable board! Starting square: {start_square}")
                    self.recommended_start_square = start_square
                    break
                else:
                    logger.debug("Board is solvable but no good starting square found, regenerating...")
            else:
                logger.debug("Board is not solvable, regenerating...")
        
        self.window = self.init_window()
        
        pygame.display.update()

    def reset_button_clicked(self, pos) -> bool:
        """
        Checks if the reset button is clicked
        - pos: (x, y) coordinates of mouse click
        - return: True if reset button is clicked, False otherwise
        """
        # TODO make this work with different board sizes
        if pos[0] >= self.width // 2 - 60 and pos[0] <= self.width // 2 - 20 and pos[1] >= 640 and pos[1] <= 690:
            return True
        return False

    def solver_button_clicked(self, pos) -> bool:
        """
        Checks if the solver button is clicked
        - pos: (x, y) coordinates of mouse click
        - return: True if solver button is clicked, False otherwise
        """
        if pos[0] >= self.width // 2 + 20 and pos[0] <= self.width // 2 + 60 and pos[1] >= 650 and pos[1] <= 690:
            return True
        return False

    def run_solver(self):
        """
        Runs the automated solver on the current board state
        """
        logger.debug("Running solver...")
        solver = HybridMinesweeperSolver(self)
        solver.solve_board()
        pygame.display.update()

    def handle_mouse_click(self, event):
        # get x, y coordinates of clicked square
        pos = pygame.mouse.get_pos()
        
        # reset if reset button is clicked
        if self.reset_button_clicked(pos):
            self.reset_game()
            return

        # solve if solver button is clicked
        if self.solver_button_clicked(pos):
            self.run_solver()
            return
        
        # get x, y coordinates of clicked square
        x = pos[0] // TILE_SIZE
        y = pos[1] // TILE_SIZE
        if y > self.num_rows - 1 or y < 0 or x > self.num_cols - 1 or x < 0:
            return
        
        
        # right click (flag)
        if event.button == MouseButton.RIGHT.value:
            self.toggle_flag_square(x, y)
                
        # left click (reveal)
        elif event.button == MouseButton.LEFT.value:
            # if square is flagged, do nothing
            if (x, y) in self.board.get_flagged_squares():
                logger.debug(f"Square ({x}, {y}) is flagged, cannot reveal")
                return
            # if square is revealed, chord from square
            if (x, y) in self.board.get_revealed_squares():
                self.chord_from_square(x, y)
                return
                
            self.reveal_square(x, y)
            if self.board.get_square_value(x, y) == EMPTY_VALUE:
                self.chord_from_square(x, y)