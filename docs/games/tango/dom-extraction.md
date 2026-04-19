# Tango — DOM Extraction

**Source:** `linkedin_games/tango/extractor.py`

## How the extractor works

Tango renders in the **main page frame** (not an iframe). The extractor:

1. Queries all `[data-cell-idx]` elements (36 cells, 0–35).
2. Reads the cell symbol from the child SVG's `aria-label`:
   - `cell-zero` → Sun (1)
   - `cell-one` → Moon (2)
   - `cell-empty` → Empty (0)
3. Only treats cells with `aria-disabled="true"` as pre-filled clues.
4. Extracts **edge constraints** by finding elements with `data-testid` of `edge-equal` or `edge-cross` and computing which two cells they connect by comparing bounding-rect center coordinates.

## Edge constraint detection

```
for each edge element:
    center = bounding_rect.center
    nearest_cell_above = cell whose center is closest and above
    nearest_cell_below = cell whose center is closest and below (or right)
    constraints.append((cell_above, cell_below, "equal"|"opposite"))
```

## Output

A `TangoState` dataclass:

```python
@dataclass
class TangoState:
    grid: list[list[int]]          # 6×6, 0=empty, 1=sun, 2=moon
    prefilled: set[tuple[int,int]] # (row, col) pairs that are clues
    constraints: list[tuple[...]]  # ((r1,c1),(r2,c2),"equal"|"opposite")
```

## Key selectors

| Selector | Purpose |
|----------|---------|
| `[data-cell-idx]` | All 36 cells |
| `[aria-disabled="true"]` | Pre-filled clue cells |
| `[data-testid="edge-equal"]` | Equal constraint markers |
| `[data-testid="edge-cross"]` | Opposite constraint markers |
