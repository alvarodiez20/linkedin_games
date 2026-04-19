"""
Entry point for the Patches solver.

    python -m linkedin_games.patches
"""

from __future__ import annotations

import sys

from linkedin_games.browser import connect_to_chrome, find_tab
from linkedin_games.patches.extractor import extract_state
from linkedin_games.patches.solver import print_solution, solve, validate_solution
from linkedin_games.patches.player import play_solution

GAME_URL_FRAGMENT = "linkedin.com/games/patches"


def main() -> None:
    print("🔗  Connecting to Chrome on localhost:9222 …")

    with connect_to_chrome() as browser:
        page = find_tab(browser, GAME_URL_FRAGMENT)
        print(f"📄  Found tab: {page.url}\n")

        # ── Step 1: Extract ──────────────────────────────────────────
        print("🔍  Extracting Patches state from the DOM …")
        state = extract_state(page)

        print(f"\n📌  Found {len(state.clues)} clues:")
        for i, clue in enumerate(state.clues):
            size_str = f", size={clue.size}" if clue.size else ""
            print(
                f"     [{i}] ({clue.row+1},{clue.col+1})  "
                f"{clue.shape.value}{size_str}  "
                f"color={clue.color}"
            )

        if state.predrawn:
            print(f"\n🎨  Pre-drawn regions: {len(state.predrawn)}")
            for cells, clue_idx in state.predrawn:
                print(f"     Clue {clue_idx}: {sorted(cells)}")

        # ── Step 2: Solve ────────────────────────────────────────────
        print("\n🧠  Solving …")
        solution = solve(state)

        if solution is None:
            print("❌  No solution found.", file=sys.stderr)
            raise SystemExit(1)

        if not validate_solution(state.clues, solution):
            print("❌  Solver produced an invalid solution!", file=sys.stderr)
            raise SystemExit(1)

        print("\n✅  Solved board:")
        print_solution(state.clues, solution)

        for i, rect in enumerate(solution):
            clue = state.clues[i]
            print(
                f"     Patch {i}: ({rect.r1+1},{rect.c1+1})→({rect.r2+1},{rect.c2+1})  "
                f"{rect.width}×{rect.height} = {rect.area} cells"
            )

        # ── Step 3: Play ─────────────────────────────────────────────
        predrawn_indices = {clue_idx for _, clue_idx in state.predrawn}
        play_solution(page, state.clues, solution, predrawn_indices)

    print("\n🎉  Done! Check the browser to see the result.")


if __name__ == "__main__":
    main()
