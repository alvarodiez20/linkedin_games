# Installation

## Requirements

- Python 3.10 or later
- [uv](https://docs.astral.sh/uv/) package manager
- Google Chrome (for browser automation)

## Install

```bash
git clone https://github.com/your-org/linkedin-games
cd linkedin-games
uv sync
uv run playwright install chromium
```

This installs all runtime dependencies and downloads the Playwright-managed Chromium binary used for CDP communication.

## Optional extras

```bash
# Development tools (ruff, mypy, pytest)
uv sync --extra dev

# Documentation tools (mkdocs-material, mkdocstrings)
uv sync --extra docs
```
