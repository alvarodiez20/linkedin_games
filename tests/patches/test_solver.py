"""Unit tests for the Patches (Shikaku) solver."""

from linkedin_games.patches.extractor import Clue, PatchesState, ShapeConstraint
from linkedin_games.patches.solver import (
    Rectangle,
    _candidate_rects,
    _shape_ok,
    solve,
    validate_solution,
)

GRID_SIZE = 6
TOTAL_CELLS = GRID_SIZE * GRID_SIZE


def _make_state(*clues: Clue, grid_size: int = GRID_SIZE) -> PatchesState:
    state = PatchesState(grid_size=grid_size)
    state.clues = list(clues)
    return state


class TestRectangle:
    def test_area(self):
        assert Rectangle(0, 0, 1, 2).area == 6  # 2 rows × 3 cols

    def test_width_and_height(self):
        r = Rectangle(1, 1, 3, 4)
        assert r.height == 3
        assert r.width == 4

    def test_cells_count(self):
        r = Rectangle(0, 0, 1, 1)
        assert len(r.cells()) == 4

    def test_contains(self):
        r = Rectangle(0, 0, 2, 2)
        assert r.contains(1, 1) is True
        assert r.contains(3, 3) is False

    def test_cells_are_correct(self):
        r = Rectangle(0, 0, 1, 1)
        assert r.cells() == frozenset({(0, 0), (0, 1), (1, 0), (1, 1)})


class TestShapeOk:
    def test_any_always_true(self):
        assert _shape_ok(Rectangle(0, 0, 0, 2), ShapeConstraint.ANY) is True

    def test_square_passes_equal_sides(self):
        assert _shape_ok(Rectangle(0, 0, 1, 1), ShapeConstraint.SQUARE) is True

    def test_square_fails_unequal_sides(self):
        assert _shape_ok(Rectangle(0, 0, 0, 2), ShapeConstraint.SQUARE) is False

    def test_vertical_passes_taller(self):
        assert _shape_ok(Rectangle(0, 0, 2, 0), ShapeConstraint.VERTICAL_RECT) is True

    def test_vertical_fails_wider(self):
        assert _shape_ok(Rectangle(0, 0, 0, 2), ShapeConstraint.VERTICAL_RECT) is False

    def test_horizontal_passes_wider(self):
        assert _shape_ok(Rectangle(0, 0, 0, 2), ShapeConstraint.HORIZONTAL_RECT) is True

    def test_horizontal_fails_taller(self):
        assert _shape_ok(Rectangle(0, 0, 2, 0), ShapeConstraint.HORIZONTAL_RECT) is False


class TestCandidateRects:
    def test_size_2_any_shape(self):
        clue = Clue(row=0, col=0, shape=ShapeConstraint.ANY, size=2, color=None)
        rects = _candidate_rects(clue, GRID_SIZE)
        assert all(r.area == 2 for r in rects)
        assert all(r.contains(0, 0) for r in rects)

    def test_square_shape_constraint(self):
        clue = Clue(row=0, col=0, shape=ShapeConstraint.SQUARE, size=None, color=None)
        rects = _candidate_rects(clue, GRID_SIZE)
        assert all(r.width == r.height for r in rects)

    def test_vertical_shape_constraint(self):
        clue = Clue(row=0, col=0, shape=ShapeConstraint.VERTICAL_RECT, size=None, color=None)
        rects = _candidate_rects(clue, GRID_SIZE)
        assert all(r.height > r.width for r in rects)

    def test_clue_cell_always_contained(self):
        clue = Clue(row=2, col=3, shape=ShapeConstraint.ANY, size=3, color=None)
        rects = _candidate_rects(clue, GRID_SIZE)
        assert all(r.contains(2, 3) for r in rects)
        assert all(r.area == 3 for r in rects)

    def test_larger_grid_size(self):
        """Candidates respect the grid boundary for a 7×7 grid."""
        clue = Clue(row=0, col=0, shape=ShapeConstraint.ANY, size=2, color=None)
        rects = _candidate_rects(clue, 7)
        assert all(r.r2 < 7 and r.c2 < 7 for r in rects)


