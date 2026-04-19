"""
DOM → state extraction for LinkedIn Patches.

The Patches game is rendered in the **main frame** (not an iframe).

DOM structure:
  - Game container:  ``[data-testid="patches-game-container"]``
  - Game board:      ``[data-testid="patches-game-board"]``  (role="group")
  - Grid:            ``[data-testid="interactive-grid"]``     (36 children, mouse events)
  - Each cell:       ``div[data-cell-idx="0..35"][data-testid="cell-N"]``  (role="button")
  - Shape clue:      ``[data-shape]`` inside a cell
    - ``PatchesShapeConstraint_VERTICAL_RECT``   → taller than wide
    - ``PatchesShapeConstraint_HORIZONTAL_RECT``  → wider than tall
    - ``PatchesShapeConstraint_SQUARE``           → equal sides
    - ``PatchesShapeConstraint_UNKNOWN``          → any shape (has a number)
  - Clue number:     ``[data-testid^="patches-clue-number"]`` → text = cell count
  - Cell color:      CSS variable ``--d5a654bb`` in inline style
  - Region overlay:  ``[data-testid^="region-overlay"]`` → already-drawn patches
  - Pre-drawn cell:  aria-label contains ``"región dibujada"`` or ``"drawn region"``
  - Region member:   aria-label contains ``"en región"`` referencing another cell

Public API:
  - ``extract_state(page) -> PatchesState``
"""

from __future__ import annotations

import re
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from playwright.sync_api import Page

GRID_SIZE = 6
TOTAL_CELLS = GRID_SIZE * GRID_SIZE
LOAD_TIMEOUT_MS = 15_000


class ShapeConstraint(Enum):
    """Shape constraint for a Patches clue."""
    VERTICAL_RECT = "vertical"    # taller than wide
    HORIZONTAL_RECT = "horizontal"  # wider than tall
    SQUARE = "square"             # equal sides
    ANY = "any"                   # any shape (UNKNOWN)


@dataclass
class Clue:
    """A single Patches clue (one per patch)."""
    row: int
    col: int
    shape: ShapeConstraint
    size: Optional[int]  # total cell count, or None (solver infers)
    color: Optional[str]  # hex color from CSS var

    @property
    def cell_idx(self) -> int:
        return self.row * GRID_SIZE + self.col


@dataclass
class PatchesState:
    """
    Full state of a Patches puzzle.

    Attributes
    ----------
    clues : list[Clue]
        Every clue on the board (one per patch to be drawn).
    predrawn : list[tuple[frozenset[tuple[int,int]], int]]
        Already-drawn regions: ``(set_of_(row,col), clue_index)``.
    """
    clues: list[Clue] = field(default_factory=list)
    predrawn: list[tuple[frozenset[tuple[int, int]], int]] = field(
        default_factory=list
    )


# ---------------------------------------------------------------------------
# Shape mapping
# ---------------------------------------------------------------------------

_SHAPE_MAP = {
    "PatchesShapeConstraint_VERTICAL_RECT": ShapeConstraint.VERTICAL_RECT,
    "PatchesShapeConstraint_HORIZONTAL_RECT": ShapeConstraint.HORIZONTAL_RECT,
    "PatchesShapeConstraint_SQUARE": ShapeConstraint.SQUARE,
    "PatchesShapeConstraint_UNKNOWN": ShapeConstraint.ANY,
}


