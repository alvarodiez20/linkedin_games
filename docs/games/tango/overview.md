# Tango — Overview

Tango is a 6×6 binary constraint puzzle where each cell must hold either a **Sun** (☀) or a **Moon** (☽).

## Rules

1. Each cell is either a Sun or a Moon.
2. No three consecutive identical symbols in any **row** or **column**.
3. Each row and each column has exactly **3 Suns and 3 Moons**.
4. Some adjacent pairs of cells have **edge constraints**:
   - **Equal** (`=`): the two cells must have the same symbol.
   - **Opposite** (`×`): the two cells must have different symbols.

## Example

```
· · ☀ · · ·
· · · · ☽ ·
· ☀ · · · ·
· · · ☽ · ·
· · · · · ·
· · · · · ☀

 = between (0,2)–(0,3)
 × between (2,1)–(3,1)
```

See [Algorithm](algorithm.md) for how the solver reasons through these constraints.
