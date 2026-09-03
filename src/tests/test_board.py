import pytest
from ..board import Board, MINE_VALUE, EMPTY_VALUE, SquareState

M = MINE_VALUE


def test_generate_mine_pos():
    num_rows = 16
    num_cols = 30
    x, y = Board.generate_mine_pos(num_rows, num_cols)
    assert 0 <= x < num_cols
    assert 0 <= y < num_rows


def test_get_num_mines_for_board_size():
    assert Board.get_num_mines_for_board_size(16, 30) == 99
    assert Board.get_num_mines_for_board_size(9, 9) == 10
    assert Board.get_num_mines_for_board_size(16, 16) == 40
    with pytest.raises(ValueError):
        Board.get_num_mines_for_board_size(10, 10)


def test_generated_board_clues_are_consistent():
    board = Board(num_rows=16, num_cols=30, num_mines=99)
    mine_count = 0
    for y in range(board.num_rows):
        for x in range(board.num_cols):
            if board.get_square_value(x, y) == M:
                mine_count += 1
            else:
                assert board.get_square_value(x, y) == board.get_num_surrounding_mines(x, y)
    assert mine_count == 99


def test_mine_count_must_fit_the_board():
    with pytest.raises(ValueError):
        Board(num_rows=3, num_cols=3, num_mines=9)


def test_from_grid_derives_layout_and_state():
    board = Board.from_grid(
        grid=[
            [1, M],
            [1, 1],
        ],
        revealed=[(0, 0)],
        flagged=[(1, 0)],
    )
    assert board.num_rows == 2
    assert board.num_cols == 2
    assert board.num_mines == 1
    assert board.get_square_value(1, 0) == M
    assert board.get_square_state(0, 0) == SquareState.REVEALED
    assert board.get_square_state(1, 0) == SquareState.FLAGGED
    assert board.get_square_state(1, 1) == SquareState.UNREVEALED


def test_square_lists_are_returned_as_copies():
    board = Board.from_grid(grid=[[1, 1], [1, M]], revealed=[(0, 0)], flagged=[(0, 1)])

    revealed = board.get_revealed_squares()
    revealed.append((1, 1))
    flagged = board.get_flagged_squares()
    flagged.clear()

    assert board.get_revealed_squares() == [(0, 0)]
    assert board.get_flagged_squares() == [(0, 1)]


def test_reveal_square():
    board = Board.from_grid(grid=[[1, 1], [1, M]])
    board.reveal_square(0, 0)
    assert board.get_square_state(0, 0) == SquareState.REVEALED
    # Revealing the same square again should not change the revealed list
    board.reveal_square(0, 0)
    assert board.get_revealed_squares().count((0, 0)) == 1
    # A flagged square cannot be revealed
    board.flag_square(0, 1)
    board.reveal_square(0, 1)
    assert board.get_square_state(0, 1) == SquareState.FLAGGED


def test_reveal_mine_detonates_and_loses():
    board = Board.from_grid(grid=[[1, 1], [1, M]])
    assert board.check_lose() is False
    board.reveal_square(1, 1)
    assert board.detonated_mine == (1, 1)
    assert board.check_lose() is True


def test_flag_square():
    board = Board.from_grid(grid=[[1, 1], [1, M]])
    board.flag_square(0, 0)
    assert board.get_square_state(0, 0) == SquareState.FLAGGED
    # Flagging the same square again should not change the flagged list
    board.flag_square(0, 0)
    assert board.get_flagged_squares().count((0, 0)) == 1
    # A revealed square cannot be flagged
    board.reveal_square(1, 0)
    board.flag_square(1, 0)
    assert board.get_square_state(1, 0) == SquareState.REVEALED


def test_unflag_square():
    board = Board.from_grid(grid=[[1, 1], [1, M]])
    board.flag_square(0, 0)
    assert board.get_square_state(0, 0) == SquareState.FLAGGED
    board.unflag_square(0, 0)
    assert board.get_square_state(0, 0) == SquareState.UNREVEALED


def test_check_win():
    grid = [
        [M, 1],
        [1, 1],
    ]
    # Reveal all non-mine squares
    board = Board.from_grid(grid=grid)
    board.reveal_square(1, 0)
    board.reveal_square(0, 1)
    board.reveal_square(1, 1)
    assert board.check_win() is True

    # If any non-mine square is left unrevealed, the game is not won
    board = Board.from_grid(grid=grid)
    board.reveal_square(1, 0)
    board.reveal_square(0, 1)
    assert board.check_win() is False


def test_get_num_surrounding_mines():
    board = Board.from_grid(grid=[
        [1, 1, 1],
        [1, M, 1],
        [1, 1, 1],
    ])
    assert board.get_num_surrounding_mines(0, 0) == 1
    assert board.get_num_surrounding_mines(0, 1) == 1
    assert board.get_num_surrounding_mines(0, 2) == 1
    assert board.get_num_surrounding_mines(1, 0) == 1
    assert board.get_num_surrounding_mines(1, 2) == 1
    assert board.get_num_surrounding_mines(2, 0) == 1
    assert board.get_num_surrounding_mines(2, 1) == 1
    assert board.get_num_surrounding_mines(2, 2) == 1
    # The mine itself has no surrounding mines
    assert board.get_num_surrounding_mines(1, 1) == 0


def test_get_num_surrounding_flags():
    board = Board.from_grid(grid=[[EMPTY_VALUE] * 3 for _ in range(3)])
    board.flag_square(0, 0)
    board.flag_square(1, 1)
    board.flag_square(2, 2)
    assert board.get_num_surrounding_flags(1, 1) == 2
    assert board.get_num_surrounding_flags(0, 0) == 1
    assert board.get_num_surrounding_flags(2, 2) == 1
    assert board.get_num_surrounding_flags(0, 1) == 2
    assert board.get_num_surrounding_flags(1, 0) == 2


def test_clone_is_independent():
    board = Board.from_grid(
        grid=[
            [1, M],
            [1, 1],
        ],
        revealed=[(0, 0)],
        flagged=[(1, 0)],
    )
    clone = board.clone()

    # Same layout and state
    assert clone.get_square_value(1, 0) == M
    assert clone.get_square_state(0, 0) == SquareState.REVEALED
    assert clone.get_square_state(1, 0) == SquareState.FLAGGED
    assert clone.num_mines == 1

    # Mutating the clone leaves the original untouched
    clone.reveal_square(1, 1)
    clone.unflag_square(1, 0)
    assert board.get_square_state(1, 1) == SquareState.UNREVEALED
    assert board.get_square_state(1, 0) == SquareState.FLAGGED


def test_out_of_bounds_square_raises():
    board = Board.from_grid(grid=[[EMPTY_VALUE]])
    with pytest.raises(IndexError):
        board.get_square_value(1, 0)
    with pytest.raises(IndexError):
        board.reveal_square(0, -1)