def extract_state(page: Page) -> PatchesState:
    """Extract the full Patches puzzle state from the DOM."""
    _wait_for_board(page)

    js = """
    (() => {
        const cells = document.querySelectorAll('[data-cell-idx]');
        if (cells.length !== 36) return null;

        const sorted = Array.from(cells).sort(
            (a, b) => parseInt(a.dataset.cellIdx) - parseInt(b.dataset.cellIdx)
        );

        const cellData = sorted.map(cell => {
            const idx = parseInt(cell.dataset.cellIdx);
            const label = cell.getAttribute('aria-label') || '';
            const style = cell.getAttribute('style') || '';

            // Shape clue
            const shapeEl = cell.querySelector('[data-shape]');
            const shape = shapeEl ? shapeEl.dataset.shape : null;

            // Clue number (for UNKNOWN shapes)
            const clueEl = cell.querySelector('[data-testid^="patches-clue-number"]');
            const clueNum = clueEl ? parseInt(clueEl.textContent.trim()) : null;

            // Color from CSS variable
            const colorMatch = style.match(/--d5a654bb:\\s*([^;]+)/);
            const color = colorMatch ? colorMatch[1].trim() : null;

            // Pre-drawn status
            const isDrawn = label.includes('región dibujada') || label.includes('drawn region');
            const inRegionMatch = label.match(/en región con pista en fila (\\d+), columna (\\d+)/);
            const inRegionOf = inRegionMatch
                ? [(parseInt(inRegionMatch[1]) - 1), (parseInt(inRegionMatch[2]) - 1)]
                : null;

            return { idx, shape, clueNum, color, isDrawn, inRegionOf };
        });

        // Region overlays for already-drawn patches
        const overlays = Array.from(
            document.querySelectorAll('[data-testid^="region-overlay"]')
        ).map(el => {
            const style = el.getAttribute('style') || '';
            const text = el.textContent.trim();
            return { style, text };
        });

        return { cellData, overlays };
    })()
    """

    result = page.evaluate(js)

    if result is None:
        print("❌  Failed to extract Patches state.", file=sys.stderr)
        raise SystemExit(1)

    state = PatchesState()
    cell_data = result["cellData"]

    # Build clues from cells that have a shape constraint
    for cd in cell_data:
        if cd["shape"] is None:
            continue

        idx = cd["idx"]
        row, col = divmod(idx, GRID_SIZE)
        shape = _SHAPE_MAP.get(cd["shape"], ShapeConstraint.ANY)
        size = cd["clueNum"]  # None for shape-only clues
        color = cd["color"]

        state.clues.append(Clue(row=row, col=col, shape=shape, size=size, color=color))

    # Build pre-drawn regions
    #   - A cell with isDrawn=True is a clue cell in a drawn region
    #   - A cell with inRegionOf=[r,c] belongs to the region whose clue is at (r,c)
    drawn_clue_cells: dict[tuple[int, int], set[tuple[int, int]]] = {}

    for cd in cell_data:
        idx = cd["idx"]
        row, col = divmod(idx, GRID_SIZE)

        if cd["isDrawn"]:
            # This cell is a clue inside a drawn region
            key = (row, col)
            drawn_clue_cells.setdefault(key, set()).add((row, col))

        if cd["inRegionOf"] is not None:
            clue_rc = tuple(cd["inRegionOf"])
            drawn_clue_cells.setdefault(clue_rc, set()).add((row, col))

    for clue_rc, member_cells in drawn_clue_cells.items():
        # Find the clue index
        clue_idx = None
        for i, clue in enumerate(state.clues):
            if (clue.row, clue.col) == clue_rc:
                clue_idx = i
                break
        if clue_idx is not None:
            state.predrawn.append(
                (frozenset(member_cells), clue_idx)
            )

    # Validate
    if len(state.clues) < 2:
        print(
            "⚠️  Very few clues found (%d). Board may not be loaded." % len(state.clues),
            file=sys.stderr,
        )

    return state


def _wait_for_board(page: Page) -> None:
    """Wait until the Patches grid is rendered."""
    try:
        page.wait_for_selector('[data-cell-idx]', timeout=LOAD_TIMEOUT_MS)
    except Exception:
        time.sleep(3)
        count = page.evaluate(
            "document.querySelectorAll('[data-cell-idx]').length"
        )
        if count < TOTAL_CELLS:
            print(
                "❌  Board did not load in time (found %d cells, need %d)."
                % (count, TOTAL_CELLS),
                file=sys.stderr,
            )
            raise SystemExit(1)
