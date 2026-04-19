"""
Constraint-satisfaction solver for LinkedIn Queens.

Rules:
  1. An N×N board has N distinct color regions.
  2. Place exactly one queen per color region.
  3. Each row must contain exactly one queen.
  4. Each column must contain exactly one queen.
  5. No two queens may be adjacent — including diagonally (touching corners).

This is a variant of the classic N-Queens problem with the additional
color-region constraint replacing the standard diagonal attack constraint.

Algorithm:
  - Pre-compute which cells belong to each color region.
  - Backtrack row-by-row, maintaining:
      - ``col_used``:    set of columns already occupied.
      - ``color_used``:  set of color regions already occupied.
      - ``queen_pos``:   list of (row, col) placed so far.
  - At each row, try columns in ascending order; skip if the column is taken,
    the color region is taken, or the candidate is adjacent to any existing queen.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from linkedin_games.queens.extractor import QueensState

logger = logging.getLogger(__name__)


@dataclass
class QueensSolution:
    """Solution to a Queens puzzle — one queen position per row.

    Attributes:
        positions: A list of ``(row, col)`` tuples, one per queen,
            sorted by row.
        grid_size: The board side length.
    """

    positions: list[tuple[int, int]]
    grid_size: int


def solve(state: QueensState) -> QueensSolution | None:
    """Solve the Queens puzzle.

    Uses backtracking row-by-row with constraint propagation.

    Args:
        state: The extracted Queens puzzle state.

    Returns:
        A ``QueensSolution`` or ``None`` if unsolvable.
    """
    n = state.grid_size
    colors = state.colors
    prefilled = state.prefilled

    # Map color index → set of cells in that region
    regions: list[set[tuple[int, int]]] = [set() for _ in range(n)]
    for r in range(n):
        for c in range(n):
            regions[colors[r][c]].add((r, c))

    # Check we actually have N distinct colors
    n_colors = len(regions)
    if n_colors != n:
        logger.warning(
            "Expected %d color regions, found %d — attempting solve anyway.", n, n_colors
        )

    # Handle pre-filled queens: they fix row, col, and color
    positions: list[tuple[int, int] | None] = [None] * n
    col_used: set[int] = set()
    color_used: set[int] = set()

    for r in range(n):
        for c in range(n):
            if prefilled[r][c]:
                color = colors[r][c]
                positions[r] = (r, c)
                col_used.add(c)
                color_used.add(color)
                logger.debug("Pre-filled queen at (%d,%d) color=%d", r + 1, c + 1, color)

    # Backtrack
    result = _backtrack(0, positions, col_used, color_used, colors, n, prefilled)
    if not result:
        return None

    final_positions = [pos for pos in positions if pos is not None]
    final_positions.sort(key=lambda p: p[0])
    return QueensSolution(positions=final_positions, grid_size=n)


def _backtrack(
    row: int,
    positions: list[tuple[int, int] | None],
    col_used: set[int],
    color_used: set[int],
    colors: list[list[int]],
    n: int,
    prefilled: list[list[bool]],
) -> bool:
    """Recursive backtracking over rows.

    Args:
        row: Current row being filled.
        positions: Partial solution list (None = not yet placed).
        col_used: Columns already occupied by a queen.
        color_used: Color-region indices already occupied.
        colors: 2-D color map.
        n: Grid size.
        prefilled: 2-D boolean map of pre-placed queens.

    Returns:
        ``True`` if a full solution was found and written into *positions*.
    """
    if row == n:
        return all(p is not None for p in positions)

    # If this row is pre-filled, skip straight to the next row
    if positions[row] is not None:
        return _backtrack(row + 1, positions, col_used, color_used, colors, n, prefilled)

    for col in range(n):
        color = colors[row][col]

        # Column conflict
        if col in col_used:
            continue

        # Color-region conflict
        if color in color_used:
            continue

        # Adjacency conflict: no queen may be adjacent (including diagonal)
        if _adjacent_conflict(row, col, positions):
            continue

        # Place queen
        positions[row] = (row, col)
        col_used.add(col)
        color_used.add(color)

        if _backtrack(row + 1, positions, col_used, color_used, colors, n, prefilled):
            return True

        # Undo
        positions[row] = None
        col_used.discard(col)
        color_used.discard(color)

    return False


def _adjacent_conflict(row: int, col: int, positions: list[tuple[int, int] | None]) -> bool:
    """Return ``True`` if placing a queen at ``(row, col)`` is adjacent to any
    already-placed queen (8-directional neighbourhood, i.e. touching corners counts).

    Args:
        row: Candidate row.
        col: Candidate column.
        positions: Current partial solution.

    Returns:
        ``True`` if the placement would create an adjacency conflict.
    """
    for pos in positions:
        if pos is None:
            continue
        pr, pc = pos
        if abs(pr - row) <= 1 and abs(pc - col) <= 1:
            return True
    return False


# ---------------------------------------------------------------------------
# Validation & formatting
# ---------------------------------------------------------------------------


def validate_solution(solution: QueensSolution, colors: list[list[int]]) -> bool:
    """Validate that a Queens solution satisfies all constraints.

    Checks:
    - Exactly N queens.
    - All rows distinct.
    - All columns distinct.
    - All color regions distinct.
    - No two queens adjacent (including diagonal).

    Args:
        solution: The candidate solution.
        colors: 2-D color map from the extracted state.

    Returns:
        ``True`` if all constraints are satisfied.
    """
    n = solution.grid_size
    if len(solution.positions) != n:
        return False

    rows = [r for r, c in solution.positions]
    cols = [c for r, c in solution.positions]
    color_ids = [colors[r][c] for r, c in solution.positions]

    if len(set(rows)) != n:
        return False
    if len(set(cols)) != n:
        return False
    if len(set(color_ids)) != n:
        return False

    # Adjacency check
    for i, (r1, c1) in enumerate(solution.positions):
        for j, (r2, c2) in enumerate(solution.positions):
            if i >= j:
                continue
            if abs(r1 - r2) <= 1 and abs(c1 - c2) <= 1:
                return False

    return True


def format_solution(solution: QueensSolution, colors: list[list[int]]) -> str:
    """Format the solved Queens board as a grid string.

    Args:
        solution: The solved Queens positions.
        colors: 2-D color map used to label each cell.

    Returns:
        A human-readable multi-line string. Queens are shown as ``Q``,
        empty cells show their color region number.
    """
    n = solution.grid_size
    queen_set = set(solution.positions)
    lines: list[str] = []
    for r in range(n):
        row_str = " ".join("Q" if (r, c) in queen_set else str(colors[r][c]) for c in range(n))
        lines.append(row_str)
    return "\n".join(lines)
