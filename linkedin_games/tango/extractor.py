"""
DOM → state extraction for LinkedIn Tango.

The Tango game renders in the **main frame** (not an iframe, unlike Sudoku).

DOM structure:
  - Grid container: ``[data-testid="interactive-grid"]``
  - Each cell:      ``div[data-cell-idx="0..35"]``
  - Cell symbol:    ``svg[data-testid]`` inside the cell
    - ``cell-zero``  → Sun  (value 1)
    - ``cell-one``   → Moon (value 2)
    - ``cell-empty`` → Empty (value 0)
  - Pre-filled:     cell has ``aria-disabled="true"``
  - Edge constraint:
    - ``svg[data-testid="edge-equal"]``   → two cells must match
    - ``svg[data-testid="edge-cross"]``   → two cells must differ
    - Direction inferred from bounding-rect center relative to the host cell.

Public API: ``extract_state(page) -> TangoState``
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from playwright.sync_api import Page

logger = logging.getLogger(__name__)

GRID_SIZE = 6
GAME_URL_FRAGMENT = "linkedin.com/games/tango"
LOAD_TIMEOUT_MS = 15_000

EMPTY = 0
SUN = 1
MOON = 2


@dataclass
class TangoState:
    """Represents the initial state of a Tango puzzle extracted from the DOM.

    Attributes:
        grid: 6×6 grid where ``0`` = empty, ``1`` = sun, ``2`` = moon.
        prefilled: 6×6 boolean grid; ``True`` where a cell carries a given clue.
        constraints: List of edge constraints as
            ``((r1, c1), (r2, c2), type)`` where *type* is ``"equal"`` or
            ``"opposite"``.
    """

    grid: list[list[int]] = field(default_factory=list)
    prefilled: list[list[bool]] = field(default_factory=list)
    constraints: list[tuple[tuple[int, int], tuple[int, int], str]] = field(default_factory=list)


def extract_state(page: Page) -> TangoState:
    """Extract the full Tango puzzle state from the live DOM.

    Waits for the board to render, then runs a single JavaScript evaluation
    to collect cell values, prefill status, and edge constraints.

    Args:
        page: Playwright ``Page`` pointing to the LinkedIn Tango tab.

    Returns:
        A ``TangoState`` dataclass populated with the current puzzle data.

    Raises:
        SystemExit: If the JavaScript evaluation returns ``None`` (board not
            loaded or unexpected DOM structure).
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
            const svg = cell.querySelector('svg[aria-label]');
            const testId = svg ? svg.getAttribute('data-testid') : null;
            const isPrefilled = cell.getAttribute('aria-disabled') === 'true';

            let value = 0;
            if (isPrefilled) {
                if (testId === 'cell-zero') value = 1;      // sun
                else if (testId === 'cell-one') value = 2;  // moon
            }

            return { value, isPrefilled };
        });

        const constraints = [];
        const edgeEls = document.querySelectorAll(
            '[data-testid="edge-cross"], [data-testid="edge-equal"]'
        );

        const cellRects = sorted.map(cell => {
            const r = cell.getBoundingClientRect();
            return { cx: r.x + r.width / 2, cy: r.y + r.height / 2 };
        });

        for (const edge of edgeEls) {
            const type = edge.dataset.testid === 'edge-equal' ? 'equal' : 'opposite';
            const rect = edge.getBoundingClientRect();
            const ex = rect.x + rect.width / 2;
            const ey = rect.y + rect.height / 2;

            const hostCell = edge.closest('[data-cell-idx]');
            if (!hostCell) continue;
            const hostIdx = parseInt(hostCell.dataset.cellIdx);
            const hostRow = Math.floor(hostIdx / 6);
            const hostCol = hostIdx % 6;
            const hostRect = cellRects[hostIdx];

            const dx = ex - hostRect.cx;
            const dy = ey - hostRect.cy;

            let neighborRow = hostRow;
            let neighborCol = hostCol;
            if (Math.abs(dx) > Math.abs(dy)) {
                neighborCol = hostCol + (dx > 0 ? 1 : -1);
            } else {
                neighborRow = hostRow + (dy > 0 ? 1 : -1);
            }

            if (neighborRow >= 0 && neighborRow < 6 && neighborCol >= 0 && neighborCol < 6) {
                constraints.push({
                    cell1: [hostRow, hostCol],
                    cell2: [neighborRow, neighborCol],
                    type: type
                });
            }
        }

        return { cellData, constraints };
    })()
    """

    result = page.evaluate(js)

    if result is None:
        logger.error("Failed to extract Tango state — board may not be loaded.")
        raise SystemExit(1)

    state = TangoState()

    cell_data = result["cellData"]
    for r in range(GRID_SIZE):
        row_vals = []
        row_pf = []
        for c in range(GRID_SIZE):
            idx = r * GRID_SIZE + c
            row_vals.append(cell_data[idx]["value"])
            row_pf.append(cell_data[idx]["isPrefilled"])
        state.grid.append(row_vals)
        state.prefilled.append(row_pf)

    for c in result["constraints"]:
        cell1 = tuple(c["cell1"])
        cell2 = tuple(c["cell2"])
        state.constraints.append((cell1, cell2, c["type"]))

    filled = sum(1 for row in state.grid for v in row if v != EMPTY)
    logger.debug("Extracted %d pre-filled cells, %d constraints", filled, len(state.constraints))
    if filled < 2:
        logger.warning(
            "Very few pre-filled cells found (%d). Board may not be fully loaded.", filled
        )

    return state


def _wait_for_board(page: Page) -> None:
    """Wait until the Tango grid cells are present in the DOM.

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
        if count < GRID_SIZE * GRID_SIZE:
            logger.error(
                "Board did not load in time (found %d cells, need %d).",
                count,
                GRID_SIZE * GRID_SIZE,
            )
            raise SystemExit(1) from None
