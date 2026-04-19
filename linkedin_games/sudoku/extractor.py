"""
DOM → grid state extraction for LinkedIn Mini Sudoku.

The game lives inside an **iframe** (src contains "/preload/").
Inside that iframe:
  - Board container: ``section.sudoku-board``
  - Grid:           ``div.sudoku-grid`` with 36 child divs
  - Each cell:      ``div.sudoku-cell[data-cell-idx="0..35"]``
  - Cell value:     ``div.sudoku-cell-content`` (text is digit or empty)
  - Pre-filled:     cell has class ``sudoku-cell-prefilled``

The public API is ``extract_grid(page) -> list[list[int]]`` which returns
a 6×6 matrix where 0 means "empty".
"""

from __future__ import annotations

import sys
import time

from playwright.sync_api import Frame, Page

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
GRID_SIZE = 6
GAME_URL_FRAGMENT = "linkedin.com/games/mini-sudoku"
LOAD_TIMEOUT_MS = 15_000


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_grid(page: Page) -> list[list[int]]:
    """
    Return the current 6×6 Sudoku grid as a 2-D list of ints (0 = empty).
    """
    frame = _get_game_frame(page)
    _wait_for_board(frame)

    grid = _extract(frame)

    if not _is_valid_initial_grid(grid):
        print(
            "\n❌  Extracted grid failed validation.\n"
            "    Grid: %s\n"
            "    Make sure the game is fully loaded.\n" % grid,
            file=sys.stderr,
        )
        raise SystemExit(1)

    return grid


def get_game_frame(page: Page) -> Frame:
    """
    Return the iframe ``Frame`` that contains the Sudoku game.
    Public so that ``player.py`` can reuse it.
    """
    return _get_game_frame(page)


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _get_game_frame(page: Page) -> Frame:
    """
    Find the iframe that contains the Sudoku game DOM.

    LinkedIn renders the game inside an iframe whose src contains "/preload/"
    or whose document contains ``.sudoku-board``.
    """
    # Give the page a moment to settle if needed
    page.wait_for_load_state("domcontentloaded")

    # Strategy 1: check all frames for .sudoku-board
    for frame in page.frames:
        try:
            count = frame.evaluate(
                "document.querySelectorAll('.sudoku-board').length"
            )
            if count > 0:
                return frame
        except Exception:
            continue

    # Strategy 2: find iframe with "/preload/" src and check contents
    for frame in page.frames:
        if "/preload/" in (frame.url or ""):
            try:
                count = frame.evaluate(
                    "document.querySelectorAll('.sudoku-cell').length"
                )
                if count > 0:
                    return frame
            except Exception:
                continue

    print(
        "\n❌  Could not find the game iframe.\n"
        "    Available frames:\n%s\n"
        % "\n".join(f"      • {f.url}" for f in page.frames),
        file=sys.stderr,
    )
    raise SystemExit(1)


def _wait_for_board(frame: Frame) -> None:
    """Wait until the Sudoku grid cells are rendered."""
    try:
        frame.wait_for_selector(".sudoku-cell", timeout=LOAD_TIMEOUT_MS)
    except Exception:
        # Fallback: brute-force wait
        time.sleep(3)
        count = frame.evaluate(
            "document.querySelectorAll('.sudoku-cell').length"
        )
        if count < GRID_SIZE * GRID_SIZE:
            print(
                "\n❌  Board did not load in time (found %d cells, need %d).\n"
                % (count, GRID_SIZE * GRID_SIZE),
                file=sys.stderr,
            )
            raise SystemExit(1)


def _extract(frame: Frame) -> list[list[int]]:
    """
    Pull the 36 cell values from the iframe DOM and reshape into 6×6.

    Only reads values from **pre-filled** cells (class ``sudoku-cell-prefilled``).
    User-entered values are ignored so the solver always gets the original puzzle.
    """
    js = """
    (() => {
        const cells = document.querySelectorAll('.sudoku-cell[data-cell-idx]');
        if (cells.length !== 36) return null;

        // Sort by data-cell-idx to guarantee order
        const sorted = Array.from(cells).sort(
            (a, b) => parseInt(a.dataset.cellIdx) - parseInt(b.dataset.cellIdx)
        );

        return sorted.map(cell => {
            // Only read pre-filled cells (ignore user-entered values)
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
        print(
            "\n❌  Failed to extract cell values (got %s).\n" % flat,
            file=sys.stderr,
        )
        raise SystemExit(1)

    # Reshape flat list into 6×6 grid
    return [flat[r * GRID_SIZE : (r + 1) * GRID_SIZE] for r in range(GRID_SIZE)]


def _is_valid_initial_grid(grid: list[list[int]]) -> bool:
    """
    Sanity-check: must be 6×6, values in [0..6], and not completely empty.
    """
    if len(grid) != GRID_SIZE:
        return False
    if any(len(row) != GRID_SIZE for row in grid):
        return False
    flat = [v for row in grid for v in row]
    if not all(0 <= v <= 6 for v in flat):
        return False
    # There should be at least a few given numbers
    if sum(1 for v in flat if v > 0) < 6:
        return False
    return True
