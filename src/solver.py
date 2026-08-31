from src.board import Board, SquareState
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.game import MinesweeperGame

class MinesweeperSolver:
    def __init__(self, game: Any):
        self.game = game
        self.board = game.board

    def solve_board(self):
        """
        Solve the Minesweeper game using a simple algorithm.
        """
        while not self.board.check_win() and not self.board.check_lose():
            progress_made = False
            for y in range(self.board.num_rows):
                for x in range(self.board.num_cols):
                    if self.board.get_square_state(x, y) == SquareState.REVEALED:
                        if self.simple_resolve_surrounding(x, y):
                            progress_made = True
            
            if not progress_made:
                if self.apply_set_logic():
                    progress_made = True
                else:
                    break

        
    def simple_resolve_surrounding(self, x: int, y: int):
        """
        If a square's number equals the number of surrounding flagged squares, 
        then all other surrounding squares are safe to reveal.
        
        If a square's number equals the number of surrounding unrevealed squares, 
        then all surrounding unrevealed squares are mines and should be flagged.
        """
        progress_made = False
        surrounding_squares = self.board.get_surrounding_squares(x, y)
        states = {
            SquareState.REVEALED: [],
            SquareState.FLAGGED: [],
            SquareState.UNREVEALED: []
        }
        for square in surrounding_squares:
            state = self.board.get_square_state(square[0], square[1])
            if state == SquareState.REVEALED:
                states[SquareState.REVEALED].append(square)
            elif state == SquareState.FLAGGED:
                states[SquareState.FLAGGED].append(square)
            elif state == SquareState.UNREVEALED:
                states[SquareState.UNREVEALED].append(square)
                
        if len(states[SquareState.FLAGGED]) < self.board.get_square_value(x, y):
            unrevealed_count = len(states[SquareState.UNREVEALED])
            mines_needed = self.board.get_square_value(x, y) - len(states[SquareState.FLAGGED])
            if unrevealed_count == mines_needed:
                for square in states[SquareState.UNREVEALED]:
                    self.game.toggle_flag_square(square[0], square[1])
                    progress_made = True
        
        if len(states[SquareState.FLAGGED]) == self.board.get_square_value(x, y):
            for square in states[SquareState.UNREVEALED]:
                self.game.reveal_square(square[0], square[1])
                progress_made = True
    
        return progress_made

    def apply_set_logic(self) -> bool:
        """
        Compares sets of unrevealed squares surrounding revealed cells.
        If Set A is a subset of Set B, the difference must contain (Value B - Value A) mines.
        """
        progress_made = False
        revealed_numbers = []
        for y in range(self.board.nuaddm_rows):
            for x in range(self.board.num_cols):
                if self.board.get_square_state(x, y) == SquareState.REVEALED:
                    val = self.board.get_square_value(x, y)
                    if val > 0:
                        surround = self.board.get_surrounding_squares(x, y)
                        # Use only unrevealed squares for the set
                        unrevealed = {s for s in surround if self.board.get_square_state(s[0], s[1]) == SquareState.UNREVEALED}
                        flags = {s for s in surround if self.board.get_square_state(s[0], s[1]) == SquareState.FLAGGED}
                        
                        # Only add if we still need mines from the unrevealed set
                        needed = val - len(flags)
                        if needed >= 0:
                            revealed_numbers.append({
                                'pos': (x, y),
                                'set': unrevealed,
                                'needed': needed
                            })

        for i in range(len(revealed_numbers)):
            for j in range(len(revealed_numbers)):
                if i == j: continue
                
                a = revealed_numbers[i]
                b = revealed_numbers[j]
                
                if a['set'].issubset(b['set']):
                    diff_set = b['set'] - a['set']
                    diff_mines = b['needed'] - a['needed']
                    
                    if diff_mines == 0 and len(diff_set) > 0:
                        for sq in diff_set:
                            self.game.reveal_square(sq[0], sq[1])
                        progress_made = True
                    elif diff_mines == len(diff_set) and len(diff_set) > 0:
                        for sq in diff_set:
                            self.game.toggle_flag_square(sq[0], sq[1])
                        progress_made = True
        
        return progress_made

