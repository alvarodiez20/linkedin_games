"""
Constraint-propagation + backtracking solver for 6×6 Tango (binary puzzle).

Rules:
  1. Each cell is Sun (1) or Moon (2).
  2. No three consecutive identical symbols in any row or column.
  3. Each row and column has exactly 3 suns and 3 moons.
  4. Edge constraints:
     - ``equal``:    two cells must have the same symbol.
     - ``opposite``: two cells must have different symbols.
"""

from __future__ import annotations

import copy
import logging

logger = logging.getLogger(__name__)

GRID_SIZE = 6
HALF = GRID_SIZE // 2
EMPTY = 0
SUN = 1
MOON = 2
VALUES = (SUN, MOON)


def solve(
    grid: list[list[int]],
    constraints: list[tuple[tuple[int, int], tuple[int, int], str]],
) -> list[list[int]] | None:
    """Solve a 6×6 Tango puzzle.

    Runs constraint propagation on the initial board to derive forced
    assignments, then falls back to backtracking with MRV for any remaining
    empty cells.

    Args:
        grid: 6×6 grid where ``0`` = empty, ``1`` = sun, ``2`` = moon.
        constraints: List of ``((r1, c1), (r2, c2), "equal"|"opposite")``
            edge constraints.

    Returns:
        The solved 6×6 grid, or ``None`` if the puzzle has no solution.
    """
    board = copy.deepcopy(grid)
    logger.debug("Starting Tango solver")

    if not _propagate(board, constraints):
        logger.debug("Contradiction found during initial propagation")
        return None

    if _backtrack(board, constraints):
        logger.debug("Solution found")
        return board

    logger.debug("No solution found")
    return None


def _backtrack(
    board: list[list[int]],
    constraints: list[tuple[tuple[int, int], tuple[int, int], str]],
) -> bool:
    """Recursive backtracking core with MRV heuristic.

    Picks the empty cell with the fewest valid options, tries each in turn,
    and recursively continues.  Backtracks if no option leads to a solution.

    Args:
        board: The current (partially filled) 6×6 grid, mutated in-place.
        constraints: Edge constraints for the puzzle.

    Returns:
        ``True`` if a solution was written into *board*; ``False`` otherwise.
    """
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
) -> tuple[int, int] | None:
    """Return the empty cell with the fewest valid options (MRV heuristic).

    Immediately returns on the first cell with 0 candidates (dead end) or
    1 candidate (forced assignment) to avoid unnecessary scanning.

    Args:
        board: The current 6×6 grid.
        constraints: Edge constraints (used to compute candidates).

    Returns:
        ``(row, col)`` of the best empty cell, or ``None`` when the board is
        fully filled.
    """
    best: tuple[int, int] | None = None
    best_count = 3

    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c] == EMPTY:
                count = len(_ordered_candidates(board, r, c))
                if count < best_count:
                    best = (r, c)
                    best_count = count
                    if count == 0:
                        return best  # dead end
                    if count == 1:
                        return best  # forced

    return best


def _ordered_candidates(board: list[list[int]], r: int, c: int) -> list[int]:
    """Return the list of values that are locally valid for cell ``(r, c)``.

    Tests Sun and Moon independently by temporarily placing each and checking
    local constraints.

    Args:
        board: The current 6×6 grid.
        r: Row index of the target cell (0-based).
        c: Column index of the target cell (0-based).

    Returns:
        List of valid values (subset of ``[SUN, MOON]``).
    """
    candidates = []
    for val in VALUES:
        board[r][c] = val
        if _is_locally_valid(board, r, c):
            candidates.append(val)
        board[r][c] = EMPTY
    return candidates


