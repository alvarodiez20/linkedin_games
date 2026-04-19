"""
DOM → grid state extraction for LinkedIn Mini Sudoku.

The game lives inside an **iframe** (src contains "/preload/").
Inside that iframe:
  - Board container: ``section.sudoku-board``
  - Grid:           ``div.sudoku-grid`` with 36 child divs
  - Each cell:      ``div.sudoku-cell[data-cell-idx="0..35"]``
  - Cell value:     ``div.sudoku-cell-content`` (text is digit or empty)
  - Pre-filled:     cell has class ``sudoku-cell-prefilled``

Public API: ``extract_grid(page) -> list[list[int]]``
"""

from __future__ import annotations

import logging
import time

from playwright.sync_api import Frame, Page

logger = logging.getLogger(__name__)

GRID_SIZE = 6
GAME_URL_FRAGMENT = "linkedin.com/games/mini-sudoku"
LOAD_TIMEOUT_MS = 15_000


def extract_grid(page: Page) -> list[list[int]]:
    """Return the current 6×6 Sudoku grid as a 2-D list of ints.

    Locates the game iframe, waits for the board to render, then reads
    only the pre-filled cells — leaving empty cells as ``0``.

    Args:
        page: Playwright ``Page`` object pointing to the LinkedIn Sudoku tab.

    Returns:
        A ``6×6`` ``list[list[int]]`` where ``0`` represents an empty cell
        and ``1``–``6`` represent given clue values.

    Raises:
        SystemExit: If the extracted grid fails sanity validation.
    """
    frame = _get_game_frame(page)
    _wait_for_board(frame)

    grid = _extract(frame)

    if not _is_valid_initial_grid(grid):
        logger.error(
            "Extracted grid failed validation: %s  Make sure the game is fully loaded.",
            grid,
        )
        raise SystemExit(1)

    logger.debug("Extracted grid: %s", grid)
    return grid


def get_game_frame(page: Page) -> Frame:
    """Return the iframe ``Frame`` that contains the Sudoku game.

    Public so that ``player.py`` can reuse it without re-searching frames.

    Args:
        page: Playwright ``Page`` object pointing to the LinkedIn Sudoku tab.

    Returns:
        The ``playwright.sync_api.Frame`` hosting the Sudoku DOM.

    Raises:
        SystemExit: If no game frame is found.
    """
    return _get_game_frame(page)


def _get_game_frame(page: Page) -> Frame:
    """Find the iframe that contains the Sudoku game DOM.

    LinkedIn renders the game inside an iframe whose src contains "/preload/".
    Two strategies are attempted in sequence:

    1. Scan all frames for a ``.sudoku-board`` element.
    2. Find the frame whose URL contains ``"/preload/"`` and has ``.sudoku-cell``
       elements.

    Args:
        page: Playwright ``Page`` to search.

    Returns:
        The game ``Frame``.

    Raises:
        SystemExit: If neither strategy locates the iframe.
    """
    page.wait_for_load_state("domcontentloaded")

    for frame in page.frames:
        try:
            count = frame.evaluate("document.querySelectorAll('.sudoku-board').length")
            if count > 0:
                logger.debug("Found game frame via .sudoku-board (url=%s)", frame.url)
                return frame
        except Exception:
            continue

    for frame in page.frames:
        if "/preload/" in (frame.url or ""):
            try:
                count = frame.evaluate("document.querySelectorAll('.sudoku-cell').length")
                if count > 0:
                    logger.debug("Found game frame via /preload/ url (url=%s)", frame.url)
                    return frame
            except Exception:
                continue

    frame_urls = "\n".join(f"  • {f.url}" for f in page.frames)
    logger.error("Could not find the game iframe. Available frames:\n%s", frame_urls)
    raise SystemExit(1)


def _wait_for_board(frame: Frame) -> None:
    """Wait until the Sudoku grid cells are rendered in the DOM.

    First tries Playwright's ``wait_for_selector``.  If that times out, falls
    back to a 3-second sleep and a manual count check.

    Args:
        frame: The game ``Frame`` to poll.

    Raises:
        SystemExit: If the board does not contain the expected 36 cells.
    """
    try:
        frame.wait_for_selector(".sudoku-cell", timeout=LOAD_TIMEOUT_MS)
        logger.debug("Board ready (wait_for_selector succeeded)")
    except Exception:
        logger.warning("wait_for_selector timed out — falling back to sleep poll")
        time.sleep(3)
        count = frame.evaluate("document.querySelectorAll('.sudoku-cell').length")
        if count < GRID_SIZE * GRID_SIZE:
            logger.error(
                "Board did not load in time (found %d cells, need %d).",
                count,
                GRID_SIZE * GRID_SIZE,
            )
            raise SystemExit(1) from None


def _extract(frame: Frame) -> list[list[int]]:
    """Pull the 36 cell values from the iframe DOM and reshape into 6×6.

    Only reads values from **pre-filled** cells (``sudoku-cell-prefilled``).
    User-entered values are ignored so the solver always receives the original
    puzzle state.

    Args:
        frame: The game ``Frame`` containing the Sudoku DOM.

    Returns:
        A flat list of 36 ints reshaped into a ``6×6`` grid.

    Raises:
        SystemExit: If the JS evaluation returns an unexpected result.
    """
    js = """
    (() => {
        const cells = document.querySelectorAll('.sudoku-cell[data-cell-idx]');
        if (cells.length !== 36) return null;

        const sorted = Array.from(cells).sort(
            (a, b) => parseInt(a.dataset.cellIdx) - parseInt(b.dataset.cellIdx)
        );

        return sorted.map(cell => {
            const isPrefilled = cell.classList.contains('sudoku-cell-prefilled');
            if (!isPrefilled) return 0;

            const content = cell.querySelector('.sudoku-cell-content');
            if (!content) return 0;
            const text = content.textContent.trim();
            const num = parseInt(text, 10);
            return (num >= 1 && num <= 6) ? num : 0;
        });
    })()
    """
    flat = frame.evaluate(js)

    if flat is None or len(flat) != GRID_SIZE * GRID_SIZE:
        logger.error("Failed to extract cell values (got %s).", flat)
        raise SystemExit(1)

    return [flat[r * GRID_SIZE : (r + 1) * GRID_SIZE] for r in range(GRID_SIZE)]


def _is_valid_initial_grid(grid: list[list[int]]) -> bool:
    """Sanity-check a freshly extracted grid.

    Verifies that the grid is 6×6, all values are in ``[0, 6]``, and at least
    6 cells carry a non-zero (pre-filled) value.

    Args:
        grid: The 6×6 grid to validate.

    Returns:
        ``True`` if the grid looks like a valid initial Sudoku puzzle.
    """
    if len(grid) != GRID_SIZE:
        return False
    if any(len(row) != GRID_SIZE for row in grid):
        return False
    flat = [v for row in grid for v in row]
    if not all(0 <= v <= 6 for v in flat):
        return False
    if sum(1 for v in flat if v > 0) < 6:
        return False
    return True
