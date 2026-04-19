# Mini Sudoku — Overview

LinkedIn's Mini Sudoku is a 6×6 variant of classic Sudoku.

## Rules

1. Fill every cell with a number from **1 to 6**.
2. No number may repeat in any **row**.
3. No number may repeat in any **column**.
4. No number may repeat in any of the six **2×3 sub-grids**.

## Sub-grid layout

```
┌───────┬───────┐
│ 0,0   │ 0,3   │
│  2×3  │  2×3  │
├───────┼───────┤
│ 2,0   │ 2,3   │
│  2×3  │  2×3  │
├───────┼───────┤
│ 4,0   │ 4,3   │
│  2×3  │  2×3  │
└───────┴───────┘
```

The grid ships with some cells pre-filled. Your task (and the solver's) is to deduce the remaining values.

## Example

```
· · 3 | · · ·
· · · | · 5 ·
· 5 · | · · 1
------+------
2 · · | · 4 ·
· 4 · | · · ·
· · · | 6 · ·
```

See [Algorithm](algorithm.md) for how the solver finds the solution.
