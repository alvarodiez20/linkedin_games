# Patches — Algorithm

**Source:** `linkedin_games/patches/solver.py`

## Approach: CSP + Forward-checking + MRV

Patches is modelled as a **Constraint Satisfaction Problem (CSP)**:

| Component | Description |
|-----------|-------------|
| Variables | One rectangle per clue |
| Domain | All geometrically valid rectangles for that clue (pre-computed) |
| Constraints | No two rectangles overlap; together they tile all 36 cells exactly once |

The solver runs in four stages:

```mermaid
flowchart TD
    A([Start]) --> B[Stage 1: Pre-compute\ncandidate rectangles\nfor each clue]
    B --> C[Stage 2: Place\npre-drawn regions\nfirst]
    C --> D[Stage 3: Filter candidates\nagainst occupied cells]
    D --> E[Stage 4: Backtrack\nwith MRV + Forward-checking]
    E -- Solution found --> F([Return solution])
    E -- No solution --> G([Return None])
```

---

## Stage 1: Candidate rectangle generation

Before any search, every valid rectangle for every clue is enumerated. A rectangle `(r1, c1, r2, c2)` is valid for a clue if:

1. It **contains** the clue cell `(clue.row, clue.col)`.
2. It **fits** within the 6×6 grid.
3. Its **area** equals `clue.size` (if specified).
4. Its **shape** satisfies `clue.shape`.

```mermaid
flowchart TD
    A[For each clue] --> B[For every r1,c1,r2,c2\nin grid bounds]
    B --> C{Contains\nclue cell?}
    C -- No --> B
    C -- Yes --> D{Area ==\nclue.size?\nor size is None}
    D -- No --> B
    D -- Yes --> E{Shape\nconstraint OK?}
    E -- No --> B
    E -- Yes --> F[Add to candidates]
    F --> B
```

### Shape constraint decision

```mermaid
flowchart LR
    A{clue.shape} -- ANY --> B([Accept any rectangle])
    A -- SQUARE --> C{width == height?}
    C -- Yes --> B
    C -- No --> D([Reject])
    A -- VERTICAL_RECT --> E{height > width?}
    E -- Yes --> B
    E -- No --> D
    A -- HORIZONTAL_RECT --> F{width > height?}
    F -- Yes --> B
    F -- No --> D
```

---

## Stage 2: Pre-drawn region placement

Some cells may already be highlighted (pre-drawn by a previous partial solve).
These are placed before the search begins — they consume cells and reduce the
effective search space immediately.

```mermaid
flowchart TD
    A[For each pre-drawn region] --> B{Find matching\nrectangle in candidates?}
    B -- Found --> C[Place it in solution\nmark cells as occupied]
    B -- Not found --> D[Build bounding-box\nrectangle from cells\nforce-place it]
    D --> C
    C --> E[Remove clue from\nunsolved list]
```

---

## Stage 3: Backtracking with MRV + Forward-checking

This is the core search. At each recursive step:

1. **MRV** — select the unsolved clue with the fewest remaining candidate rectangles.
2. **Try** each candidate in turn.
3. **Forward-check** — after placing a rectangle, remove from every other clue's candidate list any rectangle that would overlap the newly occupied cells.  If any clue's list becomes empty, abort this branch immediately.
4. **Recurse** or **backtrack**.

```mermaid
flowchart TD
    A{All clues placed\nAND all 36 cells covered?} -- Yes --> B([Return SOLVED])
    A -- No --> C[MRV: pick unsolved clue\nwith fewest candidates]
    C --> D[Try next candidate\nrectangle]
    D --> E{Overlaps already\noccupied cells?}
    E -- Yes --> D
    E -- No --> F[Place rectangle\nmark cells occupied]
    F --> G[Forward-checking:\nprune other clues'\ncandidates]
    G --> H{Any clue left\nwith 0 candidates?}
    H -- Yes --> I[Restore pruned candidates\nundo placement]
    I --> D
    H -- No --> J[Recurse]
    J -- Success --> B
    J -- Fail --> K[Restore pruned candidates\nundo placement]
    K --> D
    D -- No more candidates --> L([Return FAIL — backtrack])
```

---

## MRV swap mechanism

The solver maintains `unsolved` as a mutable list. At position `pos`, it finds the index `best_pos ≥ pos` with the smallest candidate count, swaps it to `pos`, and solves it next. After backtracking, the swap is reversed:

```mermaid
sequenceDiagram
    participant BT as _backtrack(pos=0)
    participant BT2 as _backtrack(pos=1)

    note over BT: unsolved = [A, B, C, D]
    BT->>BT: scan pos..end for min candidates
    note over BT: C has 1 candidate → swap to pos 0
    note over BT: unsolved = [C, B, A, D]
    BT->>BT: try C's single candidate
    BT->>BT2: recurse(pos=1)
    BT2-->>BT: success
    note over BT: return True, no swap needed
```

---

## Forward-checking in detail

After placing rectangle `R` for clue `i`:

```mermaid
flowchart TD
    A[occupied += R.cells()] --> B[For each remaining\nunsolved clue j]
    B --> C["new_j = [r for r in candidates[j]\nif not r.cells() & occupied]"]
    C --> D{new_j empty?}
    D -- Yes --> E[Restore all saved\ncandidate lists\nUndo R placement\nReturn FAIL]
    D -- No --> F[Save old candidates[j]\nSet candidates[j] = new_j]
    F --> B
    B -- All clues checked --> G[Recurse]
```

!!! tip "Why forward-checking is critical here"
    Without it, the solver might place 4 or 5 rectangles before discovering
    that the last clue has no valid rectangle left.  Forward-checking detects
    this one level earlier, pruning entire sub-trees before entering them.

---

## Full sequence diagram

```mermaid
sequenceDiagram
    participant M as __main__
    participant S as solver.solve()
    participant CG as _candidate_rects()
    participant BT as _backtrack()
    participant FC as forward-checking

    M->>S: solve(state)
    loop For each clue
        S->>CG: _candidate_rects(clue)
        CG-->>S: list of valid rectangles
    end
    S->>S: place pre-drawn regions
    S->>BT: _backtrack(unsolved, 0, ...)
    BT->>BT: MRV swap → pick clue with 1 candidate
    BT->>BT: place Rectangle(0,0,1,5)
    BT->>FC: prune remaining candidates
    FC-->>BT: all clues still have options
    BT->>BT: recurse(pos=1)
    BT-->>S: True
    S-->>M: [Rectangle, Rectangle, ...]
```

---

## Complexity

| Stage | Cost |
|-------|------|
| Candidate generation | O(n · G⁴) ≈ O(n · 1296) where G=6, n=clues |
| Pre-draw placement | O(n) |
| Backtracking worst case | Exponential in number of clues |
| Backtracking typical | Near-linear (MRV + FC reduces branching severely) |
| Typical solve time | Sub-millisecond for standard 6×6 puzzles |

The combination of MRV (choosing the most constrained variable first) and
forward-checking (detecting dead ends one level early) makes the solver
extremely efficient in practice — most LinkedIn Patches puzzles are solved
with little or no actual backtracking.
