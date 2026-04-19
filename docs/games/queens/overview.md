# Queens — Overview

Queens is LinkedIn's daily **colour-region N-Queens** puzzle.

## Rules

1. A **N×N** grid is pre-divided into **N colour regions**.
2. Place **exactly one queen** in each colour region.
3. Each **row** must contain exactly one queen.
4. Each **column** must contain exactly one queen.
5. No two queens may **touch** — including diagonally (the 8 surrounding cells
   of any queen must all be empty).

This is a strict strengthening of the classical N-Queens problem: the diagonal
attack constraint is replaced by an adjacency constraint (no two queens may be
in neighbouring cells), and colour regions provide an additional partition
constraint.

## Example (8×8)

```
·  ·  ·  ·  ·  Q  ·  ·   ← queen in colour 0, row 0, col 5
·  ·  Q  ·  ·  ·  ·  ·   ← queen in colour 1, row 1, col 2
·  ·  ·  ·  Q  ·  ·  ·   ← queen in colour 2, row 2, col 4
Q  ·  ·  ·  ·  ·  ·  ·   ← queen in colour 3, row 3, col 0
·  ·  ·  Q  ·  ·  ·  ·   ← queen in colour 4, row 4, col 3
·  ·  ·  ·  ·  ·  Q  ·   ← queen in colour 5, row 5, col 6
·  Q  ·  ·  ·  ·  ·  ·   ← queen in colour 6, row 6, col 1
·  ·  ·  ·  ·  ·  ·  Q   ← queen in colour 7, row 7, col 7
```

No two queens share a row, column, or adjacent cell.

See [Algorithm](algorithm.md) for how the solver finds a valid placement.
