# Architecture Overview

Every game solver follows the same **three-module pattern**:

```
linkedin_games/
└── <game>/
    ├── extractor.py   # DOM → Python data structure
    ├── solver.py      # Pure algorithm (no I/O)
    ├── player.py      # Python data structure → browser input
    └── __main__.py    # Orchestration
```

## Module responsibilities

### `extractor.py`

Connects to the live browser via Playwright, queries the DOM, and returns a pure Python data structure representing the current puzzle state. No solving happens here.

### `solver.py`

A **pure function** — takes the puzzle state, returns a solution (or `None`). Has zero dependencies on Playwright or any I/O. This isolation makes solvers easy to unit test.

### `player.py`

Takes the solution and a Playwright `Page`/`Frame` reference. Simulates realistic mouse/keyboard events to fill in the answer. Random delays are injected between inputs.

### `__main__.py`

Orchestrates the full flow:

```python
def main():
    page = connect_to_browser()      # browser.py
    state = extract_state(page)      # extractor.py
    solution = solve(state)          # solver.py
    validate_solution(solution)      # solver.py
    play_solution(page, solution)    # player.py
```

## Shared utilities

- `linkedin_games/browser.py` — CDP connection and tab management
- `linkedin_games/config.py` — envvar-based runtime configuration
