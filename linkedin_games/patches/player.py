"""
Automated input for LinkedIn Patches.

Interaction model (mouse drag):
  - ``mouseDown`` on the start cell begins the drag.
  - ``mouseMove`` through intermediate cells (triggers ``onMouseEnter``).
  - ``mouseUp`` on the end cell commits the patch.

The grid container ``[data-testid="interactive-grid"]`` handles the
high-level drag events; individual cells fire ``onMouseEnter`` to track
which cell the pointer is over.

Playwright's ``page.mouse`` is used for low-level, pixel-accurate simulation.
"""

from __future__ import annotations

import logging
import random
import time

from playwright.sync_api import Page

from linkedin_games.patches.solver import Rectangle

logger = logging.getLogger(__name__)

DRAG_STEP_DELAY = 0.03
PATCH_DELAY_MIN = 0.30
PATCH_DELAY_MAX = 0.60


def play_solution(
    page: Page,
    clues: list,
    solution: list[Rectangle],
    predrawn_indices: set[int],
    grid_size: int,
    *,
    min_delay: float = PATCH_DELAY_MIN,
    max_delay: float = PATCH_DELAY_MAX,
) -> None:
    """Draw each solved patch by simulating a mouse drag.

    Pre-drawn patches (already on screen) are skipped.  For each remaining
    patch, a drag is simulated from the top-left cell to the bottom-right cell
    of its rectangle, passing through all intermediate cells.

    Args:
        page: Playwright ``Page`` connected to the Patches game.
        clues: The puzzle clue list.
        solution: One ``Rectangle`` per clue (same order as *clues*).
        predrawn_indices: Set of clue indices whose patches are already drawn
            and should not be touched.
        min_delay: Minimum random pause between patches, in seconds.
        max_delay: Maximum random pause between patches, in seconds.
    """
    cell_rects = _get_cell_rects(page, grid_size)

    patches_to_draw = [(i, rect) for i, rect in enumerate(solution) if i not in predrawn_indices]

    total = len(patches_to_draw)
    logger.info("Drawing %d patches", total)

    for idx, (clue_i, rect) in enumerate(patches_to_draw, 1):
        _draw_patch(page, rect, cell_rects, grid_size)
        logger.info(
            "[%d/%d]  Patch %d: (%d,%d)→(%d,%d)  (%d×%d)",
            idx,
            total,
            clue_i,
            rect.r1 + 1,
            rect.c1 + 1,
            rect.r2 + 1,
            rect.c2 + 1,
            rect.width,
            rect.height,
        )
        time.sleep(random.uniform(min_delay, max_delay))

    logger.info("All %d patches drawn", total)


def _draw_patch(
    page: Page,
    rect: Rectangle,
    cell_rects: list[dict],
    grid_size: int,
) -> None:
    """Simulate a mouse drag to draw one rectangular patch.

    Moves the mouse to the top-left cell, presses the button, traverses all
    cells in the rectangle row-by-row to trigger ``onMouseEnter`` events, then
    releases at the bottom-right cell.

    Args:
        page: Playwright ``Page`` connected to the Patches game.
        rect: The rectangle to draw.
        cell_rects: Pixel coordinates for all 36 cells (indexed by cell_idx).
    """
    start_idx = rect.r1 * grid_size + rect.c1
    end_idx = rect.r2 * grid_size + rect.c2

    start = cell_rects[start_idx]
    end = cell_rects[end_idx]

    page.mouse.move(start["cx"], start["cy"])
    time.sleep(0.05)
    page.mouse.down()
    time.sleep(0.05)

    for r in range(rect.r1, rect.r2 + 1):
        for c in range(rect.c1, rect.c2 + 1):
            cell_idx = r * grid_size + c
            cr = cell_rects[cell_idx]
            page.mouse.move(cr["cx"], cr["cy"])
            time.sleep(DRAG_STEP_DELAY)

    page.mouse.move(end["cx"], end["cy"])
    time.sleep(0.05)
    page.mouse.up()
    time.sleep(0.15)  # wait for the region overlay to render


def _get_cell_rects(page: Page, grid_size: int) -> list[dict]:
    """Fetch pixel bounding rectangles for all grid cells.

    Runs a single JavaScript evaluation to retrieve bounding client rects for
    every ``[data-cell-idx]`` element, sorted by cell index.

    Args:
        page: Playwright ``Page`` connected to the Patches game.

    Returns:
        A list of 36 dicts, each with keys ``x``, ``y``, ``w``, ``h``,
        ``cx`` (center-x), ``cy`` (center-y).  Indexed by ``cell_idx`` (0–35).

    Raises:
        SystemExit: If the query returns an unexpected number of elements.
    """
    rects = page.evaluate("""
    (() => {
        const cells = Array.from(document.querySelectorAll('[data-cell-idx]'))
            .sort((a, b) => parseInt(a.dataset.cellIdx) - parseInt(b.dataset.cellIdx));
        return cells.map(cell => {
            const r = cell.getBoundingClientRect();
            return {
                x: r.x, y: r.y, w: r.width, h: r.height,
                cx: r.x + r.width / 2,
                cy: r.y + r.height / 2
            };
        });
    })()
    """)

    if len(rects) != grid_size * grid_size:
        logger.error("Expected %d cell rects, got %d.", grid_size * grid_size, len(rects))
        raise SystemExit(1)

    return rects
