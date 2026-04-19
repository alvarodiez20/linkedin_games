"""
Automated input — fills the solved numbers into the LinkedIn Sudoku UI.

Interaction model:
  1. Click on a cell (``div.sudoku-cell[data-cell-idx]``) to select it.
  2. Click a number button (``button.sudoku-input-button``) to enter a digit.

Number buttons live in ``div.sudoku-input-buttons__numbers`` and correspond
to digits 1–6 in order.

The DOM re-renders after each input, so element handles become stale.
Selectors are re-queried before every interaction; ``force=True`` bypasses
overlay/intercept issues.
"""

from __future__ import annotations

import logging
import random
import time

from playwright.sync_api import Frame, Page

from linkedin_games.sudoku.extractor import get_game_frame

logger = logging.getLogger(__name__)

GRID_SIZE = 6


def play_solution(
    page: Page,
    original: list[list[int]],
    solved: list[list[int]],
    *,
    min_delay: float = 0.20,
    max_delay: float = 0.50,
) -> None:
    """Fill the solved digits into every cell that was originally empty.

    Only cells where ``original[r][c] == 0`` are touched; pre-filled clue
    cells are skipped.

    Args:
        page: Playwright ``Page`` connected to the Sudoku game.
        original: The ``6×6`` puzzle grid as extracted (``0`` = empty).
        solved: The ``6×6`` solution grid produced by the solver.
        min_delay: Minimum random pause between cell fills, in seconds.
        max_delay: Maximum random pause between cell fills, in seconds.
    """
    frame = get_game_frame(page)

    cells_to_fill = [
        (r, c)
        for r in range(GRID_SIZE)
        for c in range(GRID_SIZE)
        if original[r][c] == 0
    ]

    total = len(cells_to_fill)
    logger.info("Filling %d empty cells", total)

    for idx, (r, c) in enumerate(cells_to_fill, 1):
        digit = solved[r][c]
        cell_idx = r * GRID_SIZE + c
        _fill_cell(frame, cell_idx, digit)
        logger.info("[%d/%d]  Row %d, Col %d → %d", idx, total, r + 1, c + 1, digit)
        time.sleep(random.uniform(min_delay, max_delay))

    logger.info("All %d cells filled", total)


def _fill_cell(frame: Frame, cell_idx: int, digit: int) -> None:
    """Click a cell then click the corresponding number button.

    Uses Playwright's native locator-based clicks (CDP-level mouse events) so
    that React's synthetic event system processes them correctly.  JavaScript
    ``dispatchEvent`` / ``element.click()`` are intentionally avoided because
    React ignores them.

    Args:
        frame: The game iframe ``Frame``.
        cell_idx: Zero-based cell index (0–35, row-major order).
        digit: The digit to enter (1–6).
    """
    cell_sel = f'.sudoku-cell[data-cell-idx="{cell_idx}"]'
    btn_sel = f'.sudoku-input-buttons__numbers .sudoku-input-button:nth-child({digit})'

    try:
        frame.locator(cell_sel).click(timeout=5000)
        time.sleep(0.1)  # let React process the cell-selection state update
        frame.locator(btn_sel).click(timeout=5000)
    except Exception as e:
        logger.warning("Failed to fill cell %d with digit %d: %s", cell_idx, digit, e)
