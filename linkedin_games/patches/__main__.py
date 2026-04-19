"""
Entry point for the Patches solver.

    python -m linkedin_games.patches
    # or, after installing:
    patches
"""

from __future__ import annotations

import logging

from linkedin_games._logging import setup_logging
from linkedin_games.browser import connect_to_chrome, find_tab
from linkedin_games.config import CDP_URL
from linkedin_games.patches.extractor import extract_state
from linkedin_games.patches.player import play_solution
from linkedin_games.patches.solver import format_solution, solve, validate_solution

logger = logging.getLogger(__name__)

GAME_URL_FRAGMENT = "linkedin.com/games/patches"


def main() -> None:
    """Run the end-to-end Patches solver pipeline.

    Connects to Chrome, opens the Patches game tab, extracts the puzzle state
    (clues + any pre-drawn regions), solves it, validates the solution, then
    plays it back by simulating mouse drags in the browser.

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
        logger.info("Extracting Patches state from the DOM …")
        state = extract_state(page)

        logger.info("Found %d clues", len(state.clues))
        for i, clue in enumerate(state.clues):
            size_str = f", size={clue.size}" if clue.size else ""
            logger.debug(
                "[%d] (%d,%d)  %s%s  color=%s",
                i, clue.row + 1, clue.col + 1, clue.shape.value, size_str, clue.color,
            )

        if state.predrawn:
            logger.info("Pre-drawn regions: %d", len(state.predrawn))
            for cells, clue_idx in state.predrawn:
                logger.debug("  Clue %d: %s", clue_idx, sorted(cells))

        # ── Step 2: Solve ────────────────────────────────────────────
        logger.info("Solving …")
        solution = solve(state)

        if solution is None:
            logger.error("No solution found.")
            raise SystemExit(1)

        if not validate_solution(state.clues, solution):
            logger.error("Solver produced an invalid solution!")
            raise SystemExit(1)

        logger.info("Solved board:\n%s", format_solution(state.clues, solution))

        for i, rect in enumerate(solution):
            logger.debug(
                "Patch %d: (%d,%d)→(%d,%d)  %d×%d = %d cells",
                i, rect.r1 + 1, rect.c1 + 1, rect.r2 + 1, rect.c2 + 1,
                rect.width, rect.height, rect.area,
            )

        # ── Step 3: Play ─────────────────────────────────────────────
        predrawn_indices = {clue_idx for _, clue_idx in state.predrawn}
        play_solution(page, state.clues, solution, predrawn_indices)

    logger.info("Done! Check the browser to see the result.")


if __name__ == "__main__":
    main()
