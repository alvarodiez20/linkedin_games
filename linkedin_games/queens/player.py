"""
Automated input for LinkedIn Queens.

Interaction model:
  - Each cell cycles through states on click:
      empty → queen (marked with a crown icon) → X (eliminated) → empty
  - A single click places a queen on an empty cell.
  - If a queen is already pre-placed we skip that cell.
  - After placing all queens the game validates automatically.

Playwright's ``page.mouse`` is used to click cell centers.
"""

from __future__ import annotations

import logging
import time

from playwright.sync_api import Page

from linkedin_games.queens.extractor import QueensState
from linkedin_games.queens.solver import QueensSolution

logger = logging.getLogger(__name__)

CLICK_DELAY = 0.25  # seconds between individual queen placements
POST_CLICK = 0.12  # short pause after each click within a sequence

# Click cycle on LinkedIn Queens: empty → X (marker) → queen → empty
# So an empty cell needs 2 clicks, a cell with X needs 1 click.


def play_solution(
    page: Page,
    state: QueensState,
    solution: QueensSolution,
) -> None:
    """Click each solved queen position in the browser.

    Cells that already have a pre-filled queen are skipped.
    If a cell needs to be reset first (e.g. it has an X marker on it),
    we click twice more to cycle back to queen state.

    Args:
        page: Playwright ``Page`` connected to the Queens game.
        state: Extracted Queens state (used to identify pre-filled queens).
        solution: The solved queen positions.
    """
    cell_rects = _get_cell_rects(page, state.grid_size)
    prefilled = state.prefilled

    queens_to_place = [(r, c) for r, c in solution.positions if not prefilled[r][c]]

    logger.info("Placing %d queens …", len(queens_to_place))

    for r, c in queens_to_place:
        cell_idx = r * state.grid_size + c
        rect = cell_rects[cell_idx]
        cx, cy = rect["cx"], rect["cy"]

        current = _get_cell_state(page, cell_idx)
        logger.debug("Cell (%d,%d) current state: %s", r + 1, c + 1, current)

        if current == "queen":
            # Already a queen — nothing to do
            logger.debug("  already a queen, skipping")
            continue
        elif current == "empty":
            # empty → X → queen  (2 clicks)
            _click(page, cx, cy)
            time.sleep(POST_CLICK)
            _click(page, cx, cy)
            time.sleep(POST_CLICK)
        elif current == "marker":
            # X → queen  (1 click)
            _click(page, cx, cy)
            time.sleep(POST_CLICK)

        logger.info("  (%d,%d) → queen", r + 1, c + 1)
        time.sleep(CLICK_DELAY)

    logger.info("All queens placed.")


def _click(page: Page, x: float, y: float) -> None:
    page.mouse.click(x, y)


def _get_cell_state(page: Page, cell_idx: int) -> str:
    """Return the current state of a cell: ``'empty'``, ``'queen'``, or ``'marker'``.

    Args:
        page: Playwright ``Page``.
        cell_idx: Zero-based flat cell index.

    Returns:
        One of ``'empty'``, ``'queen'``, or ``'marker'``.
    """
    state = page.evaluate(
        """
        (cellIdx) => {
            const cells = Array.from(document.querySelectorAll('[data-cell-idx]'))
                .sort((a, b) => parseInt(a.dataset.cellIdx) - parseInt(b.dataset.cellIdx));
            const cell = cells[cellIdx];
            if (!cell) return 'empty';
            const label = (cell.getAttribute('aria-label') || '').toLowerCase();
            if (/queen/.test(label)) return 'queen';
            if (/x|marker|elimin/i.test(label)) return 'marker';
            // check classes
            const cls = cell.className + ' ' + cell.innerHTML;
            if (/queen/i.test(cls)) return 'queen';
            if (/marker|cross|x-mark/i.test(cls)) return 'marker';
            return 'empty';
        }
        """,
        cell_idx,
    )
    return state or "empty"


def _get_cell_rects(page: Page, grid_size: int) -> list[dict]:
    """Fetch pixel bounding rectangles for all grid cells.

    Args:
        page: Playwright ``Page`` connected to the Queens game.
        grid_size: Side length of the grid.

    Returns:
        List of dicts with keys ``x``, ``y``, ``w``, ``h``, ``cx``, ``cy``,
        indexed by cell index (0-based, row-major).

    Raises:
        SystemExit: If the wrong number of cells are found.
    """
    rects = page.evaluate("""
    (() => {
        const cells = Array.from(document.querySelectorAll('[data-cell-idx]'))
            .sort((a, b) => parseInt(a.dataset.cellIdx) - parseInt(b.dataset.cellIdx));
        return cells.map(cell => {
            const r = cell.getBoundingClientRect();
            return { x: r.x, y: r.y, w: r.width, h: r.height,
                     cx: r.x + r.width / 2, cy: r.y + r.height / 2 };
        });
    })()
    """)

    expected = grid_size * grid_size
    if len(rects) != expected:
        logger.error("Expected %d cell rects, got %d.", expected, len(rects))
        raise SystemExit(1)

    return rects
