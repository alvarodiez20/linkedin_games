"""
Entry point for the Sudoku solver.

    python -m linkedin_games.sudoku
    # or, after installing:
    sudoku
"""

from __future__ import annotations

import logging

from linkedin_games._logging import setup_logging
from linkedin_games.browser import connect_to_chrome, find_tab
from linkedin_games.config import CDP_URL
from linkedin_games.sudoku.extractor import extract_grid
from linkedin_games.sudoku.player import play_solution
from linkedin_games.sudoku.solver import format_board, solve, validate_solution

logger = logging.getLogger(__name__)

GAME_URL_FRAGMENT = "linkedin.com/games/mini-sudoku"


def main() -> None:
    """Run the end-to-end Sudoku solver pipeline.

    Connects to Chrome, opens the Sudoku game tab, extracts the puzzle,
    solves it, validates the solution, then plays it back into the browser.

    Raises:
        SystemExit: With code ``1`` if no solution is found, if the solver
            produces an invalid solution, or if the browser connection fails.
    """
    setup_logging()
    logger.info("Connecting to Chrome at %s", CDP_URL)

    with connect_to_chrome() as browser:
        page = find_tab(browser, GAME_URL_FRAGMENT)
        logger.info("Found tab: %s", page.url)

        # ── Step 1: Extract ──────────────────────────────────────────
        logger.info("Extracting grid from the DOM …")
        original = extract_grid(page)
        logger.info("Initial board:\n%s", format_board(original))

        # ── Step 2: Solve ────────────────────────────────────────────
        logger.info("Solving …")
        solved = solve(original)

        if solved is None:
            logger.error("No solution found — the extracted grid may be wrong.")
            raise SystemExit(1)

        if not validate_solution(solved):
            logger.error("Solver produced an invalid solution!")
            raise SystemExit(1)

        logger.info("Solved board:\n%s", format_board(solved))

        # ── Step 3: Play ─────────────────────────────────────────────
        play_solution(page, original, solved)

    logger.info("Done! Check the browser to see the result.")


if __name__ == "__main__":
    main()
