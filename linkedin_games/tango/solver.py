"""
Constraint-propagation + backtracking solver for 6×6 Tango (binary puzzle).

Rules:
  1. Each cell is Sun (1) or Moon (2).
  2. No three consecutive identical symbols in any row or column.
  3. Each row and column has exactly 3 suns and 3 moons.
  4. Constraint edges:
     - ``equal``:    two cells must have the same symbol.
     - ``opposite``: two cells must have different symbols.
"""

from __future__ import annotations

import copy
from typing import Optional

GRID_SIZE = 6
HALF = GRID_SIZE // 2  # 3 suns and 3 moons per row/col
EMPTY = 0
SUN = 1
MOON = 2
VALUES = (SUN, MOON)


def solve(
    grid: list[list[int]],
    constraints: list[tuple[tuple[int, int], tuple[int, int], str]],
) -> Optional[list[list[int]]]:
    """
    Solve a 6×6 Tango puzzle.

    Parameters
    ----------
    grid : list[list[int]]
        6×6 grid (0=empty, 1=sun, 2=moon).
    constraints : list
        List of ``((r1,c1), (r2,c2), "equal"|"opposite")``.

    Returns ``None`` if unsolvable.
    """
    board = copy.deepcopy(grid)

    # Pre-propagate constraints for prefilled cells
    if not _propagate(board, constraints):
        return None

    if _backtrack(board, constraints):
        return board
    return None


# ---------------------------------------------------------------------------
# Core algorithm
# ---------------------------------------------------------------------------

def _backtrack(
    board: list[list[int]],
    constraints: list[tuple[tuple[int, int], tuple[int, int], str]],
) -> bool:
    cell = _find_best_empty(board, constraints)
    if cell is None:
        return True  # solved

    r, c = cell
    for val in _ordered_candidates(board, r, c):
        board[r][c] = val
        if _is_consistent(board, r, c, constraints):
            if _backtrack(board, constraints):
                return True
        board[r][c] = EMPTY

    return False


def _find_best_empty(
    board: list[list[int]],
    constraints: list[tuple[tuple[int, int], tuple[int, int], str]],
) -> Optional[tuple[int, int]]:
    """MRV heuristic: pick empty cell with fewest valid options."""
    best: Optional[tuple[int, int]] = None
    best_count = 3

    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c] == EMPTY:
                count = len(_ordered_candidates(board, r, c))
                if count < best_count:
                    best = (r, c)
                    best_count = count
                    if count == 0:
                        return best  # dead end — return immediately
                    if count == 1:
                        return best

    return best


def _ordered_candidates(board: list[list[int]], r: int, c: int) -> list[int]:
    """Return list of valid values for cell (r, c)."""
    candidates = []
    for val in VALUES:
        board[r][c] = val
        if _is_locally_valid(board, r, c):
            candidates.append(val)
        board[r][c] = EMPTY
    return candidates


# ---------------------------------------------------------------------------
# Constraint checking
# ---------------------------------------------------------------------------

def _is_consistent(
    board: list[list[int]],
    r: int,
    c: int,
    constraints: list[tuple[tuple[int, int], tuple[int, int], str]],
) -> bool:
    """Check all constraints involving cell (r, c)."""
    if not _is_locally_valid(board, r, c):
        return False

    # Check edge constraints involving this cell
    for (r1, c1), (r2, c2), ctype in constraints:
        if (r1, c1) == (r, c) or (r2, c2) == (r, c):
            v1 = board[r1][c1]
            v2 = board[r2][c2]
            if v1 == EMPTY or v2 == EMPTY:
                continue
            if ctype == "equal" and v1 != v2:
                return False
            if ctype == "opposite" and v1 == v2:
                return False

    return True


