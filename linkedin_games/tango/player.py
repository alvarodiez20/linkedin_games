"""
Automated input for LinkedIn Tango.

Interaction model (click-to-cycle):
  - 1st click on an empty cell → Sun
  - 2nd click → Moon
  - 3rd click → back to Empty

The solver reads the ACTUAL current cell value from the DOM immediately
before clicking, so the correct number of clicks is always computed even if
the board already has partial user input.
"""

from __future__ import annotations

import logging
import random
import time

from playwright.sync_api import Page

logger = logging.getLogger(__name__)

GRID_SIZE = 6
EMPTY = 0
SUN = 1
MOON = 2


def play_solution(
    page: Page,
    original: list[list[int]],
    prefilled: list[list[bool]],
    solved: list[list[int]],
    *,
    min_delay: float = 0.20,
    max_delay: float = 0.50,
) -> None:
    """Click the empty cells to set them to the solved value.

    Skips any cell where ``prefilled[r][c]`` is ``True``.  For each remaining
    cell, reads its current DOM state and computes the minimal number of clicks
    needed to reach the target value.

    Args:
        page: Playwright ``Page`` connected to the Tango game.
        original: The 6×6 puzzle grid as extracted (``0`` = empty).
        prefilled: 6×6 boolean grid marking which cells are given clues.
        solved: The 6×6 solution grid produced by the solver.
        min_delay: Minimum random pause between cell interactions, in seconds.
        max_delay: Maximum random pause between cell interactions, in seconds.
    """
    cells_to_fill = [
        (r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) if not prefilled[r][c]
    ]

    total = len(cells_to_fill)
    sym = {SUN: "☀", MOON: "☽", EMPTY: "·"}
    logger.info("Filling %d empty cells", total)

    for idx, (r, c) in enumerate(cells_to_fill, 1):
        target = solved[r][c]
        cell_idx = r * GRID_SIZE + c

        current = _read_cell_value(page, cell_idx)

        if current == target:
            logger.debug(
                "[%d/%d] Row %d, Col %d → %s (already set)", idx, total, r + 1, c + 1, sym[target]
            )
            continue

        _set_cell(page, cell_idx, current, target)
        logger.info(
            "[%d/%d]  Row %d, Col %d → %s  (was %s)",
            idx,
            total,
            r + 1,
            c + 1,
            sym[target],
            sym[current],
        )
        time.sleep(random.uniform(min_delay, max_delay))

    logger.info("All %d cells filled", total)


def _read_cell_value(page: Page, cell_idx: int) -> int:
    """Read the actual current symbol value of a cell from the live DOM.

    Args:
        page: Playwright ``Page`` connected to the Tango game.
        cell_idx: Zero-based cell index (0–35, row-major order).

    Returns:
        ``SUN`` (1), ``MOON`` (2), or ``EMPTY`` (0).
    """
    js = """
    (cellIdx) => {
        const cell = document.querySelector(`[data-cell-idx="${cellIdx}"]`);
        if (!cell) return 0;
        const svg = cell.querySelector('svg[data-testid]');
        if (!svg) return 0;
        const testId = svg.getAttribute('data-testid');
        if (testId === 'cell-zero') return 1;  // sun
        if (testId === 'cell-one') return 2;    // moon
        return 0;
    }
    """
    return page.evaluate(js, cell_idx)


def _set_cell(page: Page, cell_idx: int, current: int, target: int) -> None:
    """Advance a cell from *current* to *target* via the minimal click sequence.

    The cycle is: ``EMPTY(0) → SUN(1) → MOON(2) → EMPTY(0) → …``

    Args:
        page: Playwright ``Page`` connected to the Tango game.
        cell_idx: Zero-based cell index (0–35).
        current: The cell's current value (``0``, ``1``, or ``2``).
        target: The desired value (``1`` or ``2``).
    """
    if current == target:
        return

    clicks = 0
    state = current
    while state != target and clicks < 3:
        state = (state + 1) % 3
        clicks += 1

    selector = f'[data-cell-idx="{cell_idx}"]'
    for _ in range(clicks):
        _click_cell(page, selector)
        time.sleep(0.12)


def _click_cell(page: Page, selector: str) -> None:
    """Fire a native browser click on a cell element.

    Tries ``page.click`` first; falls back to ``page.locator().click`` on
    failure.  Both attempts use ``force=True`` to bypass any overlay.

    Args:
        page: Playwright ``Page`` connected to the Tango game.
        selector: CSS selector for the target cell.
    """
    try:
        page.click(selector, force=True, timeout=3000)
    except Exception:
        try:
            page.locator(selector).click(force=True, timeout=3000)
        except Exception as e:
            logger.warning("Could not click %s: %s", selector, e)
