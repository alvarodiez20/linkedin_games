# Games

| Game | Puzzle type | Algorithm | Grid | Status |
|------|-------------|-----------|------|--------|
| [Mini Sudoku](sudoku/overview.md) | Number placement | Backtracking + MRV | 6×6 | ✅ |
| [Tango](tango/overview.md) | Binary constraint | Constraint propagation + Backtracking | 6×6 | ✅ |
| [Patches](patches/overview.md) | Rectangle packing | CSP + Forward-checking + MRV | 6×6 | ✅ |

Each game page is organised into three sections:

- **Overview** — rules and what the puzzle looks like
- **Algorithm** — how the solver works, with pseudocode and complexity analysis
- **DOM Extraction** — how the extractor reads the puzzle state from LinkedIn's live DOM