def _is_locally_valid(board: list[list[int]], r: int, c: int) -> bool:
    """
    Check row/column constraints for cell (r, c):
    - No three consecutive identical
    - Not too many of one symbol in row/col
    """
    val = board[r][c]
    if val == EMPTY:
        return True

    # --- No three in a row (horizontal) ---
    if c >= 2 and board[r][c - 1] == val and board[r][c - 2] == val:
        return False
    if c >= 1 and c < GRID_SIZE - 1 and board[r][c - 1] == val and board[r][c + 1] == val:
        return False
    if c < GRID_SIZE - 2 and board[r][c + 1] == val and board[r][c + 2] == val:
        return False

    # --- No three in a row (vertical) ---
    if r >= 2 and board[r - 1][c] == val and board[r - 2][c] == val:
        return False
    if r >= 1 and r < GRID_SIZE - 1 and board[r - 1][c] == val and board[r + 1][c] == val:
        return False
    if r < GRID_SIZE - 2 and board[r + 1][c] == val and board[r + 2][c] == val:
        return False

    # --- Balance: count symbols in row ---
    row_count = sum(1 for v in board[r] if v == val)
    if row_count > HALF:
        return False

    # --- Balance: count symbols in column ---
    col_count = sum(1 for rr in range(GRID_SIZE) if board[rr][c] == val)
    if col_count > HALF:
        return False

    return True


# ---------------------------------------------------------------------------
# Constraint propagation
# ---------------------------------------------------------------------------

def _propagate(
    board: list[list[int]],
    constraints: list[tuple[tuple[int, int], tuple[int, int], str]],
) -> bool:
    """
    Apply constraint propagation for known cells.
    Returns False if a contradiction is found.
    """
    changed = True
    while changed:
        changed = False
        for (r1, c1), (r2, c2), ctype in constraints:
            v1 = board[r1][c1]
            v2 = board[r2][c2]

            if v1 != EMPTY and v2 == EMPTY:
                if ctype == "equal":
                    board[r2][c2] = v1
                    changed = True
                elif ctype == "opposite":
                    board[r2][c2] = SUN if v1 == MOON else MOON
                    changed = True
            elif v2 != EMPTY and v1 == EMPTY:
                if ctype == "equal":
                    board[r1][c1] = v2
                    changed = True
                elif ctype == "opposite":
                    board[r1][c1] = SUN if v2 == MOON else MOON
                    changed = True
            elif v1 != EMPTY and v2 != EMPTY:
                if ctype == "equal" and v1 != v2:
                    return False
                if ctype == "opposite" and v1 == v2:
                    return False

    return True


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

SYM = {EMPTY: "·", SUN: "☀", MOON: "☽"}


def print_board(board: list[list[int]]) -> None:
    """Pretty-print a 6×6 Tango board."""
    for row in board:
        print(" ".join(SYM.get(v, "?") for v in row))


def validate_solution(
    board: list[list[int]],
    constraints: list[tuple[tuple[int, int], tuple[int, int], str]],
) -> bool:
    """Check that a completed board satisfies all Tango rules."""
    for r in range(GRID_SIZE):
        suns = sum(1 for v in board[r] if v == SUN)
        moons = sum(1 for v in board[r] if v == MOON)
        if suns != HALF or moons != HALF:
            return False

    for c in range(GRID_SIZE):
        suns = sum(1 for r in range(GRID_SIZE) if board[r][c] == SUN)
        moons = sum(1 for r in range(GRID_SIZE) if board[r][c] == MOON)
        if suns != HALF or moons != HALF:
            return False

    # No three consecutive
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE - 2):
            if board[r][c] == board[r][c + 1] == board[r][c + 2] != EMPTY:
                return False
    for c in range(GRID_SIZE):
        for r in range(GRID_SIZE - 2):
            if board[r][c] == board[r + 1][c] == board[r + 2][c] != EMPTY:
                return False

    # Constraints
    for (r1, c1), (r2, c2), ctype in constraints:
        v1, v2 = board[r1][c1], board[r2][c2]
        if ctype == "equal" and v1 != v2:
            return False
        if ctype == "opposite" and v1 == v2:
            return False

    return True
