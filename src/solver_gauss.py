"""
Gaussian-elimination deduction for Minesweeper.

Builds a linear system over the frontier (each revealed numbered square
is an equation, each unrevealed neighbor a variable), reduces it to
RREF, and uses bounds reasoning plus deterministic substitution to find
squares that are forced to be mines or forced to be safe. Pure: returns
moves, never mutates the board.
"""
from typing import cast

import sympy

from src.board import Board, SquareState
from src.solver import Move, REVEAL, FLAG


class GaussianStrategy:
    """
    Deduce forced squares on the current frontier using linear algebra.

    The strategy repeatedly:
    1. Finds revealed numbered squares adjacent to unrevealed squares.
    2. Builds a system of linear equations representing the current
       Minesweeper frontier.
    3. Reduces the system using RREF.
    4. Uses bounds reasoning and substitution to identify forced mines
       and safe squares.
    """

    def deduce(self, board: Board) -> list[Move]:
        numbered_squares = self._numbered_squares(board)

        if not numbered_squares:
            return []

        # Find every unrevealed square that appears in at least one
        # constraint.
        unknown_squares = set()

        for x, y in numbered_squares:
            for sx, sy in board.get_surrounding_squares(x, y):
                if board.get_square_state(sx, sy) == SquareState.UNREVEALED:
                    unknown_squares.add((sx, sy))

        if not unknown_squares:
            return []

        # Sorting gives us deterministic column ordering, which makes
        # debugging the matrix much easier.
        ordered_unknowns = sorted(unknown_squares)

        # Map each unknown square to its corresponding matrix column.
        square_to_col = {
            square: col
            for col, square in enumerate(ordered_unknowns)
        }

        # Each numbered square is a row.
        #
        # Each unknown square is a variable/column.
        #
        # The final column is the augmented/RHS column.
        matrix = sympy.Matrix.zeros(
            len(numbered_squares),
            len(ordered_unknowns) + 1,
        )

        # Construct the system of equations.
        for row, (x, y) in enumerate(numbered_squares):
            surrounding = board.get_surrounding_squares(x, y)

            for square in surrounding:
                if square in square_to_col:
                    col = square_to_col[square]
                    matrix[row, col] = 1

            # The clue tells us how many mines exist around the square.
            #
            # Subtract mines that we have already flagged because they
            # aren't variables in our equation.
            matrix[row, -1] = (
                board.get_square_value(x, y)
                - board.get_num_surrounding_flags(x, y)
            )

        # Reduce the augmented matrix to reduced row echelon form.
        reduced_matrix = matrix.rref()[0]

        mines, not_mines = find_forced_squares(reduced_matrix, ordered_unknowns)

        # A square shouldn't simultaneously be classified as a mine and
        # safe. In the event of an inconsistent deduction, don't reveal it.
        not_mines -= mines

        moves: list[Move] = []
        for x, y in mines:
            if board.get_square_state(x, y) == SquareState.UNREVEALED:
                moves.append((x, y, FLAG))
        for x, y in not_mines:
            if board.get_square_state(x, y) == SquareState.UNREVEALED:
                moves.append((x, y, REVEAL))
        return moves

    def _numbered_squares(self, board: Board) -> list[tuple[int, int]]:
        """
        Find all revealed numbered squares that have at least one
        unrevealed square adjacent to them.

        These become the rows of the matrix.
        """
        numbered_squares = []

        for y in range(board.num_rows):
            for x in range(board.num_cols):
                if board.get_square_state(x, y) != SquareState.REVEALED:
                    continue

                value = board.get_square_value(x, y)

                # Only numbered squares generate equations.
                if value <= 0:
                    continue

                surrounding = board.get_surrounding_squares(x, y)

                for sx, sy in surrounding:
                    if (
                        board.get_square_state(sx, sy)
                        == SquareState.UNREVEALED
                    ):
                        numbered_squares.append((x, y))
                        break

        return numbered_squares


def find_forced_squares(
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
