from src.board import Board, SquareState
from typing import TYPE_CHECKING, Any, cast

import sympy

if TYPE_CHECKING:
    from src.game import MinesweeperGame


class GaussianMinesweeperSolver:
    def __init__(self, game: Any):
        self.game = game
        self.board: Board = game.board

    def solve_board(self):
        """
        Solve the Minesweeper game using Gaussian elimination.

        The solver repeatedly:
        1. Finds revealed numbered squares adjacent to unrevealed squares.
        2. Builds a system of linear equations representing the current
           Minesweeper frontier.
        3. Reduces the system using RREF.
        4. Uses bounds reasoning to identify forced mines and safe squares.
        5. Applies subset logic to find additional deductions.
        6. Applies those deductions.

        The solver stops when:
        - The game is won.
        - The game is lost.
        - No deterministic deductions can be made.
        """
        while not self.board.check_win() and not self.board.check_lose():
            progress_made = self.matrix_resolve()

            if not progress_made:
                break

    def matrix_resolve(self) -> bool:
        """
        Construct and solve the current Minesweeper frontier using
        Gaussian elimination.

        Returns:
            True if at least one mine or safe square was identified.
            False otherwise.
        """

        numbered_squares = self.get_numbered_squares()

        if not numbered_squares:
            return False

        # Find every unrevealed square that appears in at least one
        # constraint.
        unknown_squares = set()

        for x, y in numbered_squares:
            for sx, sy in self.board.get_surrounding_squares(x, y):
                if self.board.get_square_state(sx, sy) == SquareState.UNREVEALED:
                    unknown_squares.add((sx, sy))

        if not unknown_squares:
            return False

        # Sorting gives us deterministic column ordering, which makes
        # debugging the matrix much easier.
        unknown_squares = sorted(unknown_squares)

        # Map each unknown square to its corresponding matrix column.
        square_to_col = {
            square: col
            for col, square in enumerate(unknown_squares)
        }

        # Each numbered square is a row.
        #
        # Each unknown square is a variable/column.
        #
        # The final column is the augmented/RHS column.
        matrix = sympy.Matrix.zeros(
            len(numbered_squares),
            len(unknown_squares) + 1,
        )

        # Construct the system of equations.
        for row, (x, y) in enumerate(numbered_squares):
            surrounding = self.board.get_surrounding_squares(x, y)

            for square in surrounding:
                if square in square_to_col:
                    col = square_to_col[square]
                    matrix[row, col] = 1

            # The clue tells us how many mines exist around the square.
            #
            # Subtract mines that we have already flagged because they
            # aren't variables in our equation.
            matrix[row, -1] = (
                self.board.get_square_value(x, y)
                - self.board.get_num_surrounding_flags(x, y)
            )

        # Reduce the augmented matrix to reduced row echelon form.
        reduced_matrix = matrix.rref()[0]

        mines, not_mines = self.find_forced_squares(
            reduced_matrix,
            unknown_squares,
        )

        # A square shouldn't simultaneously be classified as a mine and
        # safe. In the event of an inconsistent deduction, don't reveal it.
        not_mines -= mines

        # Apply subset logic to find additional deductions.
        subset_mines, subset_not_mines = self.apply_set_logic()

        mines |= subset_mines
        not_mines |= subset_not_mines

        # A square shouldn't simultaneously be classified as a mine and
        # safe. Remove conflicts.
        not_mines -= mines

        progress_made = False

        # Flag known mines.
        for x, y in mines:
            if self.board.get_square_state(x, y) == SquareState.UNREVEALED:
                self.game.toggle_flag_square(x, y)
                progress_made = True

        # Reveal known safe squares.
        for x, y in not_mines:
            if self.board.get_square_state(x, y) == SquareState.UNREVEALED:
                self.game.reveal_square(x, y)
                progress_made = True

        return progress_made

    def find_forced_squares(
        self,
        matrix: sympy.Matrix,
        unknown_squares: list[tuple[int, int]],
    ) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
        """
        Examine the reduced matrix and determine which variables are
        guaranteed to be mines or guaranteed to be safe.

        Uses two strategies:
        1. Bounds reasoning: rows where RHS equals min or max bound
        2. Deterministic substitution: rows where enough variables are
           already determined that the remaining variables are forced

        Returns:
            (mines, not_mines)
        """

        mines = set()
        not_mines = set()

        # Keep applying deductions until no new ones are found.
        # This handles chains of implications in the RREF matrix.
        changed = True
        while changed:
            changed = False
            
            for row in range(matrix.rows):
                min_bound = sympy.Integer(0)
                max_bound = sympy.Integer(0)

                # Track which columns have non-zero coefficients
                non_zero_cols = []

                # Ignore the augmented/RHS column.
                for col in range(matrix.cols - 1):
                    coefficient: sympy.Basic = cast(sympy.Basic, matrix[row, col])

                    if coefficient != 0:
                        non_zero_cols.append(col)
                        if coefficient > 0:  # type: ignore
                            max_bound += coefficient  # type: ignore
                        elif coefficient < 0:  # type: ignore
                            min_bound += coefficient  # type: ignore

                rhs: sympy.Basic = cast(sympy.Basic, matrix[row, -1])

                # Skip rows with no variables.
                if not non_zero_cols:
                    continue

                # Strategy 1: Bounds reasoning
                # The equation reaches its minimum possible value.
                if rhs == min_bound:
                    for col in non_zero_cols:
                        coefficient = cast(sympy.Basic, matrix[row, col])
                        square = unknown_squares[col]

                        if coefficient < 0 and square not in mines:  # type: ignore
                            mines.add(square)
                            changed = True
                        elif coefficient > 0 and square not in not_mines:  # type: ignore
                            not_mines.add(square)
                            changed = True

                # The equation reaches its maximum possible value.
                elif rhs == max_bound:
                    for col in non_zero_cols:
                        coefficient = cast(sympy.Basic, matrix[row, col])
                        square = unknown_squares[col]

                        if coefficient < 0 and square not in not_mines:  # type: ignore
                            not_mines.add(square)
                            changed = True
                        elif coefficient > 0 and square not in mines:  # type: ignore
                            mines.add(square)
                            changed = True

                # Strategy 2: Deterministic substitution
                # If all but one variable in a row are determined, determine the last one.
                undetermined = []
                determined_mines = 0
                determined_safe = 0

                for col in non_zero_cols:
                    square = unknown_squares[col]
                    if square in mines:
                        coefficient = cast(sympy.Basic, matrix[row, col])
                        if coefficient > 0:  # type: ignore
                            determined_mines += 1
                        else:
                            determined_safe += 1
                    elif square in not_mines:
                        coefficient = cast(sympy.Basic, matrix[row, col])
                        if coefficient > 0:  # type: ignore
                            determined_safe += 1
                        else:
                            determined_mines += 1
                    else:
                        undetermined.append(col)

                # If exactly one variable is undetermined, we can solve for it.
                if len(undetermined) == 1:
                    col = undetermined[0]
                    coefficient = cast(sympy.Basic, matrix[row, col])
                    square = unknown_squares[col]

                    # Calculate what this variable must be.
                    remaining_mines_needed = int(rhs) - determined_mines  # type: ignore
                    remaining_capacity = int(coefficient)  # type: ignore

                    if remaining_mines_needed == remaining_capacity:
                        # This variable must be a mine.
                        if square not in mines:
                            mines.add(square)
                            changed = True
                    elif remaining_mines_needed == 0:
                        # This variable must be safe.
                        if square not in not_mines:
                            not_mines.add(square)
                            changed = True

        return mines, not_mines

    def get_numbered_squares(self) -> list[tuple[int, int]]:
        """
        Find all revealed numbered squares that have at least one
        unrevealed square adjacent to them.

        These become the rows of the matrix.
        """

        numbered_squares = []

        for y in range(self.board.num_rows):
            for x in range(self.board.num_cols):

                if self.board.get_square_state(x, y) != SquareState.REVEALED:
                    continue

                value = self.board.get_square_value(x, y)

                # Only numbered squares generate equations.
                if value <= 0:
                    continue

                surrounding = self.board.get_surrounding_squares(x, y)

                for sx, sy in surrounding:
                    if (
                        self.board.get_square_state(sx, sy)
                        == SquareState.UNREVEALED
                    ):
                        numbered_squares.append((x, y))
                        break

        return numbered_squares

    def apply_set_logic(self) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
        """
        Compare sets of unrevealed squares surrounding revealed cells.

        If Set A is a subset of Set B, then:

            B - A

        contains:

            mines(B) - mines(A)

        mines.

        Therefore:
            - If the difference requires 0 mines, every square in the
              difference is safe.
            - If the difference requires exactly len(difference) mines,
              every square in the difference is a mine.

        Returns:
            (mines, not_mines) - sets of squares to flag or reveal
        """
        mines = set()
        not_mines = set()

        revealed_numbers = []

        # Build the constraints generated by each revealed numbered square.
        for y in range(self.board.num_rows):
            for x in range(self.board.num_cols):
                if self.board.get_square_state(x, y) != SquareState.REVEALED:
                    continue

                value = self.board.get_square_value(x, y)

                # Only numbered squares generate constraints.
                if value <= 0:
                    continue

                surrounding = self.board.get_surrounding_squares(x, y)

                unrevealed = {
                    square
                    for square in surrounding
                    if self.board.get_square_state(
                        square[0],
                        square[1]
                    ) == SquareState.UNREVEALED
                }

                flags = {
                    square
                    for square in surrounding
                    if self.board.get_square_state(
                        square[0],
                        square[1]
                    ) == SquareState.FLAGGED
                }

                mines_needed = value - len(flags)

                # An inconsistent constraint should never occur if all
                # flags are correct. Ignore it rather than making unsafe
                # deductions.
                if mines_needed < 0 or mines_needed > len(unrevealed):
                    continue

                revealed_numbers.append({
                    "pos": (x, y),
                    "set": unrevealed,
                    "needed": mines_needed,
                })

        # Compare every pair of constraints.
        for i in range(len(revealed_numbers)):
            for j in range(len(revealed_numbers)):
                if i == j:
                    continue

                a = revealed_numbers[i]
                b = revealed_numbers[j]

                set_a = a["set"]
                set_b = b["set"]

                # We can only subtract A from B if A is a subset of B.
                if not set_a.issubset(set_b):
                    continue

                diff_set = set_b - set_a
                diff_mines = b["needed"] - a["needed"]

                if not diff_set:
                    continue

                # Difference contains no mines.
                if diff_mines == 0:
                    not_mines |= diff_set

                # Every square in the difference is a mine.
                elif diff_mines == len(diff_set):
                    mines |= diff_set

        return mines, not_mines