# Patches — Algorithm

**Source:** `linkedin_games/patches/solver.py`

## Approach: CSP + Forward-checking + MRV

Patches is modelled as a **Constraint Satisfaction Problem (CSP)**:

| Component | Description |
|-----------|-------------|
| Variables | One rectangle per clue |
| Domain | All valid rectangles for that clue (pre-computed) |
| Constraints | No two rectangles overlap; together they tile the full 36 cells |

### Step 1: Candidate generation

Before searching, every valid rectangle for each clue is pre-computed:

```python
for r1, c1, r2, c2 in all_possible_rectangles:
    rect = Rectangle(r1, c1, r2, c2)
    if rect.contains(clue.row, clue.col)
       and (clue.size is None or rect.area == clue.size)
       and shape_ok(rect, clue.shape):
        candidates[clue].append(rect)
```

### Step 2: Pre-draw placement

Any regions already drawn on screen are placed first, reducing the search space immediately.

### Step 3: Backtracking with MRV + Forward-checking

```
function backtrack(unsolved_clues, occupied_cells):
    clue = clue_with_fewest_candidates(unsolved_clues)  # MRV

    for rect in candidates[clue]:
        if rect overlaps occupied:
            continue

        place(rect)                                    # mark cells occupied
        prune(candidates for remaining clues)          # forward-checking

        if any remaining clue has 0 candidates:
            undo and continue                          # dead-end detected early

        if backtrack(remaining_clues, occupied):
            return SOLVED

        undo(rect)

    return UNSOLVABLE
```

### Forward-checking

After placing a rectangle, the solver immediately filters every remaining clue's candidates to remove rectangles that would overlap the newly occupied cells. If any clue is left with zero candidates, the branch is pruned **before** recursing deeper.

!!! tip "Why forward-checking matters for Patches"
    A 6×6 grid has 36 cells. Without forward-checking, the solver might place several rectangles before discovering a clue is now impossible. Forward-checking catches dead ends one level up, cutting the search tree significantly.

### MRV

Among unsolved clues, the one with the smallest candidate list is placed next. Clues forced to a single rectangle are resolved first, chaining constraint propagation naturally.

### Complexity

| | |
|---|---|
| Pre-computation | O(n · G⁴) where G=6, n=number of clues |
| Search | Exponential worst-case, near-linear in practice |
| Typical puzzles | Sub-millisecond |
