"""
Backtracking solver for 6×6 Mini Sudoku.

Constraints:
  • Numbers 1–6.
  • No duplicate in any row.
  • No duplicate in any column.
  • No duplicate in any of the six 2×3 sub-grids
    (2 rows tall × 3 columns wide).

Sub-grid layout::

    ┌───────┬───────┐
    │ 0,0   │ 0,3   │
    │   2×3 │   2×3 │
    ├───────┼───────┤
    │ 2,0   │ 2,3   │
    │   2×3 │   2×3 │
    ├───────┼───────┤
    │ 4,0   │ 4,3   │
    │   2×3 │   2×3 │
    └───────┴───────┘
"""

from __future__ import annotations

import copy
import logging

logger = logging.getLogger(__name__)

GRID_SIZE = 6
BOX_ROWS = 2
BOX_COLS = 3
VALID_NUMS = set(range(1, GRID_SIZE + 1))


def solve(grid: list[list[int]]) -> list[list[int]] | None:
    """Solve a 6×6 Sudoku grid using backtracking with MRV.

    The input grid is never mutated — a deep copy is made internally.

    Args:
        grid: A ``6×6`` list-of-lists where ``0`` means empty and ``1``–``6``
            are given clue values.

    Returns:
        The solved ``6×6`` grid, or ``None`` if the puzzle has no solution.

    Example:
        >>> puzzle = [[0,0,3,0,0,0], ...]
        >>> solved = solve(puzzle)
        >>> solved is not None
        True
    """
    board = copy.deepcopy(grid)
    logger.debug("Starting backtracking solver")
    if _backtrack(board):
        logger.debug("Solution found")
        return board
    logger.debug("No solution found")
    return None


def _backtrack(board: list[list[int]]) -> bool:
    """Recursive backtracking core with MRV heuristic.

    Picks the empty cell with the fewest legal candidates (MRV), tries each
    candidate in order, recurses, and backtracks on failure.

    Args:
        board: The current (partially filled) 6×6 grid, mutated in-place.

    Returns:
        ``True`` if a solution was found and written into *board*; ``False``
        if this branch has no solution.
    """
    cell = _find_best_empty(board)
    if cell is None:
        return True  # no empty cells → solved

    row, col = cell
    for num in _candidates(board, row, col):
        board[row][col] = num
        if _backtrack(board):
            return True
        board[row][col] = 0

    return False


def _find_best_empty(board: list[list[int]]) -> tuple[int, int] | None:
    """Return the empty cell with the fewest legal candidates (MRV heuristic).

    Scanning every empty cell and computing its candidate count is O(n³) per
    call, but n=6 makes this negligible.  Early exit on count==1 avoids
    unnecessary work when a forced assignment is found.

    Args:
        board: The current 6×6 grid (``0`` = empty).

    Returns:
        ``(row, col)`` of the best empty cell, or ``None`` when the board is
        complete.
    """
    best: tuple[int, int] | None = None
    best_count = GRID_SIZE + 1

    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c] == 0:
                count = len(_candidates(board, r, c))
                if count < best_count:
                    best = (r, c)
                    best_count = count
                    if count == 1:
                        return best  # forced assignment — can't improve

    return best


def _candidates(board: list[list[int]], row: int, col: int) -> list[int]:
    """Return the sorted list of valid numbers for cell ``(row, col)``.

    Computes the union of values already used in the same row, column, and
    2×3 sub-grid, then returns ``{1..6}`` minus that set.

    Args:
        board: The current 6×6 grid.
        row: Row index of the target cell (0-based).
        col: Column index of the target cell (0-based).

    Returns:
        Sorted list of integers that can legally be placed at ``(row, col)``.
    """
    used: set[int] = set()

    used.update(board[row])

    for r in range(GRID_SIZE):
        used.add(board[r][col])

    box_r = (row // BOX_ROWS) * BOX_ROWS
    box_c = (col // BOX_COLS) * BOX_COLS
    for r in range(box_r, box_r + BOX_ROWS):
        for c in range(box_c, box_c + BOX_COLS):
            used.add(board[r][c])

    return sorted(VALID_NUMS - used)


def format_board(board: list[list[int]]) -> str:
    """Format a 6×6 board as a multi-line string with sub-grid dividers.

    Args:
        board: The 6×6 grid to format.

    Returns:
        A human-readable string representation of *board*.
    """
    lines: list[str] = []
    for i, row in enumerate(board):
        if i > 0 and i % BOX_ROWS == 0:
            lines.append("───────┼───────")
        parts = []
        for j, val in enumerate(row):
            if j > 0 and j % BOX_COLS == 0:
                parts.append("│")
            parts.append(str(val) if val else "·")
        lines.append(" ".join(parts))
    return "\n".join(lines)


def print_board(board: list[list[int]]) -> None:
    """Log a 6×6 board at INFO level using structured logging.

    Args:
        board: The 6×6 grid to display.
    """
    logger.info("Board:\n%s", format_board(board))


def validate_solution(board: list[list[int]]) -> bool:
    """Return ``True`` if *board* is a valid, complete 6×6 Sudoku solution.

    Checks that every row, every column, and every 2×3 sub-grid contains
    exactly the values ``{1, 2, 3, 4, 5, 6}``.

    Args:
        board: The 6×6 grid to validate.

    Returns:
        ``True`` if the solution is valid; ``False`` otherwise.
    """
    for r in range(GRID_SIZE):
        if set(board[r]) != VALID_NUMS:
            return False

    for c in range(GRID_SIZE):
        col_vals = {board[r][c] for r in range(GRID_SIZE)}
        if col_vals != VALID_NUMS:
            return False

    for br in range(0, GRID_SIZE, BOX_ROWS):
        for bc in range(0, GRID_SIZE, BOX_COLS):
            box_vals = {
                board[r][c] for r in range(br, br + BOX_ROWS) for c in range(bc, bc + BOX_COLS)
            }
            if box_vals != VALID_NUMS:
                return False

    return True
