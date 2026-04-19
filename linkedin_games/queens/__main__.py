"""
Entry point for the Queens solver.

    python -m linkedin_games.queens
    # or, after installing:
    queens
"""

from __future__ import annotations

import logging

from linkedin_games._logging import setup_logging
from linkedin_games.browser import connect_to_chrome, find_tab
from linkedin_games.config import CDP_URL
from linkedin_games.queens.extractor import extract_state
from linkedin_games.queens.player import play_solution
from linkedin_games.queens.solver import format_solution, solve, validate_solution

logger = logging.getLogger(__name__)

GAME_URL_FRAGMENT = "linkedin.com/games/queens"


def main() -> None:
    """Run the end-to-end Queens solver pipeline.

    Connects to Chrome, opens the Queens game tab, extracts the board
    (color regions + pre-placed queens), solves it, validates the solution,
    then plays it back by clicking each queen position in the browser.

    Raises:
        SystemExit: With code ``1`` if extraction fails, no solution is found,
            the solver produces an invalid solution, or the browser connection fails.
    """
    setup_logging()
    logger.info("Connecting to Chrome at %s", CDP_URL)

    with connect_to_chrome() as browser:
        page = find_tab(browser, GAME_URL_FRAGMENT)
        logger.info("Found tab: %s", page.url)

        # ── Step 1: Extract ──────────────────────────────────────────
        logger.info("Extracting Queens state from the DOM …")
        state = extract_state(page)

        logger.info(
            "Board: %dx%d, %d color regions",
            state.grid_size,
            state.grid_size,
            len(
                set(
                    state.colors[r][c]
                    for r in range(state.grid_size)
                    for c in range(state.grid_size)
                )
            ),
        )

        pre_count = sum(
            state.prefilled[r][c] for r in range(state.grid_size) for c in range(state.grid_size)
        )
        if pre_count:
            logger.info("Pre-placed queens: %d", pre_count)

        # ── Step 2: Solve ────────────────────────────────────────────
        logger.info("Solving …")
        solution = solve(state)

        if solution is None:
            logger.error("No solution found.")
            raise SystemExit(1)

        if not validate_solution(solution, state.colors):
            logger.error("Solver produced an invalid solution!")
            raise SystemExit(1)

        logger.info("Solution:\n%s", format_solution(solution, state.colors))

        # ── Step 3: Play ─────────────────────────────────────────────
        play_solution(page, state, solution)

    logger.info("Done! Check the browser to see the result.")


if __name__ == "__main__":
    main()
