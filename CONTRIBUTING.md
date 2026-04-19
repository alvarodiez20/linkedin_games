# Contributing

## Setup

```bash
git clone https://github.com/your-org/linkedin-games
cd linkedin-games
uv sync --extra dev
uv run pre-commit install
uv run playwright install chromium
```

## Development workflow

```bash
make lint        # ruff check
make format      # ruff format
make typecheck   # mypy
make test        # pytest
make test-cov    # pytest + coverage report
```

All four checks run in CI on every push and pull request.

## Adding a new game

Each game lives in `linkedin_games/<game>/` and follows the same three-module pattern:

| Module | Responsibility |
|--------|---------------|
| `extractor.py` | Parse the puzzle state from the live DOM via Playwright |
| `solver.py` | Pure algorithm — no I/O, no Playwright dependency |
| `player.py` | Automate browser input to enter the solution |
| `__main__.py` | Orchestrate: connect → extract → solve → validate → play |

Steps:

1. Create `linkedin_games/<game>/` with the four modules above.
2. Add a CLI entry point in `pyproject.toml` under `[project.scripts]`.
3. Add unit tests in `tests/<game>/test_solver.py` (solver must be pure Python — no browser needed).
4. Document the game and its algorithm under `docs/games/<game>/`.

## Commit style

Use conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `chore:`.

## Pull requests

- Keep PRs focused on one concern.
- All CI checks must pass before merge.
- Add or update tests for any solver change.
