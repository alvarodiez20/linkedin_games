# Mini Sudoku — DOM Extraction

**Source:** `linkedin_games/sudoku/extractor.py`

## How the extractor works

LinkedIn renders the Sudoku board inside a nested `<iframe>` whose `src` contains `/preload/`. The extractor:

1. Waits for an iframe matching `/preload/` to appear (up to 15 s).
2. Switches context into that iframe's content frame.
3. Queries every `.sudoku-cell[data-cell-idx]` element (36 cells total).
4. Reads the pre-filled value from `.sudoku-cell-content` text, but **only for cells with the class `sudoku-cell-prefilled`** — empty cells are left as `0`.
5. Validates that at least 6 pre-filled cells were found (sanity check).

## Output

A `6×6` `list[list[int]]` where `0` represents an empty cell:

```python
[
  [0, 0, 3, 0, 0, 0],
  [0, 0, 0, 0, 5, 0],
  # ...
]
```

## Key selectors

| Selector | Purpose |
|----------|---------|
| `iframe[src*="/preload/"]` | Locate the game iframe |
| `.sudoku-cell[data-cell-idx]` | Individual cells (0–35) |
| `.sudoku-cell-prefilled` | Cells with given clue values |
| `.sudoku-cell-content` | Text node containing the digit |
