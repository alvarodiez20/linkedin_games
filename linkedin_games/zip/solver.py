"""
Hamiltonian-path solver for LinkedIn Zip.

Rules:
  1. Draw a single continuous path through the N×N grid.
  2. The path must visit **every non-wall cell** exactly once.
  3. Numbered cells must be visited in ascending order (1, 2, 3, …).
  4. Adjacent means orthogonally neighbouring (no diagonals).

Algorithm — DFS with ordered-waypoint constraint + Warnsdorff ordering:
  - Start from waypoint 1.
  - At each step, try orthogonal neighbours that are unvisited.
  - Skip any neighbour that is a waypoint *not* equal to the next required one.
  - Order candidates by their available-neighbour count (fewest first —
    Warnsdorff's heuristic) to minimise dead-ends.
  - Periodically check global connectivity of unvisited cells; prune if a
    region becomes unreachable.
"""

from __future__ import annotations

import logging
from collections import deque

from linkedin_games.zip.extractor import ZipState

logger = logging.getLogger(__name__)


def solve(state: ZipState) -> list[int] | None:
    """Solve the Zip puzzle.

    Args:
        state: Extracted puzzle state.

    Returns:
        An ordered list of cell indices representing the full path (from
        waypoint 1 to waypoint *max*), or ``None`` if unsolvable.
    """
    n = state.grid_size
    walls = state.walls
    passable = state.passable
    total = len(passable)
    wp_by_num = state.waypoints  # number → cell_idx
    wp_by_cell = {v: k for k, v in wp_by_num.items()}  # cell_idx → number
    max_wp = state.max_waypoint

    if max_wp not in wp_by_num:
        logger.error("No waypoints found — cannot solve.")
        return None

    # Precompute adjacency for all passable cells
    def _neighbors(idx: int) -> list[int]:
        r, c = divmod(idx, n)
        result = []
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n:
                ni = nr * n + nc
                if ni not in walls:
                    result.append(ni)
        return result

    adj: dict[int, list[int]] = {i: _neighbors(i) for i in passable}

    def available(idx: int, visited: set[int]) -> int:
        return sum(1 for nb in adj[idx] if nb not in visited)

    def is_connected(unvisited: set[int], start: int) -> bool:
        """BFS reachability check — O(|unvisited|)."""
        if not unvisited:
            return True
        seen = {start}
        queue = deque([start])
        while queue:
            cur = queue.popleft()
            for nb in adj[cur]:
                if nb in unvisited and nb not in seen:
                    seen.add(nb)
                    queue.append(nb)
        return len(seen) == len(unvisited)

    start = wp_by_num[1]
    path: list[int] = [start]
    visited: set[int] = {start}
    next_wp: int = 2  # next waypoint number that must be visited

    def backtrack() -> bool:
        nonlocal next_wp

        if len(path) == total:
            return next_wp > max_wp

        cur = path[-1]

        # Gather valid candidates
        candidates: list[int] = []
        for nb in adj[cur]:
            if nb in visited:
                continue
            # Waypoint ordering: a waypoint cell may only be entered when it
            # is the *next* required waypoint.
            if nb in wp_by_cell:
                if wp_by_cell[nb] != next_wp:
                    continue
            candidates.append(nb)

        if not candidates:
            return False

        # Warnsdorff ordering: prefer cells with fewer onward neighbours
        candidates.sort(key=lambda nb: available(nb, visited))

        for nb in candidates:
            path.append(nb)
            visited.add(nb)
            old_next = next_wp
            if nb in wp_by_cell:
                next_wp = wp_by_cell[nb] + 1

            # Connectivity pruning: every ~12 steps check that the remaining
            # unvisited cells are still all reachable.
            remaining = passable - visited
            do_check = len(remaining) <= 15 or len(path) % 12 == 0
            if not do_check or _reachable_ok(remaining, nb, adj, wp_by_cell, next_wp, max_wp):
                if backtrack():
                    return True

            path.pop()
            visited.discard(nb)
            next_wp = old_next

        return False

    logger.debug(
        "Starting Zip solver: %dx%d, %d passable cells, %d waypoints",
        n,
        n,
        total,
        max_wp,
    )
    if backtrack():
        return path
    return None


