"""
Entry point for the Tango solver.

    python -m linkedin_games.tango
    # or, after installing:
    tango
"""

from __future__ import annotations

import logging

from linkedin_games._logging import setup_logging
from linkedin_games.browser import connect_to_chrome, find_tab
from linkedin_games.config import CDP_URL
from linkedin_games.tango.extractor import extract_state
from linkedin_games.tango.player import play_solution
from linkedin_games.tango.solver import format_board, solve, validate_solution

logger = logging.getLogger(__name__)

GAME_URL_FRAGMENT = "linkedin.com/games/tango"


def main() -> None:
    """Run the end-to-end Tango solver pipeline.

    Connects to Chrome, opens the Tango game tab, extracts the puzzle state
    (grid + edge constraints), solves it, validates the solution, then plays
    it back into the browser.

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
        logger.info("Extracting Tango state from the DOM …")
        state = extract_state(page)

        logger.info("Initial board:\n%s", format_board(state.grid))

        filled = sum(pf for row in state.prefilled for pf in row)
        logger.info("Pre-filled: %d cells", filled)
        logger.info("Edge constraints: %d", len(state.constraints))
        for (r1, c1), (r2, c2), ctype in state.constraints:
            logger.debug(
                "  (%d,%d) %s (%d,%d)",
                r1 + 1,
                c1 + 1,
                "=" if ctype == "equal" else "×",
                r2 + 1,
                c2 + 1,
            )

        # ── Step 2: Solve ────────────────────────────────────────────
        logger.info("Solving …")
        solved = solve(state.grid, state.constraints)

        if solved is None:
            logger.error("No solution found.")
            raise SystemExit(1)

        if not validate_solution(solved, state.constraints):
            logger.error("Solver produced an invalid solution!")
            raise SystemExit(1)

        logger.info("Solved board:\n%s", format_board(solved))

        # ── Step 3: Play ─────────────────────────────────────────────
        play_solution(page, state.grid, state.prefilled, solved)

    logger.info("Done! Check the browser to see the result.")


if __name__ == "__main__":
    main()
