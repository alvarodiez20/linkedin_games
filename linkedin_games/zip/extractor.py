"""
DOM → state extraction for LinkedIn Zip.

The Zip game renders in the **main frame** (not an iframe).

DOM structure:
  - Cells:         ``div[data-cell-idx="0..N²-1"]`` (``data-testid="cell-{N}"``)
  - Numbered cell: has ``role="button"`` and ``aria-label="Número {N}"`` (or "Number {N}")
  - Number text:   ``div[data-cell-content="true"]`` inside the cell
  - Wall cell:     same base classes as regular cells PLUS one extra CSS class;
                   detected by comparing class sets to the modal (most-common) signature
  - Grid size:     inferred as ``int(√(total_cells))``

Public API: ``extract_state(page) → ZipState``
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field

from playwright.sync_api import Page

logger = logging.getLogger(__name__)

LOAD_TIMEOUT_MS = 15_000


@dataclass
class ZipState:
    """Full state of a Zip puzzle extracted from the DOM.

    Attributes:
        grid_size: Side length N of the N×N board.
        walls: Set of cell indices that are blocked (not part of any path).
        waypoints: Dict mapping waypoint number → cell index.  There are
            ``grid_size`` or fewer waypoints; the path must visit them in
            ascending numerical order.
    """

    grid_size: int
    walls: set[int] = field(default_factory=set)
    waypoints: dict[int, int] = field(default_factory=dict)  # number → cell_idx

    @property
    def passable(self) -> set[int]:
        """All non-wall cell indices."""
        return set(range(self.grid_size**2)) - self.walls

    @property
    def max_waypoint(self) -> int:
        return max(self.waypoints) if self.waypoints else 0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_state(page: Page) -> ZipState:
    """Extract the Zip puzzle state from the live DOM.

    Args:
        page: Playwright ``Page`` pointing to the LinkedIn Zip tab.

    Returns:
        A ``ZipState`` with grid size, wall set, and waypoint map.

    Raises:
        SystemExit: If the board is not loaded or extraction fails.
    """
    _wait_for_board(page)

    result = page.evaluate(r"""
    (() => {
        const cells = Array.from(document.querySelectorAll('[data-cell-idx]'))
            .sort((a, b) => parseInt(a.dataset.cellIdx) - parseInt(b.dataset.cellIdx));

        const nCells = cells.length;
        const gridSize = Math.round(Math.sqrt(nCells));
        if (gridSize * gridSize !== nCells || nCells < 4) {
            return { error: `Unexpected cell count: ${nCells}` };
        }

        // --- Wall detection ---
        // Collect the class signature (sorted class list) of every non-numbered cell.
        // The most common signature is the "normal" cell signature.
        // Cells with a different signature (extra classes) are walls.
        const sigFreq = {};
        const numbered = new Set();
        cells.forEach(cell => {
            if (cell.getAttribute('role') === 'button') {
                numbered.add(parseInt(cell.dataset.cellIdx));
                return;
            }
            const sig = Array.from(cell.classList).sort().join(' ');
            sigFreq[sig] = (sigFreq[sig] || 0) + 1;
        });
        const normalSig = Object.entries(sigFreq).sort((a, b) => b[1] - a[1])[0]?.[0] || '';

        const cellData = cells.map(cell => {
            const idx = parseInt(cell.dataset.cellIdx);
            const isNumbered = cell.getAttribute('role') === 'button';
            const label = cell.getAttribute('aria-label') || '';

            // Extract number from aria-label like "Número 3" or "Number 3"
            const numMatch = label.match(/\d+/);
            const number = numMatch ? parseInt(numMatch[0]) : null;

            // Wall: not numbered AND has a different class signature from normal
            const sig = Array.from(cell.classList).sort().join(' ');
            const isWall = !isNumbered && sig !== normalSig;

            return { idx, isWall, isNumbered, number };
        });

        const walls = cellData.filter(c => c.isWall).map(c => c.idx);
        const waypoints = {};
        cellData.filter(c => c.isNumbered && c.number !== null)
                .forEach(c => { waypoints[c.number] = c.idx; });

        return { gridSize, nCells, walls, waypoints };
    })()
    """)

    if result is None:
        logger.error("JS evaluation returned null — board may not be loaded.")
        raise SystemExit(1)

    if "error" in result:
        logger.error("Failed to extract Zip state: %s", result["error"])
        raise SystemExit(1)

    state = ZipState(
        grid_size=result["gridSize"],
        walls=set(result["walls"]),
        waypoints={int(k): v for k, v in result["waypoints"].items()},
    )

    logger.debug(
        "Extracted: grid=%dx%d  walls=%d  waypoints=%d  passable=%d",
        state.grid_size,
        state.grid_size,
        len(state.walls),
        len(state.waypoints),
        len(state.passable),
    )
    return state


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _wait_for_board(page: Page) -> None:
    """Poll until the board is fully rendered (cells + at least one waypoint).

    Args:
        page: Playwright ``Page`` to poll.

    Raises:
        SystemExit: If the board does not appear within the timeout.
    """
    poll_interval = 0.5
    max_attempts = int(LOAD_TIMEOUT_MS / 1000 / poll_interval) + 1

    logger.debug("Waiting for Zip board to render …")

    try:
        page.wait_for_selector("[data-cell-idx]", timeout=LOAD_TIMEOUT_MS)
    except Exception:
        logger.error("No [data-cell-idx] cells found within %ds.", LOAD_TIMEOUT_MS // 1000)
        raise SystemExit(1) from None

    for attempt in range(1, max_attempts + 1):
        counts = page.evaluate("""
        (() => {
            const cells = document.querySelectorAll('[data-cell-idx]');
            const numbered = document.querySelectorAll('[data-cell-idx][role="button"]');
            return { cells: cells.length, numbered: numbered.length };
        })()
        """)
        n, w = counts["cells"], counts["numbered"]
        gs = round(math.sqrt(n))
        if gs * gs == n and n >= 4 and w > 0:
            logger.debug("Board ready: %dx%d, %d waypoints (attempt %d)", gs, gs, w, attempt)
            return
        logger.debug(
            "Waiting … cells=%d  waypoints=%d  (attempt %d/%d)", n, w, attempt, max_attempts
        )
        time.sleep(poll_interval)

    logger.error("Zip board did not render in time.")
    raise SystemExit(1)
