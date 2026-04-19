"""Unit tests for the Tango (sun/moon binary puzzle) solver."""

import pytest

from linkedin_games.tango.solver import (
    MOON,
    SUN,
    _is_locally_valid,
    _propagate,
    solve,
    validate_solution,
)

# Helpers
E = 0  # EMPTY shorthand


def _empty_board():
    return [[E] * 6 for _ in range(6)]


# A fully constrained puzzle that forces a unique solution
PUZZLE_CONSTRAINED = [
    [SUN, E,   E,   E,   E,   E],
    [E,   E,   E,   E,   E,   E],
    [E,   E,   SUN, E,   E,   E],
    [E,   E,   E,   MOON,E,   E],
    [E,   E,   E,   E,   E,   E],
    [E,   E,   E,   E,   E,   SUN],
]

NO_CONSTRAINTS: list = []


class TestSolve:
    def test_returns_solution_for_solvable_puzzle(self):
        result = solve(PUZZLE_CONSTRAINED, NO_CONSTRAINTS)
        assert result is not None

    def test_solution_passes_validation(self):
        result = solve(PUZZLE_CONSTRAINED, NO_CONSTRAINTS)
        assert result is not None
        assert validate_solution(result, NO_CONSTRAINTS)

    def test_does_not_mutate_input(self):
        import copy
        original = copy.deepcopy(PUZZLE_CONSTRAINED)
        solve(PUZZLE_CONSTRAINED, NO_CONSTRAINTS)
        assert PUZZLE_CONSTRAINED == original

    def test_returns_none_for_invalid_puzzle(self):
        # Row 0 has 4 suns — violates balance rule, no solution possible
        bad = [
            [SUN, SUN, SUN, SUN, E, E],
            [E] * 6,
            [E] * 6,
            [E] * 6,
            [E] * 6,
            [E] * 6,
        ]
        assert solve(bad, NO_CONSTRAINTS) is None

    def test_equal_constraint_is_respected(self):
        grid = _empty_board()
        grid[0][0] = SUN
        constraints = [((0, 0), (0, 1), "equal")]
        result = solve(grid, constraints)
        assert result is not None
        assert result[0][0] == result[0][1]

    def test_opposite_constraint_is_respected(self):
        grid = _empty_board()
        grid[0][0] = SUN
        constraints = [((0, 0), (0, 1), "opposite")]
        result = solve(grid, constraints)
        assert result is not None
        assert result[0][0] != result[0][1]

    def test_conflicting_constraints_return_none(self):
        grid = _empty_board()
        grid[0][0] = SUN
        grid[0][1] = MOON
        # Both equal AND opposite between (0,0) and (0,1) is a contradiction
        constraints = [
            ((0, 0), (0, 1), "equal"),
            ((0, 0), (0, 1), "opposite"),
        ]
        assert solve(grid, constraints) is None


class TestPropagate:
    def test_equal_propagates_known_value(self):
        board = _empty_board()
        board[0][0] = SUN
        constraints = [((0, 0), (0, 1), "equal")]
        result = _propagate(board, constraints)
        assert result is True
        assert board[0][1] == SUN

    def test_opposite_propagates_known_value(self):
        board = _empty_board()
        board[0][0] = SUN
        constraints = [((0, 0), (0, 1), "opposite")]
        result = _propagate(board, constraints)
        assert result is True
        assert board[0][1] == MOON

    def test_contradiction_returns_false(self):
        board = _empty_board()
        board[0][0] = SUN
        board[0][1] = MOON
        constraints = [((0, 0), (0, 1), "equal")]
        assert _propagate(board, constraints) is False

    def test_chain_propagation(self):
        board = _empty_board()
        board[0][0] = SUN
        constraints = [
            ((0, 0), (0, 1), "equal"),   # (0,1) → SUN
            ((0, 1), (0, 2), "opposite"), # (0,2) → MOON
        ]
        _propagate(board, constraints)
        assert board[0][1] == SUN
        assert board[0][2] == MOON


class TestLocalValidity:
    def test_three_in_a_row_horizontal_is_invalid(self):
        board = _empty_board()
        board[0][0] = SUN
        board[0][1] = SUN
        board[0][2] = SUN
        assert _is_locally_valid(board, 0, 2) is False

    def test_three_in_a_row_vertical_is_invalid(self):
        board = _empty_board()
        board[0][0] = MOON
        board[1][0] = MOON
        board[2][0] = MOON
        assert _is_locally_valid(board, 2, 0) is False

    def test_row_imbalance_is_invalid(self):
        board = _empty_board()
        # 4 suns in row 0 exceeds HALF (3)
        for c in range(4):
            board[0][c] = SUN
        assert _is_locally_valid(board, 0, 3) is False

    def test_valid_partial_row_is_ok(self):
        board = _empty_board()
        board[0][0] = SUN
        board[0][1] = MOON
        assert _is_locally_valid(board, 0, 1) is True


class TestValidateSolution:
    def _make_valid_board(self):
        # Alternating pattern satisfying all Tango rules
        return [
            [SUN,  MOON, SUN,  MOON, SUN,  MOON],
            [MOON, SUN,  MOON, SUN,  MOON, SUN],
            [SUN,  MOON, SUN,  MOON, SUN,  MOON],
            [MOON, SUN,  MOON, SUN,  MOON, SUN],
            [SUN,  MOON, SUN,  MOON, SUN,  MOON],
            [MOON, SUN,  MOON, SUN,  MOON, SUN],
        ]

    def test_valid_board_returns_true(self):
        assert validate_solution(self._make_valid_board(), []) is True

    def test_imbalanced_row_returns_false(self):
        board = self._make_valid_board()
        board[0] = [SUN, SUN, SUN, SUN, MOON, MOON]  # 4 suns
        assert validate_solution(board, []) is False

    def test_three_consecutive_returns_false(self):
        board = self._make_valid_board()
        board[0][0] = SUN
        board[0][1] = SUN
        board[0][2] = SUN  # three in a row
        assert validate_solution(board, []) is False

    def test_equal_constraint_violation_returns_false(self):
        board = self._make_valid_board()
        constraints = [((0, 0), (0, 1), "equal")]
        # board[0][0]=SUN, board[0][1]=MOON → violates equal
        assert validate_solution(board, constraints) is False

    def test_opposite_constraint_satisfied(self):
        board = self._make_valid_board()
        constraints = [((0, 0), (0, 1), "opposite")]
        # board[0][0]=SUN, board[0][1]=MOON → satisfies opposite
        assert validate_solution(board, constraints) is True
