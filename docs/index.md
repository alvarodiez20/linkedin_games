# LinkedIn Games Solver

Automated solvers for LinkedIn's daily puzzle games. Each solver connects to a running Chrome instance, reads the puzzle from the DOM, computes a solution, and plays it back into the browser.

```
sudoku    # solve today's Mini Sudoku
tango     # solve today's Tango
patches   # solve today's Patches
```

## Games supported

| Game | Algorithm | Status |
|------|-----------|--------|
| [Mini Sudoku](games/sudoku/overview.md) | Backtracking + MRV | ✅ |
| [Tango](games/tango/overview.md) | Constraint propagation + Backtracking + MRV | ✅ |
| [Patches](games/patches/overview.md) | CSP + Forward-checking + MRV | ✅ |

## Quick start

```bash
# 1. Install
uv sync

# 2. Launch Chrome with remote debugging
google-chrome --remote-debugging-port=9222 --user-data-dir="$HOME/.chrome-debug-profile"

# 3. Log in to LinkedIn, then run a solver
sudoku
```

See [Getting Started](getting-started/installation.md) for full setup instructions.
