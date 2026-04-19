"""
Automated input for LinkedIn Patches.

The Patches game uses a **mouse-drag** interaction:
  - mouseDown on the start cell → begin drawing
  - mouseMove through cells (mouseEnter on each) → extend rectangle
  - mouseUp on the end cell → commit the patch

The grid container ``[data-testid="interactive-grid"]`` handles:
  ``onMouseDown``, ``onMouseMove``, ``onMouseUp``, ``onMouseLeave``

Individual cells fire ``onMouseEnter`` / ``onMouseLeave`` to track
which cell the pointer is over during the drag.

We use Playwright's low-level ``page.mouse`` to simulate real mouse events.
"""

from __future__ import annotations

import random
import sys
import time

from playwright.sync_api import Page

from linkedin_games.patches.extractor import GRID_SIZE
from linkedin_games.patches.solver import Rectangle

# Delay constants
DRAG_STEP_DELAY = 0.03   # seconds between cells during drag
PATCH_DELAY_MIN = 0.30   # minimum delay between patches
PATCH_DELAY_MAX = 0.60   # maximum delay between patches


def play_solution(
    page: Page,
    clues: list,
    solution: list[Rectangle],
    predrawn_indices: set[int],
    *,
    min_delay: float = PATCH_DELAY_MIN,
    max_delay: float = PATCH_DELAY_MAX,
) -> None:
    """
    Draw each solved patch by simulating a mouse drag.

    Parameters
    ----------
    page : Page
        Playwright page connected to the Patches game.
    clues : list[Clue]
        The puzzle clues.
    solution : list[Rectangle]
        One Rectangle per clue (same order).
    predrawn_indices : set[int]
        Indices of clues that are already drawn (skip these).
    """
    # Get cell bounding rects for pixel-accurate dragging
    cell_rects = _get_cell_rects(page)

    patches_to_draw = [
        (i, rect) for i, rect in enumerate(solution)
        if i not in predrawn_indices
    ]

    total = len(patches_to_draw)
    print(f"\n🖊️  Drawing {total} patches …")

    for idx, (clue_i, rect) in enumerate(patches_to_draw, 1):
        _draw_patch(page, rect, cell_rects)
        print(
            f"   [{idx}/{total}]  Patch {clue_i}: "
            f"({rect.r1+1},{rect.c1+1})→({rect.r2+1},{rect.c2+1})  "
            f"({rect.width}×{rect.height})"
        )
        time.sleep(random.uniform(min_delay, max_delay))

    print("\n✅  All patches drawn!")


def _draw_patch(
    page: Page,
    rect: Rectangle,
    cell_rects: list[dict],
) -> None:
    """
    Simulate a mouse drag from the top-left corner cell to the bottom-right
    corner cell of the rectangle.
    """
    start_idx = rect.r1 * GRID_SIZE + rect.c1
    end_idx = rect.r2 * GRID_SIZE + rect.c2

    start = cell_rects[start_idx]
    end = cell_rects[end_idx]

    sx = start["cx"]
    sy = start["cy"]
    ex = end["cx"]
    ey = end["cy"]

    # Move to start, press, drag to end, release
    page.mouse.move(sx, sy)
    time.sleep(0.05)
    page.mouse.down()
    time.sleep(0.05)

    # Move through intermediate cells row by row to trigger mouseEnter events
    for r in range(rect.r1, rect.r2 + 1):
        for c in range(rect.c1, rect.c2 + 1):
            cell_idx = r * GRID_SIZE + c
            cr = cell_rects[cell_idx]
            page.mouse.move(cr["cx"], cr["cy"])
            time.sleep(DRAG_STEP_DELAY)

    # Ensure we're at the exact end position
    page.mouse.move(ex, ey)
    time.sleep(0.05)
    page.mouse.up()
    time.sleep(0.15)  # wait for region to render


def _get_cell_rects(page: Page) -> list[dict]:
    """
    Get pixel coordinates (center, bounds) for all 36 cells.
    Returns a list indexed by cell_idx (0–35).
    """
    rects = page.evaluate("""
    (() => {
        const cells = Array.from(document.querySelectorAll('[data-cell-idx]'))
            .sort((a, b) => parseInt(a.dataset.cellIdx) - parseInt(b.dataset.cellIdx));
        return cells.map(cell => {
            const r = cell.getBoundingClientRect();
            return {
                x: r.x,
                y: r.y,
                w: r.width,
                h: r.height,
                cx: r.x + r.width / 2,
                cy: r.y + r.height / 2
            };
        });
    })()
    """)

    if len(rects) != GRID_SIZE * GRID_SIZE:
        print(
            "❌  Expected %d cell rects, got %d."
            % (GRID_SIZE * GRID_SIZE, len(rects)),
            file=sys.stderr,
        )
        raise SystemExit(1)

    return rects
