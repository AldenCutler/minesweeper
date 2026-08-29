import pytest
from ..board import Board, MINE_VALUE, EMPTY_VALUE

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
        
def test_generate_internal_board():
    board = Board(num_rows=16, num_cols=30)
    internal_board = board.generate_internal_board()
    assert len(internal_board) == 16
    assert len(internal_board[0]) == 30
    mine_count = sum(row.count(MINE_VALUE) for row in internal_board)
    assert mine_count == 99
    for y in range(16):
        for x in range(30):
            if internal_board[y][x] != MINE_VALUE:
                surrounding_mines = board.get_num_surrounding_mines(x, y, internal_board)
                assert internal_board[y][x] == surrounding_mines
                
def test_get_revealed_and_flagged_squares():
    board = Board(num_rows=16, num_cols=30)
    board.revealed = [(0, 0), (1, 1)]
    board.flagged = [(2, 2), (3, 3)]
    assert board.get_revealed_squares() == [(0, 0), (1, 1)]
    assert board.get_flagged_squares() == [(2, 2), (3, 3)]
    
def test_reveal_square():
    board = Board(num_rows=16, num_cols=30)
    x, y = 0, 0
    board.reveal_square(x, y)
    assert (x, y) in board.revealed
    # Revealing the same square again should not change the revealed list
    board.reveal_square(x, y)
    assert board.revealed.count((x, y)) == 1
    
def test_flag_square():
    board = Board(num_rows=16, num_cols=30)
    x, y = 0, 0
    board.flag_square(x, y)
    assert (x, y) in board.flagged
    # Flagging the same square again should not change the flagged list
    board.flag_square(x, y)
    assert board.flagged.count((x, y)) == 1
    
def test_unflag_square():
    board = Board(num_rows=16, num_cols=30)
    x, y = 0, 0
    board.flag_square(x, y)
    assert (x, y) in board.flagged
    board.unflag_square(x, y)
    assert (x, y) not in board.flagged
    
def test_check_win():
    board = Board(num_rows=16, num_cols=30)
    # Reveal all non-mine squares
    for y in range(16):
        for x in range(30):
            if board.get_square_value(x, y) != MINE_VALUE:
                board.reveal_square(x, y)
    assert board.check_win() == True
    # If any non-mine square is not revealed, check_win should return False
    board = Board(num_rows=16, num_cols=30)
    for y in range(16):
        for x in range(30):
            if board.get_square_value(x, y) != MINE_VALUE and (x, y) != (0, 0):
                board.reveal_square(x, y)
    assert board.check_win() == False
    
def test_check_lose():
    board = Board(num_rows=16, num_cols=30)
    # Reveal a mine square
    for y in range(16):
        for x in range(30):
            if board.get_square_value(x, y) == MINE_VALUE:
                board.reveal_square(x, y)
                break
        else:
            continue
        break
    assert board.check_lose() == True
    # If no mine square is revealed, check_lose should return False
    board = Board(num_rows=16, num_cols=30)
    for y in range(16):
        for x in range(30):
            if board.get_square_value(x, y) != MINE_VALUE:
                board.reveal_square(x, y)
    assert board.check_lose() == False
    
def test_get_num_surrounding_mines():
    board = Board(num_rows=16, num_cols=30)
    # Clear the board and set only one mine at (1, 1)
    board.board = [[EMPTY_VALUE for _ in range(30)] for _ in range(16)]
    board.board[1][1] = MINE_VALUE
    # Check surrounding squares for mines
    assert board.get_num_surrounding_mines(0, 0, board.board) == 1
    assert board.get_num_surrounding_mines(0, 1, board.board) == 1
    assert board.get_num_surrounding_mines(0, 2, board.board) == 1
    assert board.get_num_surrounding_mines(1, 0, board.board) == 1
    assert board.get_num_surrounding_mines(1, 2, board.board) == 1
    assert board.get_num_surrounding_mines(2, 0, board.board) == 1
    assert board.get_num_surrounding_mines(2, 1, board.board) == 1
    assert board.get_num_surrounding_mines(2, 2, board.board) == 1
    
def test_get_num_surrounding_flags():
    board = Board(num_rows=16, num_cols=30)
    # Flag squares at (0, 0), (1, 1), and (2, 2)
    board.flag_square(0, 0)
    board.flag_square(1, 1)
    board.flag_square(2, 2)
    # Check surrounding squares for flags
    assert board.get_num_surrounding_flags(1, 1) == 2
    assert board.get_num_surrounding_flags(0, 0) == 1
    assert board.get_num_surrounding_flags(2, 2) == 1
    assert board.get_num_surrounding_flags(0, 1) == 2
    assert board.get_num_surrounding_flags(1, 0) == 2