class TestSolve:
    def test_trivial_single_clue_fills_entire_grid(self):
        # One clue at (0,0) with size=36 fills the 6×6 grid
        clue = Clue(row=0, col=0, shape=ShapeConstraint.ANY, size=36, color=None)
        state = _make_state(clue)
        result = solve(state)
        assert result is not None
        assert result[0] == Rectangle(0, 0, 5, 5)

    def test_two_clues_covering_full_grid(self):
        # Left half: clue at (0,0), size=18; Right half: clue at (0,3), size=18
        c1 = Clue(row=0, col=0, shape=ShapeConstraint.ANY, size=18, color=None)
        c2 = Clue(row=0, col=3, shape=ShapeConstraint.ANY, size=18, color=None)
        state = _make_state(c1, c2)
        result = solve(state)
        assert result is not None
        assert validate_solution(state.clues, result)

    def test_solution_validates(self):
        c1 = Clue(row=0, col=0, shape=ShapeConstraint.ANY, size=6, color=None)
        c2 = Clue(row=1, col=0, shape=ShapeConstraint.ANY, size=6, color=None)
        c3 = Clue(row=2, col=0, shape=ShapeConstraint.ANY, size=6, color=None)
        c4 = Clue(row=3, col=0, shape=ShapeConstraint.ANY, size=6, color=None)
        c5 = Clue(row=4, col=0, shape=ShapeConstraint.ANY, size=6, color=None)
        c6 = Clue(row=5, col=0, shape=ShapeConstraint.ANY, size=6, color=None)
        state = _make_state(c1, c2, c3, c4, c5, c6)
        result = solve(state)
        assert result is not None
        assert validate_solution(state.clues, result)

    def test_returns_none_when_no_solution(self):
        # Two clues both forced to the same single cell — no valid tiling
        c1 = Clue(row=0, col=0, shape=ShapeConstraint.ANY, size=36, color=None)
        c2 = Clue(row=0, col=1, shape=ShapeConstraint.ANY, size=36, color=None)
        state = _make_state(c1, c2)
        result = solve(state)
        assert result is None

    def test_shape_constraint_square_is_respected(self):
        # Four 3×3 squares in the grid
        c1 = Clue(row=0, col=0, shape=ShapeConstraint.SQUARE, size=9, color=None)
        c2 = Clue(row=0, col=3, shape=ShapeConstraint.SQUARE, size=9, color=None)
        c3 = Clue(row=3, col=0, shape=ShapeConstraint.SQUARE, size=9, color=None)
        c4 = Clue(row=3, col=3, shape=ShapeConstraint.SQUARE, size=9, color=None)
        state = _make_state(c1, c2, c3, c4)
        result = solve(state)
        assert result is not None
        for rect in result:
            assert rect.width == rect.height

    def test_7x7_grid(self):
        """Solver works for non-6×6 grid sizes (e.g. 7×7)."""
        c1 = Clue(row=0, col=0, shape=ShapeConstraint.ANY, size=49, color=None)
        state = _make_state(c1, grid_size=7)
        result = solve(state)
        assert result is not None
        assert result[0] == Rectangle(0, 0, 6, 6)


class TestValidateSolution:
    def test_valid_solution_passes(self):
        clue = Clue(row=0, col=0, shape=ShapeConstraint.ANY, size=36, color=None)
        rect = Rectangle(0, 0, 5, 5)
        assert validate_solution([clue], [rect]) is True

    def test_overlapping_rects_fail(self):
        c1 = Clue(row=0, col=0, shape=ShapeConstraint.ANY, size=4, color=None)
        c2 = Clue(row=0, col=1, shape=ShapeConstraint.ANY, size=4, color=None)
        r1 = Rectangle(0, 0, 1, 1)  # cells (0,0),(0,1),(1,0),(1,1)
        r2 = Rectangle(0, 1, 1, 2)  # overlaps at (0,1) and (1,1)
        assert validate_solution([c1, c2], [r1, r2]) is False

    def test_clue_outside_rect_fails(self):
        clue = Clue(row=5, col=5, shape=ShapeConstraint.ANY, size=4, color=None)
        rect = Rectangle(0, 0, 1, 1)  # does not contain (5,5)
        assert validate_solution([clue], [rect]) is False

    def test_wrong_size_fails(self):
        clue = Clue(row=0, col=0, shape=ShapeConstraint.ANY, size=4, color=None)
        rect = Rectangle(0, 0, 0, 5)  # area=6, not 4
        assert validate_solution([clue], [rect]) is False

    def test_wrong_total_cells_fails(self):
        """validate_solution checks total covered cells against total_cells arg."""
        clue = Clue(row=0, col=0, shape=ShapeConstraint.ANY, size=36, color=None)
        rect = Rectangle(0, 0, 5, 5)
        # pass total_cells=49 (7×7) — 36-cell rect won't cover 49
        assert validate_solution([clue], [rect], total_cells=49) is False
