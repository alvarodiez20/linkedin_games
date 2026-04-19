"""
Automated input for LinkedIn Tango.

The Tango game uses a click-to-cycle interaction:
  - 1st click on empty cell → Sun
  - 2nd click → Moon
  - 3rd click → back to Empty

Uses Playwright's native click (browser-level mouse simulation)
because the game uses React event delegation.

Before clicking, reads each cell's ACTUAL current value from the DOM
to correctly calculate how many clicks are needed.
"""

from __future__ import annotations

import time
import random
import sys

from playwright.sync_api import Page

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
    """
    Click the empty cells to set them to the solved value.
    """
    cells_to_fill = [
        (r, c)
        for r in range(GRID_SIZE)
        for c in range(GRID_SIZE)
        if not prefilled[r][c]
    ]

    total = len(cells_to_fill)
    sym = {SUN: "☀", MOON: "☽", EMPTY: "·"}
    print(f"\n🖊️  Filling {total} empty cells …")

    for idx, (r, c) in enumerate(cells_to_fill, 1):
        target = solved[r][c]
        cell_idx = r * GRID_SIZE + c

        # Read the ACTUAL current value from the DOM right before clicking
        current = _read_cell_value(page, cell_idx)

        if current == target:
            print(f"   [{idx}/{total}]  Row {r+1}, Col {c+1} → {sym[target]} (already set)")
            continue

        _set_cell(page, cell_idx, current, target)
        print(f"   [{idx}/{total}]  Row {r+1}, Col {c+1} → {sym[target]}  (was {sym[current]})")
        time.sleep(random.uniform(min_delay, max_delay))

    print("\n✅  All cells filled!")


def _read_cell_value(page: Page, cell_idx: int) -> int:
    """Read the actual current value of a cell from the DOM."""
    js = """
    (cellIdx) => {
        const cell = document.querySelector(`[data-cell-idx="${cellIdx}"]`);
        if (!cell) return 0;
        const svg = cell.querySelector('svg[data-testid]');
        if (!svg) return 0;
        const testId = svg.getAttribute('data-testid');
        if (testId === 'cell-zero') return 1;  // sun
        if (testId === 'cell-one') return 2;    // moon
        return 0; // empty
    }
    """
    return page.evaluate(js, cell_idx)


def _set_cell(page: Page, cell_idx: int, current: int, target: int) -> None:
    """
    Click cell to cycle from *current* to *target*.

    Cycle order: empty(0) → sun(1) → moon(2) → empty(0)
    """
    if current == target:
        return

    # Calculate clicks needed to go from current to target
    # Cycle: 0 → 1 → 2 → 0 → ...
    clicks = 0
    state = current
    while state != target and clicks < 3:
        # Advance one step in the cycle
        state = (state + 1) % 3
        clicks += 1

    selector = f'[data-cell-idx="{cell_idx}"]'
    for i in range(clicks):
        _click_cell(page, selector)
        time.sleep(0.12)


def _click_cell(page: Page, selector: str) -> None:
    """
    Click a cell using Playwright's native click (real browser mouse events).
    """
    try:
        page.click(selector, force=True, timeout=3000)
    except Exception:
        try:
            page.locator(selector).click(force=True, timeout=3000)
        except Exception as e:
            print(f"⚠️  Could not click {selector}: {e}", file=sys.stderr)
