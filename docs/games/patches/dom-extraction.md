# Patches — DOM Extraction

**Source:** `linkedin_games/patches/extractor.py`

## How the extractor works

Patches renders in the **main page frame**. The extractor:

1. Queries all `[data-cell-idx="0"]`–`[data-cell-idx="35"]` elements.
2. For each cell, detects whether it holds a clue:
   - **Shape** — read from the `[data-shape]` attribute and mapped to `ShapeConstraint`.
   - **Size** — read from `[data-testid^="patches-clue-number"]` text content.
   - **Color** — extracted from the CSS variable `--d5a654bb` in the element's inline style.
3. Detects **pre-drawn regions** by looking for cells whose `aria-label` contains `"drawn region"` or `"región dibujada"`. Each group of such cells is associated with the clue index it belongs to.

## Shape mapping

| DOM value | `ShapeConstraint` |
|-----------|-------------------|
| `PatchesShapeConstraint_VERTICAL_RECT` | `VERTICAL_RECT` |
| `PatchesShapeConstraint_HORIZONTAL_RECT` | `HORIZONTAL_RECT` |
| `PatchesShapeConstraint_SQUARE` | `SQUARE` |
| `PatchesShapeConstraint_UNKNOWN` | `ANY` |

## Output

A `PatchesState` dataclass:

```python
@dataclass
class PatchesState:
    clues: list[Clue]
    predrawn: list[tuple[frozenset[tuple[int,int]], int]]
    # predrawn: [(set_of_cells, clue_index), ...]
```

## Key selectors

| Selector | Purpose |
|----------|---------|
| `[data-cell-idx]` | All 36 cells |
| `[data-shape]` | Shape constraint attribute |
| `[data-testid^="patches-clue-number"]` | Clue size number |
| `aria-label` containing `"drawn region"` | Pre-drawn region cells |
