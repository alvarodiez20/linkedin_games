# Development Setup

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- Google Chrome

## Install all dev tools

```bash
uv sync --extra dev
uv run pre-commit install
uv run playwright install chromium
```

## Common tasks

```bash
make lint        # ruff check (linting)
make format      # ruff format (auto-format)
make typecheck   # mypy
make test        # pytest
make test-cov    # pytest with coverage report
```

## Environment variables

All runtime settings can be overridden without editing code:

| Variable | Default | Description |
|----------|---------|-------------|
| `CDP_URL` | `http://localhost:9222` | Chrome DevTools Protocol endpoint |
| `INPUT_DELAY_MIN` | `0.20` | Min seconds between cell inputs |
| `INPUT_DELAY_MAX` | `0.50` | Max seconds between cell inputs |
| `BOARD_TIMEOUT_MS` | `15000` | Max ms to wait for game board to load |

See `linkedin_games/config.py` for the full list.