def _reachable_ok(
    remaining: set[int],
    last: int,
    adj: dict[int, list[int]],
    wp_by_cell: dict[int, int],
    next_wp: int,
    max_wp: int,
) -> bool:
    """Return False if remaining unvisited cells are disconnected, or if the
    next required waypoint is unreachable from *last*.

    Args:
        remaining: Set of unvisited passable cells.
        last: The cell just placed.
        adj: Precomputed adjacency map.
        wp_by_cell: Map cell_idx → waypoint number.
        next_wp: The next waypoint number that must be visited.
        max_wp: The final waypoint number.

    Returns:
        ``True`` if the remaining search looks feasible.
    """
    # --- Component connectivity ---
    if not remaining:
        return True

    # BFS from last to check all remaining cells are still in one component
    seen: set[int] = {last}
    queue: deque[int] = deque([last])
    while queue:
        cur = queue.popleft()
        for nb in adj[cur]:
            if nb in remaining and nb not in seen:
                seen.add(nb)
                queue.append(nb)

    # All remaining cells must be reachable from last
    if len(seen) < len(remaining):
        return False

    # --- Next waypoint reachability (quick check) ---
    # If the next required waypoint is not in the reachable set, fail.
    if next_wp <= max_wp:
        # We don't have the full state here, so just check if the next_wp cell
        # is in the remaining reachable set.
        # wp_by_cell is cell→num; we need to find the cell for next_wp
        next_cell = next(
            (cell for cell, num in wp_by_cell.items() if num == next_wp and cell in seen),
            None,
        )
        if next_cell is None:
            return False

    return True


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def format_path(path: list[int], state: ZipState) -> str:
    """Format the solution path as an ASCII grid.

    Args:
        path: Ordered list of cell indices.
        state: The puzzle state (used for grid size and wall info).

    Returns:
        A multi-line string showing the path step number at each cell.
    """
    n = state.grid_size
    grid = [["##" if i in state.walls else "  " for i in range(n)] for _ in range(n)]
    for step, idx in enumerate(path, 1):
        r, c = divmod(idx, n)
        grid[r][c] = f"{step:2d}"
    lines = []
    for row in grid:
        lines.append(" ".join(row))
    return "\n".join(lines)


def validate_path(path: list[int], state: ZipState) -> bool:
    """Return ``True`` if *path* is a valid solution.

    Checks:
    - Covers all passable cells exactly once.
    - Each consecutive pair is orthogonally adjacent.
    - Waypoints appear in ascending numerical order.

    Args:
        path: Candidate solution path.
        state: Puzzle state.

    Returns:
        ``True`` if valid.
    """
    n = state.grid_size
    passable = state.passable
    wp_by_cell = {v: k for k, v in state.waypoints.items()}

    if set(path) != passable:
        logger.debug(
            "Path does not cover all passable cells (|path|=%d, |passable|=%d)",
            len(set(path)),
            len(passable),
        )
        return False

    if len(path) != len(set(path)):
        logger.debug("Path visits a cell more than once.")
        return False

    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        ra, ca = divmod(a, n)
        rb, cb = divmod(b, n)
        if abs(ra - rb) + abs(ca - cb) != 1:
            logger.debug("Non-adjacent step %d→%d: (%d,%d)→(%d,%d)", a, b, ra, ca, rb, cb)
            return False

    last_wp = 0
    for idx in path:
        if idx in wp_by_cell:
            wp_num = wp_by_cell[idx]
            if wp_num != last_wp + 1:
                logger.debug("Waypoint out of order: expected %d got %d", last_wp + 1, wp_num)
                return False
            last_wp = wp_num

    if last_wp != state.max_waypoint:
        logger.debug("Not all waypoints visited (last=%d, max=%d)", last_wp, state.max_waypoint)
        return False

    return True
