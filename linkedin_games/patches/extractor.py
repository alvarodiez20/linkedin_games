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

    def cell_idx(self, grid_size: int) -> int:
        """Return the zero-based flat cell index for this clue's position.

        Args:
            grid_size: The side length of the grid.

        Returns:
            ``row * grid_size + col``.
        """
        return self.row * grid_size + self.col


@dataclass
class PatchesState:
    """Full state of a Patches puzzle extracted from the DOM.

    Attributes:
        clues: Every clue on the board — one per rectangle to be drawn.
        predrawn: Already-drawn regions as ``(frozenset_of_cells, clue_index)``
            pairs.  The solver places these first before searching.
    """

    grid_size: int = 6
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
        const nCells = cells.length;
        const gridSize = Math.sqrt(nCells);
        if (nCells < 16 || !Number.isInteger(gridSize)) {
            return { error: `Invalid cell count: ${nCells}` };
        }

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

        return { cellData, gridSize, nCells };
    })()
    """

    result = page.evaluate(js)

    if result is None:
        logger.error("Failed to extract Patches state — JS evaluation unexpectedly returned null.")
        raise SystemExit(1)

    if "error" in result:
        logger.error("Failed to extract Patches state: %s", result["error"])
        raise SystemExit(1)

    state = PatchesState(grid_size=int(result["gridSize"]))
    cell_data = result["cellData"]

    for cd in cell_data:
        if cd["shape"] is None:
            continue
        idx = cd["idx"]
        row, col = divmod(idx, state.grid_size)
        shape = _SHAPE_MAP.get(cd["shape"], ShapeConstraint.ANY)
        state.clues.append(
            Clue(row=row, col=col, shape=shape, size=cd["clueNum"], color=cd["color"])
        )

    drawn_clue_cells: dict[tuple[int, int], set[tuple[int, int]]] = {}
    for cd in cell_data:
        idx = cd["idx"]
        row, col = divmod(idx, state.grid_size)
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
    """Wait until the Patches grid is fully rendered in the DOM.

    The game's React app may mount the grid container and cell elements before
    populating the ``data-shape`` attributes that carry the clue information.
    This function waits for **both** conditions:

    1. At least 16 ``[data-cell-idx]`` cells are present (and count is a perfect square).
    2. At least one ``[data-shape]`` element exists (clues have rendered).

    A polling loop with a generous timeout ensures the page has time to
    complete its JavaScript rendering even on slow connections.

    Args:
        page: Playwright ``Page`` to poll.

    Raises:
        SystemExit: If the board does not fully render within the timeout.
    """
    poll_interval = 0.5  # seconds between polls
    max_attempts = int(LOAD_TIMEOUT_MS / 1000 / poll_interval) + 1

    logger.debug("Waiting for board to fully render (up to %ds) …", LOAD_TIMEOUT_MS // 1000)

    # First, wait for at least one cell element to appear in the DOM.
    try:
        page.wait_for_selector("[data-cell-idx]", timeout=LOAD_TIMEOUT_MS)
        logger.debug("Cell elements detected in the DOM")
    except Exception:
        logger.error("No cell elements appeared within %ds", LOAD_TIMEOUT_MS // 1000)
        raise SystemExit(1) from None

    # Then poll until all 36 cells exist AND at least one shape clue has rendered.
    for attempt in range(1, max_attempts + 1):
        counts = page.evaluate("""
        (() => {
            const cells = document.querySelectorAll('[data-cell-idx]').length;
            const shapes = document.querySelectorAll('[data-shape]').length;
            return { cells, shapes };
        })()
        """)

        cell_count = counts["cells"]
        shape_count = counts["shapes"]

        if cell_count >= 16 and int(cell_count**0.5) ** 2 == cell_count and shape_count > 0:
            logger.debug(
                "Board ready: %d cells, %d shape clues (attempt %d)",
                cell_count,
                shape_count,
                attempt,
            )
            return

        logger.debug(
            "Waiting … cells=%d  shapes=%d  (attempt %d/%d)",
            cell_count,
            shape_count,
            attempt,
            max_attempts,
        )
        time.sleep(poll_interval)

    logger.error(
        "Board did not fully load in time (found %d cells, %d shapes).",
        cell_count,
        shape_count,
    )
    raise SystemExit(1)
