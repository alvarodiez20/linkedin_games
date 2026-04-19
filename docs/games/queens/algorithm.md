# Queens — Algorithm

## Problem Formulation

Given an N×N grid partitioned into N colour regions, find a placement of N
queens such that:

- Each colour region contains **exactly one** queen.
- Each row contains **exactly one** queen.
- Each column contains **exactly one** queen.
- No two queens are **adjacent** (including diagonally — the full 8-cell
  Moore neighbourhood).

## Approach: Row-by-Row Backtracking

The solver uses a simple but effective **recursive backtracking** strategy:

```
for row 0 … N-1:
    for each column c in 0 … N-1:
        if c is not already used by another queen
        AND the colour of (row, c) is not already used
        AND no already-placed queen is adjacent to (row, c):
            place queen at (row, c)
            recurse to row + 1
            if recursion succeeds → done
            else → undo and try next column
```

### Constraint Checks

At each candidate cell `(row, col)` the solver enforces three constraints:

| Constraint | Check |
|---|---|
| **Column uniqueness** | `col ∉ col_used` |
| **Colour uniqueness** | `colors[row][col] ∉ color_used` |
| **Adjacency** | `∀ placed queen (pr, pc): max(|pr−row|, |pc−col|) > 1` |

The Chebyshev distance check (`max(|Δr|, |Δc|) > 1`) is equivalent to "not in
the 8-cell neighbourhood".

## Complexity

In the worst case this is O(N!) but in practice the colour constraint prunes
the search drastically — typically solving a 9×9 board in microseconds.

## Pre-filled Queens

LinkedIn occasionally pre-places one or more queens. These are read from the
DOM's `hasQueen` cell state. Pre-placed queens immediately fill the relevant
row, column, and colour entries, leaving fewer choices for the remaining rows.

## Validation

After solving, `validate_solution` checks all four constraints:

```python
# N queens
assert len(positions) == N
# Unique rows
assert len({r for r, c in positions}) == N
# Unique columns
assert len({c for r, c in positions}) == N
# Unique colour regions
assert len({colors[r][c] for r, c in positions}) == N
# No adjacency
for (r1, c1), (r2, c2) in combinations(positions, 2):
    assert not (abs(r1-r2) <= 1 and abs(c1-c2) <= 1)
```
