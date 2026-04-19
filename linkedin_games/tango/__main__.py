"""
Entry point for the Tango solver.

    python -m linkedin_games.tango
"""

from __future__ import annotations

import sys

from linkedin_games.browser import connect_to_chrome, find_tab
from linkedin_games.tango.extractor import extract_state, SUN, MOON, EMPTY
from linkedin_games.tango.solver import print_board, solve, validate_solution
from linkedin_games.tango.player import play_solution

GAME_URL_FRAGMENT = "linkedin.com/games/tango"


def main() -> None:
    print("🔗  Connecting to Chrome on localhost:9222 …")

    with connect_to_chrome() as browser:
        page = find_tab(browser, GAME_URL_FRAGMENT)
        print(f"📄  Found tab: {page.url}\n")

        # ── Step 1: Extract ──────────────────────────────────────────
        print("🔍  Extracting Tango state from the DOM …")
        state = extract_state(page)

        print("\n📋  Initial board:")
        print_board(state.grid)

        sym = {EMPTY: "·", SUN: "☀", MOON: "☽"}
        print(f"\n📌  Pre-filled: {sum(pf for row in state.prefilled for pf in row)} cells")
        print(f"🔗  Constraints: {len(state.constraints)}")
        for (r1, c1), (r2, c2), ctype in state.constraints:
            print(f"     ({r1+1},{c1+1}) {'=' if ctype == 'equal' else '×'} ({r2+1},{c2+1})")

        # ── Step 2: Solve ────────────────────────────────────────────
        print("\n🧠  Solving …")
        solved = solve(state.grid, state.constraints)

        if solved is None:
            print("❌  No solution found.", file=sys.stderr)
            raise SystemExit(1)

        if not validate_solution(solved, state.constraints):
            print("❌  Solver produced an invalid solution!", file=sys.stderr)
            raise SystemExit(1)

        print("\n✅  Solved board:")
        print_board(solved)

        # ── Step 3: Play ─────────────────────────────────────────────
        play_solution(page, state.grid, state.prefilled, solved)

    print("\n🎉  Done! Check the browser to see the result.")


if __name__ == "__main__":
    main()
