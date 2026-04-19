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
from typing import Optional

GRID_SIZE = 6
BOX_ROWS = 2  # height of each sub-grid
BOX_COLS = 3  # width  of each sub-grid
VALID_NUMS = set(range(1, GRID_SIZE + 1))


def solve(grid: list[list[int]]) -> Optional[list[list[int]]]:
    """
    Solve a 6×6 Sudoku grid in-place using backtracking.

    *grid* should be a 6×6 list-of-lists where 0 means empty.
    Returns the solved grid, or ``None`` if unsolvable.
    """
    board = copy.deepcopy(grid)
    if _backtrack(board):
        return board
    return None


# ---------------------------------------------------------------------------
# Core algorithm
# ---------------------------------------------------------------------------

def _backtrack(board: list[list[int]]) -> bool:
    """Recursive backtracking with MRV (minimum remaining values) heuristic."""
    cell = _find_best_empty(board)
    if cell is None:
        return True  # no empty cells left → solved

    row, col = cell
    for num in _candidates(board, row, col):
        board[row][col] = num
        if _backtrack(board):
            return True
        board[row][col] = 0

    return False


def _find_best_empty(board: list[list[int]]) -> Optional[tuple[int, int]]:
    """
    Return the empty cell (row, col) with the fewest legal candidates
    (MRV heuristic).  Returns ``None`` when the board is complete.
    """
    best: Optional[tuple[int, int]] = None
    best_count = GRID_SIZE + 1

    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c] == 0:
                count = len(_candidates(board, r, c))
                if count < best_count:
                    best = (r, c)
                    best_count = count
                    if count == 1:
                        return best  # can't do better than 1

    return best


def _candidates(board: list[list[int]], row: int, col: int) -> list[int]:
    """Return sorted list of valid numbers for cell (row, col)."""
    used: set[int] = set()

    # Row constraint
    used.update(board[row])

    # Column constraint
    for r in range(GRID_SIZE):
        used.add(board[r][col])

    # Sub-grid constraint
    box_r = (row // BOX_ROWS) * BOX_ROWS
    box_c = (col // BOX_COLS) * BOX_COLS
    for r in range(box_r, box_r + BOX_ROWS):
        for c in range(box_c, box_c + BOX_COLS):
            used.add(board[r][c])

    return sorted(VALID_NUMS - used)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def print_board(board: list[list[int]]) -> None:
    """Pretty-print a 6×6 board to stdout."""
    for i, row in enumerate(board):
        if i > 0 and i % BOX_ROWS == 0:
            print("───────┼───────")
        parts = []
        for j, val in enumerate(row):
            if j > 0 and j % BOX_COLS == 0:
                parts.append("│")
            parts.append(str(val) if val else "·")
        print(" ".join(parts))


def validate_solution(board: list[list[int]]) -> bool:
    """Return True if *board* is a valid, complete 6×6 Sudoku solution."""
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
                board[r][c]
                for r in range(br, br + BOX_ROWS)
                for c in range(bc, bc + BOX_COLS)
            }
            if box_vals != VALID_NUMS:
                return False

    return True
