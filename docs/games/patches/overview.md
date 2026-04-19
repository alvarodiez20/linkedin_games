# Patches — Overview

Patches is LinkedIn's variant of **Shikaku** — a rectangle-packing puzzle played on a 6×6 grid.

## Rules

1. Divide the entire grid into non-overlapping **rectangles** (patches).
2. Each patch contains **exactly one clue cell**.
3. A clue with a **number** specifies the exact cell count of its patch.
4. A clue with a **shape icon** restricts the geometry:
   - **Vertical rectangle** — height > width
   - **Horizontal rectangle** — width > height
   - **Square** — width == height
   - **Any** (no icon, but has a number) — any rectangle of that area

## Example

```
· · A · · ·
· · · · B ·
· · · · · ·
· · · C · ·
· · · · · ·
D · · · · ·

A = size 4, any shape
B = size 6, vertical
C = size 9, square
D = size 17, any
```

See [Algorithm](algorithm.md) for how the solver tiles the grid.
