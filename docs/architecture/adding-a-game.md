# Adding a New Game

Follow this guide to add a solver for a new LinkedIn game.

## 1. Create the package

```bash
mkdir linkedin_games/<game>
touch linkedin_games/<game>/__init__.py
```

## 2. Implement `extractor.py`

```python
# linkedin_games/<game>/extractor.py
from dataclasses import dataclass
from playwright.sync_api import Page

@dataclass
class <Game>State:
    # fields representing the puzzle

def extract_state(page: Page) -> <Game>State:
    # query the DOM and return a <Game>State
    ...
```

Tips:
- Use `page.wait_for_selector(selector, timeout=15000)` before querying.
- Check if the game uses an `<iframe>` (like Sudoku) or the main frame (like Tango/Patches).
- Inspect the live DOM in Chrome DevTools to find stable selectors.

## 3. Implement `solver.py`

```python
# linkedin_games/<game>/solver.py
from typing import Optional
from linkedin_games.<game>.extractor import <Game>State

def solve(state: <Game>State) -> Optional[<SolutionType>]:
    # pure algorithm, no Playwright dependency
    ...
```

**Keep the solver pure.** No `print()`, no Playwright, no side effects. This makes it trivially unit-testable.

## 4. Implement `player.py`

```python
# linkedin_games/<game>/player.py
from playwright.sync_api import Page
from linkedin_games.<game>.extractor import <Game>State

def play_solution(page: Page, state: <Game>State, solution: ...) -> None:
    # simulate clicks/drags to enter the solution
    ...
```

## 5. Implement `__main__.py`

```python
# linkedin_games/<game>/__main__.py
from linkedin_games.browser import connect_and_open
from linkedin_games.<game>.extractor import extract_state
from linkedin_games.<game>.solver import solve
from linkedin_games.<game>.player import play_solution

GAME_URL = "https://www.linkedin.com/games/<game>/"

def main() -> None:
    page = connect_and_open(GAME_URL)
    state = extract_state(page)
    solution = solve(state)
    if solution is None:
        raise SystemExit("No solution found")
    play_solution(page, state, solution)
```

## 6. Register the CLI entry point

In `pyproject.toml`:

```toml
[project.scripts]
<game> = "linkedin_games.<game>.__main__:main"
```

## 7. Write tests

```bash
mkdir tests/<game>
touch tests/<game>/__init__.py
touch tests/<game>/test_solver.py
```

Test the solver with known puzzles and edge cases. No Playwright needed — solvers are pure Python.

## 8. Document

Add pages under `docs/games/<game>/`: `overview.md`, `algorithm.md`, `dom-extraction.md`.
Register them in `mkdocs.yml` under the `Games` nav section.
