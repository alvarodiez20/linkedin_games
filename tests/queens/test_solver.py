"""Unit tests for the Queens solver."""

from linkedin_games.queens.extractor import QueensState
from linkedin_games.queens.solver import (
    QueensSolution,
    _adjacent_conflict,
    format_solution,
    solve,
    validate_solution,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _diagonal_colors(n: int) -> list[list[int]]:
    """Each color region is one diagonal stripe — always has a valid solution."""
    return [[(r + c) % n for c in range(n)] for r in range(n)]


def _strip_colors(n: int) -> list[list[int]]:
    """Each color region is one full row."""
    return [[r] * n for r in range(n)]


def _make_state(colors: list[list[int]], prefilled: list[list[bool]] | None = None) -> QueensState:
    n = len(colors)
    pf = prefilled or [[False] * n for _ in range(n)]
    return QueensState(grid_size=n, colors=colors, prefilled=pf)


# ---------------------------------------------------------------------------
# TestAdjacentConflict
# ---------------------------------------------------------------------------


class TestAdjacentConflict:
    def test_no_queens_no_conflict(self):
        assert _adjacent_conflict(0, 0, []) is False

    def test_same_cell_is_conflict(self):
        assert _adjacent_conflict(0, 0, [(0, 0)]) is True

    def test_orthogonal_neighbors_are_conflicts(self):
        assert _adjacent_conflict(1, 0, [(0, 0)]) is True  # below
        assert _adjacent_conflict(0, 1, [(0, 0)]) is True  # right

    def test_diagonal_neighbor_is_conflict(self):
        assert _adjacent_conflict(1, 1, [(0, 0)]) is True

    def test_two_apart_is_not_conflict(self):
        assert _adjacent_conflict(0, 2, [(0, 0)]) is False
        assert _adjacent_conflict(2, 0, [(0, 0)]) is False

    def test_none_entries_are_skipped(self):
        positions: list = [None, (0, 0)]
        assert _adjacent_conflict(1, 1, positions) is True

    def test_far_rows_no_conflict(self):
        assert _adjacent_conflict(3, 3, [(0, 0)]) is False


# ---------------------------------------------------------------------------
# TestSolve
# ---------------------------------------------------------------------------


class TestSolve:
    def test_1x1_trivial(self):
        state = _make_state([[0]])
        result = solve(state)
        assert result is not None
        assert result.positions == [(0, 0)]

    def test_2x2_no_solution(self):
        """Every pair of cells in a 2×2 grid is adjacent — no solution exists."""
        colors = [[0, 1], [0, 1]]
        state = _make_state(colors)
        result = solve(state)
        assert result is None

    def test_4x4_strip_colors(self):
        colors = _strip_colors(4)
        state = _make_state(colors)
        result = solve(state)
        assert result is not None
        assert validate_solution(result, colors)

    def test_5x5_diagonal_colors(self):
        colors = _diagonal_colors(5)
        state = _make_state(colors)
        result = solve(state)
        assert result is not None
        assert validate_solution(result, colors)

    def test_8x8_strip_colors(self):
        """8×8 board with row-strip coloring always has a valid solution."""
        colors = _strip_colors(8)
        state = _make_state(colors)
        result = solve(state)
        assert result is not None
        assert validate_solution(result, colors)

    def test_solution_has_n_queens(self):
        n = 6
        colors = _strip_colors(n)
        state = _make_state(colors)
        result = solve(state)
        assert result is not None
        assert len(result.positions) == n

    def test_all_rows_distinct(self):
        colors = _strip_colors(5)
        state = _make_state(colors)
        result = solve(state)
        assert result is not None
        assert len({r for r, c in result.positions}) == 5

    def test_all_cols_distinct(self):
        colors = _strip_colors(5)
        state = _make_state(colors)
        result = solve(state)
        assert result is not None
        assert len({c for r, c in result.positions}) == 5

    def test_all_colors_distinct(self):
        colors = _strip_colors(5)
        state = _make_state(colors)
        result = solve(state)
        assert result is not None
        color_ids = [colors[r][c] for r, c in result.positions]
        assert len(set(color_ids)) == 5

    def test_prefilled_queen_is_honoured(self):
        """A pre-placed queen at (0,0) must appear in the solution."""
        colors = _strip_colors(5)
        prefilled = [[False] * 5 for _ in range(5)]
        prefilled[0][0] = True
        state = _make_state(colors, prefilled)
        result = solve(state)
        assert result is not None
        assert (0, 0) in result.positions

    def test_known_4x4_solution(self):
        """Hand-crafted 4×4 board with a known valid solution."""
        # Colors:
        #  0 0 1 1
        #  0 0 1 1
        #  2 2 3 3
        #  2 2 3 3
        colors = [
            [0, 0, 1, 1],
            [0, 0, 1, 1],
            [2, 2, 3, 3],
            [2, 2, 3, 3],
        ]
        state = _make_state(colors)
        result = solve(state)
        assert result is not None
        assert validate_solution(result, colors)
        # Verify no adjacency violations explicitly
        positions = result.positions
        for i, (r1, c1) in enumerate(positions):
            for j, (r2, c2) in enumerate(positions):
                if i >= j:
                    continue
                assert not (abs(r1 - r2) <= 1 and abs(c1 - c2) <= 1), (
                    f"Queens at ({r1},{c1}) and ({r2},{c2}) are adjacent!"
                )


# ---------------------------------------------------------------------------
# TestValidateSolution
# ---------------------------------------------------------------------------


class TestValidateSolution:
    def _sol(self, n: int, positions: list[tuple[int, int]]) -> QueensSolution:
        return QueensSolution(positions=positions, grid_size=n)

    def test_valid_1x1(self):
        assert validate_solution(self._sol(1, [(0, 0)]), [[0]]) is True

    def test_wrong_queen_count(self):
        sol = self._sol(2, [(0, 0)])  # only 1 queen for a 2×2 board
        assert validate_solution(sol, _strip_colors(2)) is False

    def test_duplicate_row_fails(self):
        sol = self._sol(2, [(0, 0), (0, 1)])
        assert validate_solution(sol, [[0, 0], [1, 1]]) is False

    def test_duplicate_col_fails(self):
        sol = self._sol(2, [(0, 0), (1, 0)])
        assert validate_solution(sol, [[0, 1], [0, 1]]) is False

    def test_duplicate_color_fails(self):
        sol = self._sol(2, [(0, 0), (0, 1)])
        # both in color region 0
        assert validate_solution(sol, [[0, 0], [1, 1]]) is False

    def test_adjacency_fails(self):
        colors = _strip_colors(3)
        sol = self._sol(3, [(0, 0), (1, 1), (2, 2)])
        assert validate_solution(sol, colors) is False

    def test_valid_strip_solution(self):
        n = 4
        colors = _strip_colors(n)
        result = solve(_make_state(colors))
        assert result is not None
        assert validate_solution(result, colors) is True


# ---------------------------------------------------------------------------
# TestFormatSolution
# ---------------------------------------------------------------------------


class TestFormatSolution:
    def test_queen_marker_present(self):
        sol = QueensSolution(positions=[(0, 0)], grid_size=1)
        output = format_solution(sol, [[0]])
        assert "Q" in output

    def test_non_queen_cell_shows_color(self):
        sol = QueensSolution(positions=[(0, 0)], grid_size=2)
        colors = [[0, 1], [2, 3]]
        output = format_solution(sol, colors)
        assert "1" in output
        assert "2" in output
        assert "3" in output

    def test_output_has_n_lines(self):
        n = 4
        colors = _strip_colors(n)
        result = solve(_make_state(colors))
        assert result is not None
        output = format_solution(result, colors)
        assert len(output.strip().split("\n")) == n

    def test_exactly_n_queens_in_output(self):
        n = 5
        colors = _strip_colors(n)
        result = solve(_make_state(colors))
        assert result is not None
        output = format_solution(result, colors)
        assert sum(row.count("Q") for row in output.split("\n")) == n
