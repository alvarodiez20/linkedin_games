# Testing

## Running tests

```bash
make test          # run all tests
make test-cov      # run with coverage report
uv run pytest tests/sudoku/  # run a single game's tests
```

## Test structure

```
tests/
├── sudoku/
│   └── test_solver.py   # backtracking, MRV, candidate logic, validation
├── tango/
│   └── test_solver.py   # propagation, backtracking, local validity, validation
└── patches/
    └── test_solver.py   # Rectangle, shape constraints, candidate gen, full solve
```

## What is tested

Solver modules are **pure Python** — no browser, no Playwright. Tests run entirely offline.

Each test file covers:

- `solve()` — returns correct solution for known puzzles
- `solve()` — returns `None` for unsolvable inputs
- `solve()` — does not mutate the input
- Core sub-functions (candidate generation, constraint checks, propagation)
- `validate_solution()` — accepts valid solutions, rejects invalid ones

## What is NOT tested

DOM extraction (`extractor.py`) and input automation (`player.py`) require a live browser and are not covered by automated tests. Manual testing against the live LinkedIn games verifies these.

## Adding tests for a new game

1. Create `tests/<game>/test_solver.py`.
2. Import from `linkedin_games.<game>.solver` only (no Playwright imports).
3. Write at least: a solvable-puzzle test, an unsolvable-puzzle test, and a validation test.