def _is_consistent(
    board: list[list[int]],
    r: int,
    c: int,
    constraints: list[tuple[tuple[int, int], tuple[int, int], str]],
) -> bool:
    """Check all constraints involving cell ``(r, c)`` after a placement.

    Combines local validity (balance, no-three-in-a-row) with edge constraint
    checking for any fully-assigned constraint pair involving this cell.

    Args:
        board: The current 6×6 grid (with the new value already placed).
        r: Row index of the newly placed cell.
        c: Column index of the newly placed cell.
        constraints: Full list of edge constraints.

    Returns:
        ``True`` if no constraint is violated; ``False`` otherwise.
    """
    if not _is_locally_valid(board, r, c):
        return False

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
    """Check row/column constraints for cell ``(r, c)``.

    Verifies:
    - No three consecutive identical symbols horizontally or vertically.
    - The row symbol count does not exceed ``HALF`` (3).
    - The column symbol count does not exceed ``HALF`` (3).

    Args:
        board: The current 6×6 grid.
        r: Row index of the cell to check.
        c: Column index of the cell to check.

    Returns:
        ``True`` if placement at ``(r, c)`` satisfies all local rules.
    """
    val = board[r][c]
    if val == EMPTY:
        return True

    # No three in a row — horizontal
    if c >= 2 and board[r][c - 1] == val and board[r][c - 2] == val:
        return False
    if c >= 1 and c < GRID_SIZE - 1 and board[r][c - 1] == val and board[r][c + 1] == val:
        return False
    if c < GRID_SIZE - 2 and board[r][c + 1] == val and board[r][c + 2] == val:
        return False

    # No three in a row — vertical
    if r >= 2 and board[r - 1][c] == val and board[r - 2][c] == val:
        return False
    if r >= 1 and r < GRID_SIZE - 1 and board[r - 1][c] == val and board[r + 1][c] == val:
        return False
    if r < GRID_SIZE - 2 and board[r + 1][c] == val and board[r + 2][c] == val:
        return False

    # Balance
    row_count = sum(1 for v in board[r] if v == val)
    if row_count > HALF:
        return False

    col_count = sum(1 for rr in range(GRID_SIZE) if board[rr][c] == val)
    if col_count > HALF:
        return False

    return True


def _propagate(
    board: list[list[int]],
    constraints: list[tuple[tuple[int, int], tuple[int, int], str]],
) -> bool:
    """Apply constraint propagation to derive forced cell assignments.

    Repeatedly scans all edge constraints.  When one endpoint of an
    ``equal`` or ``opposite`` constraint is filled and the other is empty,
    the empty cell is immediately forced.  Terminates when no further
    deductions can be made (fixed-point) or a contradiction is found.

    Args:
        board: The 6×6 grid, mutated in-place as deductions are applied.
        constraints: Edge constraints for the puzzle.

    Returns:
        ``True`` if propagation completed without contradiction; ``False`` if
        a contradiction was detected (two cells forced to conflicting values).
    """
    changed = True
    while changed:
        changed = False
        for (r1, c1), (r2, c2), ctype in constraints:
            v1 = board[r1][c1]
            v2 = board[r2][c2]

            if v1 != EMPTY and v2 == EMPTY:
                board[r2][c2] = v1 if ctype == "equal" else (SUN if v1 == MOON else MOON)
                changed = True
            elif v2 != EMPTY and v1 == EMPTY:
                board[r1][c1] = v2 if ctype == "equal" else (SUN if v2 == MOON else MOON)
                changed = True
            elif v1 != EMPTY and v2 != EMPTY:
                if ctype == "equal" and v1 != v2:
                    return False
                if ctype == "opposite" and v1 == v2:
                    return False

    return True


SYM = {EMPTY: "·", SUN: "☀", MOON: "☽"}


def format_board(board: list[list[int]]) -> str:
    """Format a 6×6 Tango board as a multi-line string.

    Args:
        board: The 6×6 grid to format.

    Returns:
        A human-readable string using ``☀`` / ``☽`` / ``·`` symbols.
    """
    return "\n".join(" ".join(SYM.get(v, "?") for v in row) for row in board)


def print_board(board: list[list[int]]) -> None:
    """Log a 6×6 Tango board at INFO level.

    Args:
        board: The 6×6 grid to display.
    """
    logger.info("Board:\n%s", format_board(board))


def validate_solution(
    board: list[list[int]],
    constraints: list[tuple[tuple[int, int], tuple[int, int], str]],
) -> bool:
    """Return ``True`` if *board* satisfies all Tango rules.

    Checks:
    - Every row and column has exactly ``HALF`` suns and ``HALF`` moons.
    - No three consecutive identical symbols horizontally or vertically.
    - All edge constraints (``equal`` / ``opposite``) are satisfied.

    Args:
        board: The 6×6 completed grid to validate.
        constraints: Edge constraints that must hold.

    Returns:
        ``True`` if the solution is valid; ``False`` otherwise.
    """
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

    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE - 2):
            if board[r][c] == board[r][c + 1] == board[r][c + 2] != EMPTY:
                return False
    for c in range(GRID_SIZE):
        for r in range(GRID_SIZE - 2):
            if board[r][c] == board[r + 1][c] == board[r + 2][c] != EMPTY:
                return False

    for (r1, c1), (r2, c2), ctype in constraints:
        v1, v2 = board[r1][c1], board[r2][c2]
        if ctype == "equal" and v1 != v2:
            return False
        if ctype == "opposite" and v1 == v2:
            return False

    return True
