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

from dataclasses import dataclass
from typing import Optional

from linkedin_games.patches.extractor import (
    GRID_SIZE,
    TOTAL_CELLS,
    Clue,
    PatchesState,
    ShapeConstraint,
)


@dataclass(frozen=True)
class Rectangle:
    """Axis-aligned rectangle: top-left (r1,c1) to bottom-right (r2,c2) inclusive."""
    r1: int
    c1: int
    r2: int
    c2: int

    @property
    def width(self) -> int:
        return self.c2 - self.c1 + 1

    @property
    def height(self) -> int:
        return self.r2 - self.r1 + 1

    @property
    def area(self) -> int:
        return self.width * self.height

    def cells(self) -> frozenset[tuple[int, int]]:
        return frozenset(
            (r, c)
            for r in range(self.r1, self.r2 + 1)
            for c in range(self.c1, self.c2 + 1)
        )

    def contains(self, row: int, col: int) -> bool:
        return self.r1 <= row <= self.r2 and self.c1 <= col <= self.c2


def solve(state: PatchesState) -> Optional[list[Rectangle]]:
    """
    Solve a Patches puzzle.

    Returns a list of Rectangles (one per clue, same order as ``state.clues``)
    or ``None`` if unsolvable.
    """
    n_clues = len(state.clues)

    # Pre-compute candidates for each clue
    candidates: list[list[Rectangle]] = []
    for clue in state.clues:
        candidates.append(_candidate_rects(clue))

    # Occupied grid: set of (row, col) already filled
    occupied: set[tuple[int, int]] = set()

    # Solution: clue_idx → Rectangle
    solution: list[Optional[Rectangle]] = [None] * n_clues

    # Place pre-drawn regions first
    for region_cells, clue_idx in state.predrawn:
        clue = state.clues[clue_idx]
        # Find the matching rectangle candidate
        matched = False
        for rect in candidates[clue_idx]:
            if rect.cells() == region_cells:
                solution[clue_idx] = rect
                occupied.update(region_cells)
                matched = True
                break
        if not matched:
            # Pre-drawn region doesn't match any candidate.
            # Force it: build a bounding-box rect from the cells.
            rows = [r for r, c in region_cells]
            cols = [c for r, c in region_cells]
            rect = Rectangle(min(rows), min(cols), max(rows), max(cols))
            solution[clue_idx] = rect
            occupied.update(region_cells)

    # Remaining clues to solve
    unsolved = [i for i in range(n_clues) if solution[i] is None]

    # Filter candidates against currently occupied cells
    for i in unsolved:
        candidates[i] = [
            r for r in candidates[i] if not r.cells() & occupied
        ]

    if _backtrack(unsolved, 0, candidates, occupied, solution):
        return solution  # type: ignore[return-value]

    return None


def _backtrack(
    unsolved: list[int],
    pos: int,
    candidates: list[list[Rectangle]],
    occupied: set[tuple[int, int]],
    solution: list[Optional[Rectangle]],
) -> bool:
    if pos == len(unsolved):
        return len(occupied) == TOTAL_CELLS

    # MRV: pick the unsolved clue with fewest remaining candidates
    best_pos = pos
    best_count = len(candidates[unsolved[pos]])
    for p in range(pos + 1, len(unsolved)):
        c = len(candidates[unsolved[p]])
        if c < best_count:
            best_count = c
            best_pos = p

    # Swap to front
    unsolved[pos], unsolved[best_pos] = unsolved[best_pos], unsolved[pos]

    clue_idx = unsolved[pos]

    for rect in candidates[clue_idx]:
        cells = rect.cells()

        # Check no overlap
        if cells & occupied:
            continue

        # Place
        solution[clue_idx] = rect
        occupied.update(cells)

        # Forward-check: prune candidates for remaining clues
        saved: dict[int, list[Rectangle]] = {}
        feasible = True
        for p in range(pos + 1, len(unsolved)):
            ci = unsolved[p]
            old = candidates[ci]
            new = [r for r in old if not r.cells() & occupied]
            if not new:
                feasible = False
                # Restore already-pruned
                for sci, sv in saved.items():
                    candidates[sci] = sv
                break
            saved[ci] = old
            candidates[ci] = new

        if feasible and _backtrack(unsolved, pos + 1, candidates, occupied, solution):
            return True

        # Undo
        for sci, sv in saved.items():
            candidates[sci] = sv
        occupied.difference_update(cells)
        solution[clue_idx] = None

    # Swap back
    unsolved[pos], unsolved[best_pos] = unsolved[best_pos], unsolved[pos]
    return False


def _candidate_rects(clue: Clue) -> list[Rectangle]:
    """
    Generate all valid rectangles for a clue.

    A valid rectangle:
      - Contains the clue cell (row, col)
      - Fits within the 6×6 grid
      - Satisfies the shape constraint
      - If size is given, has area == size
    """
    rects: list[Rectangle] = []

    for r1 in range(GRID_SIZE):
        for c1 in range(GRID_SIZE):
            for r2 in range(r1, GRID_SIZE):
                for c2 in range(c1, GRID_SIZE):
                    rect = Rectangle(r1, c1, r2, c2)

                    # Must contain the clue cell
                    if not rect.contains(clue.row, clue.col):
                        continue

                    # Check size constraint
                    if clue.size is not None and rect.area != clue.size:
                        continue

                    # Minimum area of 1
                    if rect.area < 1:
                        continue

                    # Check shape constraint
                    if not _shape_ok(rect, clue.shape):
                        continue

                    rects.append(rect)

    return rects


def _shape_ok(rect: Rectangle, shape: ShapeConstraint) -> bool:
    """Check if a rectangle satisfies the shape constraint."""
    if shape == ShapeConstraint.ANY:
        return True
    if shape == ShapeConstraint.SQUARE:
        return rect.width == rect.height
    if shape == ShapeConstraint.VERTICAL_RECT:
        return rect.height > rect.width
    if shape == ShapeConstraint.HORIZONTAL_RECT:
        return rect.width > rect.height
    return True


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def print_solution(clues: list[Clue], solution: list[Rectangle]) -> None:
    """Pretty-print the solved board with letter labels for each patch."""
    grid = [["·"] * GRID_SIZE for _ in range(GRID_SIZE)]
    labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij"

    for i, rect in enumerate(solution):
        label = labels[i] if i < len(labels) else "?"
        for r in range(rect.r1, rect.r2 + 1):
            for c in range(rect.c1, rect.c2 + 1):
                grid[r][c] = label

    for row in grid:
        print(" ".join(row))


def validate_solution(
    clues: list[Clue],
    solution: list[Rectangle],
) -> bool:
    """Check that a solution is valid: full coverage, no overlap, constraints met."""
    all_cells: set[tuple[int, int]] = set()

    for i, rect in enumerate(solution):
        cells = rect.cells()

        # Check overlap
        overlap = cells & all_cells
        if overlap:
            return False
        all_cells.update(cells)

        # Check clue is inside
        clue = clues[i]
        if not rect.contains(clue.row, clue.col):
            return False

        # Check shape
        if not _shape_ok(rect, clue.shape):
            return False

        # Check size
        if clue.size is not None and rect.area != clue.size:
            return False

    # Check full coverage
    if len(all_cells) != TOTAL_CELLS:
        return False

    return True
