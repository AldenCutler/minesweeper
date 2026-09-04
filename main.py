from src.game import MinesweeperGame
from src.board import Board
from src.board_analyzer import BoardAnalyzer, UnsolvableBoardError
import logging
import argparse
import pygame
import sys

logger = logging.getLogger(__name__)

FPS = 60


def play(game: MinesweeperGame):
    """
    Main game loop
    """
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game.reset_game()

            if event.type == pygame.MOUSEBUTTONDOWN:
                game.handle_mouse_click(event)

        if game.board.check_lose():
            game.reveal_all_mines()
            return game_over(game)

        if game.board.check_win():
            game.show_win()
            return game_over(game)

        clock.tick(FPS)


def game_over(game: MinesweeperGame):
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game.reset_game()
                    return play(game)

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if game.reset_button_clicked(pos):
                    game.reset_game()
                    return play(game)

        clock.tick(FPS)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Play Minesweeper")
    parser.add_argument("--rows", type=int, default=16, help="Number of rows in the board")
    parser.add_argument("--cols", type=int, default=30, help="Number of columns in the board")
    parser.add_argument("--mines", type=int, default=None,
                      help="Number of mines (classic count for 9x9/16x16/16x30, else expert density)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    if args.rows < 1 or args.cols < 1:
        parser.error("rows and cols must be at least 1")

    num_mines = args.mines
    if num_mines is None:
        num_mines = Board.default_mine_count(args.rows, args.cols)

    try:
        board, start_square = BoardAnalyzer.generate_solvable_board(
            num_rows=args.rows,
            num_cols=args.cols,
            num_mines=num_mines,
        )
    except UnsolvableBoardError as exc:
        parser.error(str(exc))
    except ValueError as exc:
        parser.error(str(exc))

    game = MinesweeperGame(
        board=board,
        recommended_start_square=start_square
    )

    play(game)
