"""
DOM → state extraction for LinkedIn Tango.

The Tango game is rendered in the **main frame** (not an iframe, unlike Sudoku).

DOM structure:
  - Grid container: ``[data-testid="interactive-grid"]``
  - Each cell:      ``div[data-cell-idx="0..35"][data-testid="cell-N"]``
  - Cell content:   ``svg[aria-label]`` inside each cell
    - ``aria-label="Sol"`` / ``"Sun"``  → sun  (``data-testid="cell-zero"``)
    - ``aria-label="Luna"`` / ``"Moon"`` → moon (``data-testid="cell-one"``)
    - ``aria-label="Vacío"`` / ``"Empty"`` → empty (``data-testid="cell-empty"``)
  - Pre-filled:     cell has ``aria-disabled="true"``
  - Constraints:    ``svg[data-testid="edge-cross"]`` or ``svg[data-testid="edge-equal"]``
    - Nested inside a cell div (grandparent = the cell with ``data-cell-idx``)
    - Position determines which neighbor the constraint connects to:
      - Right-positioned (``_09d57bc7`` class on parent) → constraint with cell to the right
      - Bottom-positioned (``_7284be76`` class on parent) → constraint with cell below

Public API:
  - ``extract_state(page) -> TangoState``
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field

from playwright.sync_api import Page

GRID_SIZE = 6
GAME_URL_FRAGMENT = "linkedin.com/games/tango"
LOAD_TIMEOUT_MS = 15_000

# Cell values
EMPTY = 0
SUN = 1
MOON = 2


@dataclass
class TangoState:
    """
    Represents the initial state of a Tango puzzle.

    Attributes
    ----------
    grid : list[list[int]]
        6×6 grid where 0=empty, 1=sun, 2=moon.
    prefilled : list[list[bool]]
        6×6 grid indicating which cells are pre-filled.
    constraints : list[tuple[tuple[int,int], tuple[int,int], str]]
        List of ``((r1,c1), (r2,c2), type)`` where type is ``"equal"`` or ``"opposite"``.
    """
    grid: list[list[int]] = field(default_factory=list)
    prefilled: list[list[bool]] = field(default_factory=list)
    constraints: list[tuple[tuple[int, int], tuple[int, int], str]] = field(
        default_factory=list
    )


def extract_state(page: Page) -> TangoState:
    """Extract the full Tango puzzle state from the DOM."""
    _wait_for_board(page)

    js = """
    (() => {
        const cells = document.querySelectorAll('[data-cell-idx]');
        if (cells.length !== 36) return null;

        const sorted = Array.from(cells).sort(
            (a, b) => parseInt(a.dataset.cellIdx) - parseInt(b.dataset.cellIdx)
        );

        // Extract cell data
        const cellData = sorted.map(cell => {
            const svg = cell.querySelector('svg[aria-label]');
            const testId = svg ? svg.getAttribute('data-testid') : null;
            const isPrefilled = cell.getAttribute('aria-disabled') === 'true';

            let value = 0; // empty
            // Only read values from prefilled cells to get the original puzzle
            if (isPrefilled) {
                if (testId === 'cell-zero') value = 1; // sun
                else if (testId === 'cell-one') value = 2; // moon
            }

            return { value, isPrefilled };
        });

        // Extract constraints by position
        // Constraints are SVGs with data-testid = "edge-cross" or "edge-equal"
        // They sit inside a cell div and face either right or bottom
        const constraints = [];
        const edgeEls = document.querySelectorAll('[data-testid="edge-cross"], [data-testid="edge-equal"]');

        // Get cell bounding rects for spatial mapping
        const cellRects = sorted.map(cell => {
            const r = cell.getBoundingClientRect();
            return { x: r.x, y: r.y, w: r.width, h: r.height, cx: r.x + r.width/2, cy: r.y + r.height/2 };
        });

        for (const edge of edgeEls) {
            const type = edge.dataset.testid === 'edge-equal' ? 'equal' : 'opposite';
            const rect = edge.getBoundingClientRect();
            const ex = rect.x + rect.width / 2;
            const ey = rect.y + rect.height / 2;

            // Find the grandparent cell (the cell this constraint is inside)
            let hostCell = edge.closest('[data-cell-idx]');
            if (!hostCell) continue;
            const hostIdx = parseInt(hostCell.dataset.cellIdx);
            const hostRow = Math.floor(hostIdx / 6);
            const hostCol = hostIdx % 6;
            const hostRect = cellRects[hostIdx];

            // Determine direction: is the edge to the right or below the host cell center?
            const dx = ex - hostRect.cx;
            const dy = ey - hostRect.cy;

            let neighborRow = hostRow;
            let neighborCol = hostCol;
            if (Math.abs(dx) > Math.abs(dy)) {
                // Horizontal → right neighbor
                neighborCol = hostCol + (dx > 0 ? 1 : -1);
            } else {
                // Vertical → bottom neighbor
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
        print("❌  Failed to extract Tango state.", file=sys.stderr)
        raise SystemExit(1)

    state = TangoState()

    # Build grid and prefilled from cellData
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

    # Build constraints
    for c in result["constraints"]:
        cell1 = tuple(c["cell1"])
        cell2 = tuple(c["cell2"])
        state.constraints.append((cell1, cell2, c["type"]))

    # Validate
    filled = sum(1 for row in state.grid for v in row if v != EMPTY)
    if filled < 2:
        print("⚠️  Very few pre-filled cells found (%d). Board may not be loaded." % filled,
              file=sys.stderr)

    return state


def _wait_for_board(page: Page) -> None:
    """Wait until the Tango grid is rendered."""
    try:
        page.wait_for_selector('[data-cell-idx]', timeout=LOAD_TIMEOUT_MS)
    except Exception:
        time.sleep(3)
        count = page.evaluate(
            "document.querySelectorAll('[data-cell-idx]').length"
        )
        if count < GRID_SIZE * GRID_SIZE:
            print(
                "❌  Board did not load in time (found %d cells, need %d)."
                % (count, GRID_SIZE * GRID_SIZE),
                file=sys.stderr,
            )
            raise SystemExit(1)
