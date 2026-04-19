# Tango — Algorithm

**Source:** `linkedin_games/tango/solver.py`

## Approach: Constraint Propagation + Backtracking + MRV

The solver combines three techniques in a specific order to minimise search:

1. **Constraint propagation** — derive forced assignments from edge constraints before searching.
2. **Backtracking with MRV** — explore remaining cells using the variable with the fewest legal options.
3. **Consistency checking** — prune branches as early as possible using local validity rules.

---

## Constraint model

| Component | Description |
|-----------|-------------|
| Variables | Each empty cell in the 6×6 grid |
| Domain | {Sun = 1, Moon = 2} |
| Balance rule | Exactly 3 Suns and 3 Moons per row and column |
| No-three rule | No 3 consecutive identical symbols horizontally or vertically |
| Edge constraints | `equal` (same symbol) or `opposite` (different symbol) between adjacent cells |

---

## Phase 1: Constraint Propagation

Before any backtracking, the solver scans all edge constraints and applies **arc consistency**. If one endpoint of a constraint is already filled and the other is empty, the second cell can be immediately determined:

```mermaid
flowchart TD
    A([Start propagation]) --> B[Scan all edge constraints]
    B --> C{Constraint type?}
    C -- equal --> D{One side filled,\nother empty?}
    C -- opposite --> E{One side filled,\nother empty?}
    D -- Yes --> F["Fill empty cell\nwith same value"]
    E -- Yes --> G["Fill empty cell\nwith opposite value"]
    F & G --> H[Mark changed = True]
    D -- No --> I{Both filled?}
    E -- No --> I
    I -- Conflict --> J([Return False\ncontradiction])
    I -- Consistent --> B
    H --> B
    B -- No changes --> K([Return True\npropagation complete])
```

This loop repeats (fixed-point iteration) until no new deductions can be made or a contradiction is found.

!!! note "Why propagation before backtracking?"
    Many LinkedIn Tango puzzles can be fully solved by propagation alone —
    especially those with chains of `equal`/`opposite` constraints. When
    propagation leaves 0 undecided cells, backtracking is never invoked at all.

### Propagation example

```
Given:  (0,0) = ☀,  constraint: (0,0) = (0,1)

Step 1: (0,1) is empty, (0,0) = ☀, type = equal  →  (0,1) := ☀
Step 2: constraint: (0,1) × (0,2)
        (0,1) = ☀, type = opposite                →  (0,2) := ☽
Step 3: No more deductions. Stop.
```

---

## Phase 2: Backtracking with MRV

After propagation, remaining empty cells are filled via backtracking:

```mermaid
flowchart TD
    A([Start backtrack]) --> B{Any empty cell?}
    B -- No --> C([Return SOLVED])
    B -- Yes --> D[MRV: pick empty cell\nwith fewest valid options]
    D --> E{Candidate count}
    E -- 0 --> F([Return FAIL — backtrack])
    E -- 1 or 2 --> G[Try first candidate value]
    G --> H[Place value in cell]
    H --> I[Consistency check]
    I -- Fail --> J[Undo — try next candidate]
    J --> G
    I -- Pass --> K[Recurse deeper]
    K -- Success --> C
    K -- Fail --> J
    J -- No more candidates --> F
```

---

## Consistency check in detail

After placing a value at `(r, c)`, two checks run before recursing:

```mermaid
flowchart LR
    A["Place val at (r,c)"] --> B[_is_locally_valid]
    B --> C{No three\nconsecutive?}
    C -- Fail --> Z([Reject])
    C -- Pass --> D{Row count\n≤ HALF?}
    D -- Fail --> Z
    D -- Pass --> E{Col count\n≤ HALF?}
    E -- Fail --> Z
    E -- Pass --> F[Check edge constraints\ninvolving this cell]
    F --> G{Both endpoints\nfilled?}
    G -- No --> H([Accept])
    G -- Yes --> I{equal/opposite\nsatisfied?}
    I -- Yes --> H
    I -- No --> Z
```

### No-three-in-a-row check

Six patterns are tested for each placed cell — three horizontal and three vertical:

```
Horizontal patterns for cell at column c:
  [c-2][c-1][c]   ←←←
  [c-1][c][c+1]   ←→
      [c][c+1][c+2]  →→

Vertical patterns for cell at row r: (same, transposed)
```

### Balance check

```
row_count  = number of val already in row  r
col_count  = number of val already in col  c

if row_count > 3 or col_count > 3:  REJECT
```

---

## MRV for binary domains

With only two possible values (Sun / Moon), MRV picks from:
- **Count = 0** → dead end, backtrack immediately.
- **Count = 1** → forced assignment, no branching.
- **Count = 2** → genuine choice, branch.

```mermaid
flowchart LR
    A[Scan empty cells] --> B[For each: test Sun,\ntest Moon locally]
    B --> C{Any cell\nwith count 0?}
    C -- Yes --> D([Return it: dead end])
    C -- No --> E{Any cell\nwith count 1?}
    E -- Yes --> F([Return it: forced])
    E -- No --> G([Return cell with\ncount = 2])
```

---

## End-to-end sequence diagram

```mermaid
sequenceDiagram
    participant M as __main__
    participant S as solver.solve()
    participant P as _propagate()
    participant BT as _backtrack()
    participant MRV as _find_best_empty()
    participant CC as _is_consistent()

    M->>S: solve(grid, constraints)
    S->>P: _propagate(board, constraints)
    P-->>S: True (no contradiction)
    S->>BT: _backtrack(board, constraints)
    BT->>MRV: find_best_empty(board, constraints)
    MRV-->>BT: cell = (2, 3), count = 1  [forced]
    BT->>CC: is_consistent(board, 2, 3, constraints)
    CC-->>BT: True
    BT->>BT: recurse()
    BT-->>S: True
    S-->>M: solved board
```

---

## Complexity

| Measure | Value |
|---------|-------|
| After propagation | Often 0–5 undecided cells remain |
| Worst-case search | O(2^k) where k = undecided cells after propagation |
| Typical time | Sub-millisecond |
| Binary domain | Makes MRV very effective — forced assignments are common |
