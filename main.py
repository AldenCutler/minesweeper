from src.game import MinesweeperGame
from src.board import Board
from src.board_analyzer import BoardAnalyzer
import logging
import argparse
import pygame

logger = logging.getLogger(__name__)

def generate_solvable_board(num_rows: int, num_cols: int) -> tuple[Board, tuple[int, int]]:
    """
    Generate a solvable Minesweeper board.
    
    Keeps generating boards until one is found that can be solved
    without guessing, then returns the board and the recommended
    starting square.
    
    Args:
        num_rows: Number of rows in the board
        num_cols: Number of columns in the board
        
    Returns:
        (board, (start_x, start_y)) - the solvable board and starting square
    """
    while True:
        board = Board(num_rows=num_rows, num_cols=num_cols)
        
        logger.debug("Checking if board is solvable...")
        if BoardAnalyzer.is_solvable(board):
            # Board is solvable, find the best starting square
            start_square = BoardAnalyzer.find_best_starting_square(board)
            if start_square:
                logger.debug(f"Board is solvable! Starting square: {start_square}")
                return board, start_square
            else:
                logger.debug("Board is solvable but no good starting square found, regenerating...")
        else:
            logger.debug("Board is not solvable, regenerating...")

def play(game: MinesweeperGame):
    """
    Main game loop
    """
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            
            if game.board.check_lose():
                game.reveal_all_mines()
                return game_over(game)
            
            if game.board.check_win():
                return game_over(game)
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game.reset_game()

            if event.type == pygame.MOUSEBUTTONDOWN:
                game.handle_mouse_click(event)
                
                
def game_over(game: MinesweeperGame):
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if game.reset_button_clicked(pos):
                    game.reset_game()
                    return play(game)

if __name__ == "__main__":
    
    args = argparse.ArgumentParser(description="Play Minesweeper")
    args.add_argument("--rows", type=int, default=16, help="Number of rows in the board")
    args.add_argument("--cols", type=int, default=30, help="Number of columns in the board")
    args.add_argument("--mines", type=int, default=99, help="Number of mines in the board")
    args.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = args.parse_args()
    
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        
    board, start_square = generate_solvable_board(
        num_rows=args.rows,
        num_cols=args.cols
    )
    
    game = MinesweeperGame(
        board=board,
        num_rows=args.rows,
        num_cols=args.cols,
        num_mines=args.mines,
        recommended_start_square=start_square
    )
    
    play(game)