"""
Constraint-satisfaction + backtracking solver for 6×6 Patches (Shikaku).

Rules:
  1. Fill the entire 6×6 grid with non-overlapping rectangles (patches).
  2. Each patch contains exactly one clue cell.
  3. Shape constraints restrict the rectangle geometry:
     - ``VERTICAL_RECT``:   height > width
     - ``HORIZONTAL_RECT``: width > height
     - ``SQUARE``:          width == height
     - ``ANY``:             any rectangle with the given cell count
  4. Clues with a number specify the exact cell count of the patch.
     Clues without a number have their size inferred by the solver.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from linkedin_games.patches.extractor import (
    Clue,
    PatchesState,
    ShapeConstraint,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Rectangle:
    """Axis-aligned rectangle from top-left ``(r1, c1)`` to bottom-right ``(r2, c2)`` inclusive.

    Attributes:
        r1: Top row index (0-based).
        c1: Left column index (0-based).
        r2: Bottom row index (0-based, inclusive).
        c2: Right column index (0-based, inclusive).
    """

    r1: int
    c1: int
    r2: int
    c2: int

    @property
    def width(self) -> int:
        """Number of columns spanned by this rectangle.

        Returns:
            ``c2 - c1 + 1``.
        """
        return self.c2 - self.c1 + 1

    @property
    def height(self) -> int:
        """Number of rows spanned by this rectangle.

        Returns:
            ``r2 - r1 + 1``.
        """
        return self.r2 - self.r1 + 1

    @property
    def area(self) -> int:
        """Total cell count of this rectangle.

        Returns:
            ``width * height``.
        """
        return self.width * self.height

    def cells(self) -> frozenset[tuple[int, int]]:
        """Return the set of all ``(row, col)`` pairs covered by this rectangle.

        Returns:
            A ``frozenset`` of ``(row, col)`` tuples.
        """
        return frozenset(
            (r, c) for r in range(self.r1, self.r2 + 1) for c in range(self.c1, self.c2 + 1)
        )

    def contains(self, row: int, col: int) -> bool:
        """Return ``True`` if cell ``(row, col)`` is inside this rectangle.

        Args:
            row: Row index to test (0-based).
            col: Column index to test (0-based).

        Returns:
            ``True`` if the cell is within the rectangle's bounds.
        """
        return self.r1 <= row <= self.r2 and self.c1 <= col <= self.c2


def solve(state: PatchesState) -> list[Rectangle] | None:
    """Solve a Patches puzzle.

    Pre-computes all valid rectangle candidates for each clue, places any
    pre-drawn regions first, then runs backtracking with MRV and forward-
    checking to find a complete non-overlapping tiling of the 6×6 grid.

    Args:
        state: The extracted puzzle state (clues + pre-drawn regions).

    Returns:
        A list of ``Rectangle`` objects — one per clue, in the same order as
        ``state.clues`` — or ``None`` if the puzzle has no solution.
    """
    n_clues = len(state.clues)
    grid_size = state.grid_size
    candidates: list[list[Rectangle]] = [_candidate_rects(clue, grid_size) for clue in state.clues]
    occupied: set[tuple[int, int]] = set()
    solution: list[Rectangle | None] = [None] * n_clues

    for region_cells, clue_idx in state.predrawn:
        matched = next(
            (rect for rect in candidates[clue_idx] if rect.cells() == region_cells),
            None,
        )
        if matched:
            solution[clue_idx] = matched
            occupied.update(region_cells)
        else:
            rows = [r for r, c in region_cells]
            cols = [c for r, c in region_cells]
            rect = Rectangle(min(rows), min(cols), max(rows), max(cols))
            solution[clue_idx] = rect
            occupied.update(region_cells)

    unsolved = [i for i in range(n_clues) if solution[i] is None]
    for i in unsolved:
        candidates[i] = [r for r in candidates[i] if not r.cells() & occupied]

    logger.debug(
        "Starting backtrack: %d clues to solve, %d cells pre-occupied",
        len(unsolved),
        len(occupied),
    )

    if _backtrack(unsolved, 0, candidates, occupied, solution, grid_size * grid_size):
        return solution  # type: ignore[return-value]

    return None


def _backtrack(
    unsolved: list[int],
    pos: int,
    candidates: list[list[Rectangle]],
    occupied: set[tuple[int, int]],
    solution: list[Rectangle | None],
    total_cells: int,
) -> bool:
    """Recursive backtracking core with MRV and forward-checking.

    At each step, selects the unsolved clue with the fewest remaining
    candidate rectangles (MRV), tries each one, prunes remaining candidates
    with forward-checking, and recurses.  Backtracks on failure.

    Args:
        unsolved: List of unsolved clue indices in the current search order.
        pos: Current position in *unsolved* — indices before *pos* are solved.
        candidates: Per-clue list of still-viable rectangle options.
        occupied: Set of ``(row, col)`` cells already covered.
        solution: Partial solution array, indexed by clue index.

    Returns:
        ``True`` if a complete valid tiling was found and written into
        *solution*; ``False`` otherwise.
    """
    if pos == len(unsolved):
        return len(occupied) == total_cells

    # MRV: swap the clue with the fewest candidates to the front
    best_pos = pos
    best_count = len(candidates[unsolved[pos]])
    for p in range(pos + 1, len(unsolved)):
        c = len(candidates[unsolved[p]])
        if c < best_count:
            best_count = c
            best_pos = p
    unsolved[pos], unsolved[best_pos] = unsolved[best_pos], unsolved[pos]

    clue_idx = unsolved[pos]

    for rect in candidates[clue_idx]:
        cells = rect.cells()
        if cells & occupied:
            continue

        solution[clue_idx] = rect
        occupied.update(cells)

        # Forward-checking: prune candidates for all remaining clues
        saved: dict[int, list[Rectangle]] = {}
        feasible = True
        for p in range(pos + 1, len(unsolved)):
            ci = unsolved[p]
            old = candidates[ci]
            new = [r for r in old if not r.cells() & occupied]
            if not new:
                feasible = False
                for sci, sv in saved.items():
                    candidates[sci] = sv
                break
            saved[ci] = old
            candidates[ci] = new

        if feasible and _backtrack(unsolved, pos + 1, candidates, occupied, solution, total_cells):
            return True

        for sci, sv in saved.items():
            candidates[sci] = sv
        occupied.difference_update(cells)
        solution[clue_idx] = None

    unsolved[pos], unsolved[best_pos] = unsolved[best_pos], unsolved[pos]
    return False


def _candidate_rects(clue: Clue, grid_size: int) -> list[Rectangle]:
    """Generate all valid rectangles for a given clue.

    A rectangle is valid if:
    - It contains the clue cell.
    - It fits within the grid.
    - Its area equals ``clue.size`` (when specified).
    - Its geometry satisfies ``clue.shape``.

    Args:
        clue: The puzzle clue specifying position, shape, and optional size.
        grid_size: Side length of the grid.

    Returns:
        List of all valid ``Rectangle`` objects for this clue.
    """
    rects: list[Rectangle] = []
    for r1 in range(grid_size):
        for c1 in range(grid_size):
            for r2 in range(r1, grid_size):
                for c2 in range(c1, grid_size):
                    rect = Rectangle(r1, c1, r2, c2)
                    if not rect.contains(clue.row, clue.col):
                        continue
                    if clue.size is not None and rect.area != clue.size:
                        continue
                    if not _shape_ok(rect, clue.shape):
                        continue
                    rects.append(rect)
    return rects


def _shape_ok(rect: Rectangle, shape: ShapeConstraint) -> bool:
    """Return ``True`` if *rect* satisfies the given shape constraint.

    Args:
        rect: The rectangle to test.
        shape: The required geometric relationship between width and height.

    Returns:
        ``True`` if the shape constraint is satisfied.
    """
    if shape == ShapeConstraint.ANY:
        return True
    if shape == ShapeConstraint.SQUARE:
        return rect.width == rect.height
    if shape == ShapeConstraint.VERTICAL_RECT:
        return rect.height > rect.width
    if shape == ShapeConstraint.HORIZONTAL_RECT:
        return rect.width > rect.height
    return True


def format_solution(clues: list[Clue], solution: list[Rectangle], grid_size: int = 6) -> str:
    """Format the solved board as a letter-labelled grid string.

    Args:
        clues: The puzzle clue list (length must equal ``len(solution)``).
        solution: One ``Rectangle`` per clue.
        grid_size: Side length of the grid.

    Returns:
        A human-readable multi-line string where each cell shows the letter
        label of the rectangle that covers it.
    """
    grid = [["·"] * grid_size for _ in range(grid_size)]
    labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij"
    for i, rect in enumerate(solution):
        label = labels[i] if i < len(labels) else "?"
        for r in range(rect.r1, rect.r2 + 1):
            for c in range(rect.c1, rect.c2 + 1):
                grid[r][c] = label
    return "\n".join(" ".join(row) for row in grid)


def print_solution(clues: list[Clue], solution: list[Rectangle]) -> None:
    """Log the solved board at INFO level using letter labels.

    Args:
        clues: The puzzle clue list.
        solution: One ``Rectangle`` per clue.
    """
    logger.info("Solution:\n%s", format_solution(clues, solution))


def validate_solution(
    clues: list[Clue],
    solution: list[Rectangle],
    total_cells: int = 36,
) -> bool:
    """Return ``True`` if *solution* is a valid Patches tiling.

    Checks:
    - No two rectangles overlap.
    - Every rectangle contains its corresponding clue cell.
    - Every rectangle satisfies its shape constraint.
    - Every rectangle has the correct area (when ``clue.size`` is specified).
    - The rectangles together cover all cells exactly once.

    Args:
        clues: The puzzle clue list.
        solution: One ``Rectangle`` per clue, in the same order.
        total_cells: Total number of cells in the grid (grid_size ** 2).

    Returns:
        ``True`` if the solution is valid; ``False`` otherwise.
    """
    all_cells: set[tuple[int, int]] = set()
    for i, rect in enumerate(solution):
        cells = rect.cells()
        if cells & all_cells:
            return False
        all_cells.update(cells)
        clue = clues[i]
        if not rect.contains(clue.row, clue.col):
            return False
        if not _shape_ok(rect, clue.shape):
            return False
        if clue.size is not None and rect.area != clue.size:
            return False
    return len(all_cells) == total_cells
