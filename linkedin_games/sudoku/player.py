"""
Automated input — fills the solved numbers into the LinkedIn game UI.

The game interaction model:
  1. Click on a cell (``div.sudoku-cell[data-cell-idx]``) to select it.
  2. Click a number button (``button.sudoku-input-button``) to enter a digit.

The number buttons are in ``div.sudoku-input-buttons__numbers`` and correspond
to digits 1–6 in order.

Important: The DOM re-renders after each input, so element handles become stale.
We re-query selectors before every interaction and use ``force=True`` clicks
to bypass overlay/intercept issues.
"""

from __future__ import annotations

import time
import random

from playwright.sync_api import Frame, Page

from linkedin_games.sudoku.extractor import get_game_frame

GRID_SIZE = 6


def play_solution(
    page: Page,
    original: list[list[int]],
    solved: list[list[int]],
    *,
    min_delay: float = 0.20,
    max_delay: float = 0.50,
) -> None:
    """
    Type the solved digits into the browser for every cell that was
    originally empty (``original[r][c] == 0``).
    """
    frame = get_game_frame(page)

    cells_to_fill = [
        (r, c)
        for r in range(GRID_SIZE)
        for c in range(GRID_SIZE)
        if original[r][c] == 0
    ]

    total = len(cells_to_fill)
    print(f"\n🖊️  Filling {total} empty cells …")

    for idx, (r, c) in enumerate(cells_to_fill, 1):
        digit = solved[r][c]
        cell_idx = r * GRID_SIZE + c
        _fill_cell(frame, cell_idx, digit)
        print(f"   [{idx}/{total}]  Row {r+1}, Col {c+1} → {digit}")
        time.sleep(random.uniform(min_delay, max_delay))

    print("\n✅  All cells filled!")


def _fill_cell(frame: Frame, cell_idx: int, digit: int) -> None:
    """
    Click cell *cell_idx*, then click the number button for *digit*.

    Uses Playwright's native locator clicks (CDP-level mouse events) so that
    React's synthetic event system processes them correctly.  JavaScript
    dispatchEvent / element.click() are not used because React ignores them.
    """
    cell_sel = f'.sudoku-cell[data-cell-idx="{cell_idx}"]'
    btn_sel = f'.sudoku-input-buttons__numbers .sudoku-input-button:nth-child({digit})'

    try:
        frame.locator(cell_sel).click(timeout=5000)
        time.sleep(0.1)  # let React process the cell-selection state update
        frame.locator(btn_sel).click(timeout=5000)
    except Exception as e:
        print(f"⚠️  Failed to fill cell {cell_idx} with digit {digit}: {e}")
