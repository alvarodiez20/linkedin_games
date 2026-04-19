"""
Entry point for the Zip solver.

    python -m linkedin_games.zip
    # or, after installing:
    zip-game
"""

from __future__ import annotations

import logging

from linkedin_games._logging import setup_logging
from linkedin_games.browser import connect_to_chrome, find_tab
from linkedin_games.config import CDP_URL
from linkedin_games.zip.extractor import extract_state
from linkedin_games.zip.player import play_solution
from linkedin_games.zip.solver import format_path, solve, validate_path

logger = logging.getLogger(__name__)

GAME_URL_FRAGMENT = "linkedin.com/games/zip"


def main() -> None:
    """Run the end-to-end Zip solver pipeline.

    Connects to Chrome, opens the Zip game tab, extracts the puzzle state
    (grid + walls + waypoints), finds a Hamiltonian path that visits all cells
    in waypoint order, validates it, then draws the path in the browser via a
    simulated mouse drag.

    Raises:
        SystemExit: With code ``1`` if extraction fails, no solution is found,
            the validator rejects the solution, or the browser connection fails.
    """
    setup_logging()
    logger.info("Connecting to Chrome at %s", CDP_URL)

    with connect_to_chrome() as browser:
        page = find_tab(browser, GAME_URL_FRAGMENT)
        logger.info("Found tab: %s", page.url)

        # ── Step 1: Extract ──────────────────────────────────────────
        logger.info("Extracting Zip state from the DOM …")
        state = extract_state(page)

        logger.info(
            "Board: %dx%d  walls=%d  waypoints=%d  passable_cells=%d",
            state.grid_size,
            state.grid_size,
            len(state.walls),
            len(state.waypoints),
            len(state.passable),
        )
        logger.debug("Waypoints: %s", sorted(state.waypoints.items()))
        logger.debug("Walls: %s", sorted(state.walls))

        # ── Step 2: Solve ────────────────────────────────────────────
        logger.info("Solving …")
        path = solve(state)

        if path is None:
            logger.error("No solution found.")
            raise SystemExit(1)

        if not validate_path(path, state):
            logger.error("Solver produced an invalid path!")
            raise SystemExit(1)

        logger.info("Solution found (%d cells):\n%s", len(path), format_path(path, state))

        # ── Step 3: Play ─────────────────────────────────────────────
        play_solution(page, state, path)

    logger.info("Done! Check the browser to see the result.")


if __name__ == "__main__":
    main()
