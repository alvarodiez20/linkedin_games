# Tango — Algorithm

**Source:** `linkedin_games/tango/solver.py`

## Approach: Constraint Propagation + Backtracking + MRV

The solver combines three techniques:

1. **Constraint propagation** — derive forced assignments before searching.
2. **Backtracking** — explore remaining cells recursively.
3. **MRV heuristic** — always pick the cell with the fewest legal options.

### Constraint model

| Component | Description |
|-----------|-------------|
| Variables | Each empty cell |
| Domain | {Sun=1, Moon=2} |
| Global constraints | Balance (3 of each per row/col), no-three-in-a-row |
| Edge constraints | Equal or Opposite between specific cell pairs |

### Phase 1: Constraint propagation

Before backtracking, the solver scans all edge constraints. If one cell in an `equal`/`opposite` pair is already filled, the other is immediately determined:

```
if cell_a == SUN and constraint == "equal":
    cell_b = SUN   # forced
if cell_a == SUN and constraint == "opposite":
    cell_b = MOON  # forced
```

This loop repeats until no further deductions can be made (fixed-point). If a contradiction is found (two cells forced to conflicting values) the puzzle is immediately declared unsolvable.

### Phase 2: Backtracking + MRV

```
function backtrack(board, constraints):
    cell = cell_with_fewest_candidates(board, constraints)  # MRV
    if cell is None:
        return SOLVED

    for value in [SUN, MOON]:
        board[cell] = value
        if is_consistent(board, cell, constraints):
            if backtrack(board, constraints):
                return SOLVED
        board[cell] = EMPTY

    return UNSOLVABLE
```

### Consistency check

`is_consistent` verifies two things after placing a value:

1. **Local validity** — no three consecutive identical symbols, row/column balance not exceeded.
2. **Edge constraints** — all `equal`/`opposite` pairs involving the cell that are now fully assigned.

!!! note "Why propagation + backtracking?"
    Propagation alone solves many LinkedIn Tango puzzles without any search.
    Backtracking handles the rare cases where propagation leaves ambiguity.

### Complexity

| | |
|---|---|
| After propagation | Often 0–5 undecided cells |
| Worst case search | O(2^k) where k = undecided cells after propagation |
| In practice | Sub-millisecond |
