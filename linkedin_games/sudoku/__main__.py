"""
Entry point for the Sudoku solver.

    python -m linkedin_games.sudoku
    # or, after installing:
    sudoku
"""

from __future__ import annotations

import sys

from linkedin_games.browser import connect_to_chrome, find_tab
from linkedin_games.sudoku.extractor import extract_grid
from linkedin_games.sudoku.solver import print_board, solve, validate_solution
from linkedin_games.sudoku.player import play_solution


GAME_URL_FRAGMENT = "linkedin.com/games/mini-sudoku"


def main() -> None:
    print("🔗  Connecting to Chrome on localhost:9222 …")

    with connect_to_chrome() as browser:
        page = find_tab(browser, GAME_URL_FRAGMENT)
        print(f"📄  Found tab: {page.url}\n")

        # ── Step 1: Extract ──────────────────────────────────────────
        print("🔍  Extracting grid from the DOM …")
        original = extract_grid(page)

        print("\n📋  Initial board:")
        print_board(original)

        # ── Step 2: Solve ────────────────────────────────────────────
        print("\n🧠  Solving …")
        solved = solve(original)

        if solved is None:
            print("❌  No solution found — the extracted grid may be wrong.", file=sys.stderr)
            raise SystemExit(1)

        if not validate_solution(solved):
            print("❌  Solver produced an invalid solution!", file=sys.stderr)
            raise SystemExit(1)

        print("\n✅  Solved board:")
        print_board(solved)

        # ── Step 3: Play ─────────────────────────────────────────────
        play_solution(page, original, solved)

    print("\n🎉  Done! Check the browser to see the result.")


if __name__ == "__main__":
    main()
