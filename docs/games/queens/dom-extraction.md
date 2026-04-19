# Queens — DOM Extraction

## Page Structure

The Queens game renders in the **main browser frame** (no iframes).

```
[data-testid="queens-game-container"]     ← outer wrapper
  └─ [data-testid="interactive-grid"]     ← NxN grid
       └─ div[data-cell-idx="0..N²-1"]   ← one div per cell
            ├─ [data-cell-color="0..N-1"] ← colour region index  (strategy 1)
            ├─ class="… color-{N} …"      ← CSS class fallback   (strategy 2)
            └─ style="background-color:…" ← computed BG fallback (strategy 3)
```

## Cell Index Scheme

Each cell carries `data-cell-idx` (a zero-based integer, row-major):

```
cell_idx = row × N + col
row      = cell_idx ÷ N   (integer division)
col      = cell_idx mod N
```

The grid size `N` is inferred dynamically:

```python
n_cells  = len(cells)
grid_size = int(math.sqrt(n_cells))
assert grid_size * grid_size == n_cells
```

## Colour Region Detection

The extractor tries three strategies in priority order:

| Priority | Source | Example |
|---|---|---|
| 1 | `data-cell-color` attribute | `data-cell-color="3"` |
| 2 | CSS class containing `"color"` | `class="queens-cell queens-cell-color-3"` |
| 3 | Computed `background-color` | `rgb(255, 200, 100)` → mapped to index |

Strategy 3 builds a colour-index map by collecting all unique `background-color`
values across all cells and assigning them integer indices in encounter order.

## Queen Detection

A queen is considered present on a cell when:

- The cell's `aria-label` matches `/queen/i`, **or**
- The cell or any descendent has a class matching `/queen/i`.

## Waiting for the Board

The extractor uses a polling loop (`_wait_for_board`) that waits until:

1. At least one `[data-cell-idx]` element exists.
2. The total cell count is a perfect square ≥ 4.
3. At least one cell carries colour information (strategy 1, 2, or 3).

The default timeout is **15 seconds** (`LOAD_TIMEOUT_MS`).
