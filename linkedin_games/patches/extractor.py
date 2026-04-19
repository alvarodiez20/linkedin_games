"""
DOM → state extraction for LinkedIn Patches.

The Patches game renders in the **main frame** (not an iframe).

DOM structure:
  - Game container:  ``[data-testid="patches-game-container"]``
  - Grid:            ``[data-testid="interactive-grid"]`` (36 children)
  - Each cell:       ``div[data-cell-idx="0..35"]``
  - Shape clue:      ``[data-shape]`` inside a cell — maps to ShapeConstraint
  - Clue number:     ``[data-testid^="patches-clue-number"]`` text = cell count
  - Cell color:      CSS variable ``--d5a654bb`` in inline style
  - Pre-drawn cell:  ``aria-label`` contains ``"región dibujada"`` / ``"drawn region"``
  - Region member:   ``aria-label`` contains ``"en región"`` referencing clue cell

Public API: ``extract_state(page) -> PatchesState``
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum

from playwright.sync_api import Page

logger = logging.getLogger(__name__)

GRID_SIZE = 6
TOTAL_CELLS = GRID_SIZE * GRID_SIZE
LOAD_TIMEOUT_MS = 15_000


class ShapeConstraint(Enum):
    """Shape constraint for a Patches clue."""

    VERTICAL_RECT = "vertical"
    HORIZONTAL_RECT = "horizontal"
    SQUARE = "square"
    ANY = "any"


@dataclass
class Clue:
    """A single Patches clue — one per rectangle that must be drawn.

    Attributes:
        row: Zero-based row of the clue cell.
        col: Zero-based column of the clue cell.
        shape: Geometric constraint on the clue's rectangle.
        size: Required cell count, or ``None`` when the solver must infer it.
        color: Hex color string extracted from the cell's CSS variable, or
            ``None`` if absent.
    """

    row: int
    col: int
    shape: ShapeConstraint
    size: int | None
    color: str | None

    @property
    def cell_idx(self) -> int:
        """Return the zero-based flat cell index for this clue's position.

        Returns:
            ``row * GRID_SIZE + col``.
        """
        return self.row * GRID_SIZE + self.col


@dataclass
class PatchesState:
    """Full state of a Patches puzzle extracted from the DOM.

    Attributes:
        clues: Every clue on the board — one per rectangle to be drawn.
        predrawn: Already-drawn regions as ``(frozenset_of_cells, clue_index)``
            pairs.  The solver places these first before searching.
    """

    clues: list[Clue] = field(default_factory=list)
    predrawn: list[tuple[frozenset[tuple[int, int]], int]] = field(default_factory=list)


_SHAPE_MAP = {
    "PatchesShapeConstraint_VERTICAL_RECT": ShapeConstraint.VERTICAL_RECT,
    "PatchesShapeConstraint_HORIZONTAL_RECT": ShapeConstraint.HORIZONTAL_RECT,
    "PatchesShapeConstraint_SQUARE": ShapeConstraint.SQUARE,
    "PatchesShapeConstraint_UNKNOWN": ShapeConstraint.ANY,
}


def extract_state(page: Page) -> PatchesState:
    """Extract the full Patches puzzle state from the live DOM.

    Waits for the board, runs a single JS evaluation to collect cell metadata,
    then reconstructs clue list and pre-drawn regions in Python.

    Args:
        page: Playwright ``Page`` pointing to the LinkedIn Patches tab.

    Returns:
        A ``PatchesState`` dataclass with all clues and pre-drawn regions.

    Raises:
        SystemExit: If the JavaScript evaluation returns ``None``.
    """
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

            const shapeEl = cell.querySelector('[data-shape]');
            const shape = shapeEl ? shapeEl.dataset.shape : null;

            const clueEl = cell.querySelector('[data-testid^="patches-clue-number"]');
            const clueNum = clueEl ? parseInt(clueEl.textContent.trim()) : null;

            const colorMatch = style.match(/--d5a654bb:\\s*([^;]+)/);
            const color = colorMatch ? colorMatch[1].trim() : null;

            const isDrawn = label.includes('región dibujada') || label.includes('drawn region');
            const inRegionMatch = label.match(
                /en región con pista en fila (\\d+), columna (\\d+)/
            );
            const inRegionOf = inRegionMatch
                ? [(parseInt(inRegionMatch[1]) - 1), (parseInt(inRegionMatch[2]) - 1)]
                : null;

            return { idx, shape, clueNum, color, isDrawn, inRegionOf };
        });

        return { cellData };
    })()
    """

    result = page.evaluate(js)

    if result is None:
        logger.error("Failed to extract Patches state — board may not be loaded.")
        raise SystemExit(1)

    state = PatchesState()
    cell_data = result["cellData"]

    for cd in cell_data:
        if cd["shape"] is None:
            continue
        idx = cd["idx"]
        row, col = divmod(idx, GRID_SIZE)
        shape = _SHAPE_MAP.get(cd["shape"], ShapeConstraint.ANY)
        state.clues.append(
            Clue(row=row, col=col, shape=shape, size=cd["clueNum"], color=cd["color"])
        )

    drawn_clue_cells: dict[tuple[int, int], set[tuple[int, int]]] = {}
    for cd in cell_data:
        idx = cd["idx"]
        row, col = divmod(idx, GRID_SIZE)
        if cd["isDrawn"]:
            drawn_clue_cells.setdefault((row, col), set()).add((row, col))
        if cd["inRegionOf"] is not None:
            clue_rc = tuple(cd["inRegionOf"])
            drawn_clue_cells.setdefault(clue_rc, set()).add((row, col))

    for clue_rc, member_cells in drawn_clue_cells.items():
        clue_idx = next(
            (i for i, clue in enumerate(state.clues) if (clue.row, clue.col) == clue_rc),
            None,
        )
        if clue_idx is not None:
            state.predrawn.append((frozenset(member_cells), clue_idx))

    logger.debug("Extracted %d clues, %d pre-drawn regions", len(state.clues), len(state.predrawn))
    if len(state.clues) < 2:
        logger.warning(
            "Very few clues found (%d). Board may not be fully loaded.", len(state.clues)
        )

    return state


def _wait_for_board(page: Page) -> None:
    """Wait until the Patches grid cells are present in the DOM.

    Tries ``wait_for_selector`` first; falls back to a 3-second sleep and a
    manual cell-count check.

    Args:
        page: Playwright ``Page`` to poll.

    Raises:
        SystemExit: If fewer than 36 cells are found after the fallback wait.
    """
    try:
        page.wait_for_selector("[data-cell-idx]", timeout=LOAD_TIMEOUT_MS)
        logger.debug("Board ready (wait_for_selector succeeded)")
    except Exception:
        logger.warning("wait_for_selector timed out — falling back to sleep poll")
        time.sleep(3)
        count = page.evaluate("document.querySelectorAll('[data-cell-idx]').length")
        if count < TOTAL_CELLS:
            logger.error(
                "Board did not load in time (found %d cells, need %d).", count, TOTAL_CELLS
            )
            raise SystemExit(1) from None
