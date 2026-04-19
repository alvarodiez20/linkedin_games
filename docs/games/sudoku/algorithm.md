# Mini Sudoku — Algorithm

**Source:** `linkedin_games/sudoku/solver.py`

## Approach: Backtracking + MRV

The solver uses **recursive backtracking** with the **Minimum Remaining Values (MRV)** heuristic.

### Constraint model

| Component | Description |
|-----------|-------------|
| Variables | Each empty cell |
| Domain | {1, 2, 3, 4, 5, 6} |
| Constraints | Row uniqueness, column uniqueness, 2×3 box uniqueness |

### MRV heuristic

Instead of filling cells left-to-right, MRV picks the empty cell with the **fewest legal values** remaining. This reduces the branching factor early and dramatically cuts the search tree.

!!! tip "Why MRV works well here"
    A cell with only one legal value is a forced assignment — no branching at all.
    Choosing it first propagates the most information before we explore alternatives.

### Pseudocode

```
function solve(board):
    cell = find_cell_with_fewest_candidates(board)  # MRV
    if cell is None:
        return board  # all cells filled → solved

    for value in candidates(board, cell):
        board[cell] = value
        if solve(board) succeeds:
            return board
        board[cell] = 0  # backtrack

    return UNSOLVABLE
```

### Candidate computation

```python
def _candidates(board, row, col):
    used = set(board[row])          # row constraint
    used |= {board[r][col] for r in range(6)}  # column constraint
    box_r, box_c = (row // 2) * 2, (col // 3) * 3
    for r in range(box_r, box_r + 2):
        for c in range(box_c, box_c + 3):
            used.add(board[r][c])   # sub-grid constraint
    return sorted({1,2,3,4,5,6} - used)
```

### Complexity

| | |
|---|---|
| Worst case | O(6^m) where m = number of empty cells |
| Typical case | Much faster due to MRV pruning |
| Space | O(m) call stack depth |

For a 6×6 grid with ~20 empty cells, the solver completes in well under 1 ms in practice.
