"""
Automated input for LinkedIn Zip.

Interaction model:
  - The user draws the path by clicking and dragging through cells.
  - The game registers a trail as the mouse passes through each cell.
  - We simulate: mousedown on cell 1 → mousemove through every cell in
    path order → mouseup on the last cell.

All moves use orthogonal steps so the path is always continuous.
"""

from __future__ import annotations

import logging
import time

from playwright.sync_api import Page

from linkedin_games.zip.extractor import ZipState

logger = logging.getLogger(__name__)

MOVE_DELAY = 0.02  # seconds between mousemove steps
POST_DRAG = 0.30  # pause after completing the drag


def play_solution(page: Page, state: ZipState, path: list[int]) -> None:
    """Draw the solution path in the browser by simulating a mouse drag.

    Args:
        page: Playwright ``Page`` connected to the Zip game.
        state: Extracted puzzle state (used for grid size).
        path: Ordered list of cell indices representing the solution.
    """
    cell_rects = _get_cell_rects(page, state.grid_size)

    if not path:
        logger.error("Empty path — nothing to draw.")
        return

    logger.info("Drawing path of %d cells …", len(path))

    start = cell_rects[path[0]]
    page.mouse.move(start["cx"], start["cy"])
    time.sleep(0.05)
    page.mouse.down()
    time.sleep(0.05)

    for cell_idx in path[1:]:
        rect = cell_rects[cell_idx]
        page.mouse.move(rect["cx"], rect["cy"])
        time.sleep(MOVE_DELAY)

    end = cell_rects[path[-1]]
    page.mouse.move(end["cx"], end["cy"])
    time.sleep(0.05)
    page.mouse.up()
    time.sleep(POST_DRAG)

    logger.info("Path drawn — %d cells covered.", len(path))


def _get_cell_rects(page: Page, grid_size: int) -> list[dict]:
    """Fetch pixel bounding rectangles for all grid cells.

    Args:
        page: Playwright ``Page`` connected to the Zip game.
        grid_size: Side length of the grid.

    Returns:
        List of dicts (``x``, ``y``, ``w``, ``h``, ``cx``, ``cy``) indexed
        by cell index (0-based, row-major).

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
