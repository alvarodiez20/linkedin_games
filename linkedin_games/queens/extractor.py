"""
DOM → state extraction for LinkedIn Queens.

The Queens game renders in the **main frame** (not an iframe).

DOM structure (observed patterns):
  - Game container:  ``[data-testid="queens-game-container"]`` or similar
  - Grid cells:      ``[data-cell-idx]`` or ``[data-row][data-col]``
  - Color regions:   indicated by a CSS class or ``data-cell-color`` attribute on each cell
  - Queen placed:    cell has ``aria-label`` containing ``"queen"`` or a child element with
                     a queen SVG / class ``queens-cell-with-queen``
  - Cell states:     clicking cycles  empty → queen → X (marker) → empty

The solver only needs the grid size and the color map (which color each cell belongs to).

Public API: ``extract_state(page) -> QueensState``
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from playwright.sync_api import Page

logger = logging.getLogger(__name__)

LOAD_TIMEOUT_MS = 15_000


@dataclass
class QueensState:
    """Full state of a Queens puzzle extracted from the DOM.

    Attributes:
        grid_size: Side length of the board (N×N).
        colors: 2-D list ``colors[row][col]`` giving the integer color-region
            index (0-based) of each cell.  There are exactly ``grid_size``
            distinct colors, one queen per color region.
        prefilled: 2-D bool list — ``True`` where a queen is already placed
            in the initial puzzle state (pre-filled by LinkedIn).
    """

    grid_size: int
    colors: list[list[int]]
    prefilled: list[list[bool]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_state(page: Page) -> QueensState:
    """Extract the full Queens puzzle state from the live DOM.

    Waits for the board to fully render, then runs a single JS evaluation to
    collect cell color regions and any pre-placed queens.

    Args:
        page: Playwright ``Page`` pointing to the LinkedIn Queens tab.

    Returns:
        A ``QueensState`` dataclass with color map and pre-placed queens.

    Raises:
        SystemExit: If extraction fails (board not loaded or unexpected DOM).
    """
    _wait_for_board(page)

    js = r"""
    (() => {
        // ── locate cells ──
        // LinkedIn uses data-cell-idx on individual cell divs inside the grid.
        // The color region is stored either as:
        //   • data-cell-color="0" … "N-1"
        //   • a CSS class like "queens-cell-color-0"
        //   • an inline background-color / CSS variable
        // We try all approaches and return diagnostic info so Python can adapt.

        const cells = Array.from(document.querySelectorAll('[data-cell-idx]'));
        if (cells.length === 0) return { error: 'no [data-cell-idx] cells found' };

        const nCells = cells.length;
        const gridSize = Math.round(Math.sqrt(nCells));
        if (gridSize * gridSize !== nCells) {
            return { error: `cell count ${nCells} is not a perfect square` };
        }

        // Sort by idx
        cells.sort((a, b) => parseInt(a.dataset.cellIdx) - parseInt(b.dataset.cellIdx));

        const cellData = cells.map(cell => {
            const idx = parseInt(cell.dataset.cellIdx);
            const row = Math.floor(idx / gridSize);
            const col = idx % gridSize;

            // ── color detection ──────────────────────────────────────
            // Strategy 1: data-cell-color attribute
            let colorId = cell.dataset.cellColor ?? null;

            // Strategy 2: class like "queens-cell-color-3"
            if (colorId === null) {
                const colorClass = Array.from(cell.classList)
                    .find(c => /color/i.test(c));
                if (colorClass) {
                    const m = colorClass.match(/(\d+)$/);
                    if (m) colorId = m[1];
                }
            }

            // Strategy 3: look inside child elements for color class
            if (colorId === null) {
                const inner = cell.querySelector('[class*="color"]');
                if (inner) {
                    const colorClass = Array.from(inner.classList)
                        .find(c => /color/i.test(c));
                    if (colorClass) {
                        const m = colorClass.match(/(\d+)$/);
                        if (m) colorId = m[1];
                    }
                }
            }

            // Strategy 4: background-color inline style → map to index later
            let bgColor = null;
            if (colorId === null) {
                const style = cell.getAttribute('style') || '';
                // look for background-color or a CSS variable
                const bgMatch = style.match(/background(?:-color)?:\s*([^;]+)/);
                bgColor = bgMatch ? bgMatch[1].trim() : null;

                // Also check computed style
                if (!bgColor) {
                    const computed = window.getComputedStyle(cell).backgroundColor;
                    if (computed && computed !== 'rgba(0, 0, 0, 0)' && computed !== 'transparent') {
                        bgColor = computed;
                    }
                }
            }

            // ── queen detection ──────────────────────────────────────
            const label = cell.getAttribute('aria-label') || '';
            const hasQueenByLabel = /queen/i.test(label);
            const hasQueenByClass = Array.from(cell.classList).some(c => /queen/i.test(c))
                || !!cell.querySelector('[class*="queen"]');

            // ── full class list for debugging ──
            const classList = Array.from(cell.classList).join(' ');
            const innerHtml = cell.innerHTML.substring(0, 200);

            return {
                idx, row, col,
                colorId,
                bgColor,
                hasQueen: hasQueenByLabel || hasQueenByClass,
                label,
                classList,
                innerHtml,
            };
        });

        return { gridSize, nCells, cellData };
    })()
    """

    result = page.evaluate(js)

    if result is None:
        logger.error("JS evaluation returned null — board may not be loaded.")
        raise SystemExit(1)

    if "error" in result:
        logger.error("Failed to extract Queens state: %s", result["error"])
        raise SystemExit(1)

    grid_size: int = result["gridSize"]
    cell_data: list[dict] = result["cellData"]

    logger.debug("Raw extraction: grid_size=%d, cells=%d", grid_size, result["nCells"])

    # ── Build color map ──────────────────────────────────────────────────────
    # First try: data-cell-color (integer strings)
    colors_raw = [cd["colorId"] for cd in cell_data]

    if any(c is None for c in colors_raw):
        # Fall back to bgColor mapping
        logger.debug("color ids missing — falling back to background-color mapping")
        bg_colors = [cd["bgColor"] for cd in cell_data]
        unique_bgs = list(dict.fromkeys(b for b in bg_colors if b))
        color_index_map = {bg: i for i, bg in enumerate(unique_bgs)}
        colors_raw = [str(color_index_map.get(cd["bgColor"], -1)) for cd in cell_data]

    # Validate we got something useful
    unique_colors = set(c for c in colors_raw if c is not None)
    if not unique_colors or "-1" in unique_colors and len(unique_colors) == 1:
        # Last resort: log debug info and bail
        logger.error(
            "Could not determine color regions. Sample cell[0]: classList=%r innerHtml=%r",
            cell_data[0]["classList"] if cell_data else "?",
            cell_data[0]["innerHtml"] if cell_data else "?",
        )
        raise SystemExit(1)

    # Build 2-D grids
    colors: list[list[int]] = [[0] * grid_size for _ in range(grid_size)]
    prefilled: list[list[bool]] = [[False] * grid_size for _ in range(grid_size)]

    for cd in cell_data:
        r, c = cd["row"], cd["col"]
        colors[r][c] = int(colors_raw[cell_data.index(cd)])
        prefilled[r][c] = cd["hasQueen"]

    n_colors = len(set(colors[r][c] for r in range(grid_size) for c in range(grid_size)))
    logger.debug("Extracted %d color regions, grid %dx%d", n_colors, grid_size, grid_size)

    pre_count = sum(prefilled[r][c] for r in range(grid_size) for c in range(grid_size))
    if pre_count:
        logger.info("Pre-placed queens: %d", pre_count)

    return QueensState(grid_size=grid_size, colors=colors, prefilled=prefilled)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _wait_for_board(page: Page) -> None:
    """Wait until the Queens grid is fully rendered in the DOM.

    Polls until ``[data-cell-idx]`` cells are present and their count is a
    perfect square ≥ 4, then additionally waits for color information to appear
    on at least one cell.

    Args:
        page: Playwright ``Page`` to poll.

    Raises:
        SystemExit: If the board does not fully render within the timeout.
    """
    poll_interval = 0.5
    max_attempts = int(LOAD_TIMEOUT_MS / 1000 / poll_interval) + 1

    logger.debug("Waiting for Queens board to render (up to %ds) …", LOAD_TIMEOUT_MS // 1000)

    # Phase 1: wait for any cell element
    try:
        page.wait_for_selector("[data-cell-idx]", timeout=LOAD_TIMEOUT_MS)
        logger.debug("Queens cells detected in DOM")
    except Exception:
        logger.error(
            "No [data-cell-idx] cells appeared within %ds. Make sure the Queens game page is open.",
            LOAD_TIMEOUT_MS // 1000,
        )
        raise SystemExit(1) from None

    # Phase 2: wait for a perfect-square count and some color info
    cell_count = 0
    for attempt in range(1, max_attempts + 1):
        result = page.evaluate(r"""
        (() => {
            const cells = document.querySelectorAll('[data-cell-idx]');
            const n = cells.length;
            const gs = Math.round(Math.sqrt(n));
            const isPerfect = gs * gs === n && n >= 4;

            // check color presence
            let hasColor = false;
            for (const cell of cells) {
                if (cell.dataset.cellColor !== undefined) { hasColor = true; break; }
                if (Array.from(cell.classList).some(c => /color/i.test(c))) { hasColor = true; break; }
                const inner = cell.querySelector('[class*="color"]');
                if (inner) { hasColor = true; break; }
                const bg = window.getComputedStyle(cell).backgroundColor;
                if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') {
                    hasColor = true; break;
                }
            }
            return { n, isPerfect, hasColor };
        })()
        """)

        cell_count = result["n"]
        if result["isPerfect"] and result["hasColor"]:
            grid_size = round(cell_count**0.5)
            logger.debug(
                "Board ready: %d cells (%dx%d), color info present (attempt %d)",
                cell_count,
                grid_size,
                grid_size,
                attempt,
            )
            return

        logger.debug(
            "Waiting … cells=%d  perfect=%s  hasColor=%s  (attempt %d/%d)",
            cell_count,
            result["isPerfect"],
            result["hasColor"],
            attempt,
            max_attempts,
        )
        time.sleep(poll_interval)

    logger.error("Queens board did not fully render in time (found %d cells).", cell_count)
    raise SystemExit(1)
