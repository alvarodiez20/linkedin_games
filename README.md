# LinkedIn Games Solver

<div align="center">

[![CI](https://github.com/alvarodiez20/linkedin_games/actions/workflows/ci.yml/badge.svg)](https://github.com/alvarodiez20/linkedin_games/actions/workflows/ci.yml)
[![Docs](https://github.com/alvarodiez20/linkedin_games/actions/workflows/docs.yml/badge.svg)](https://github.com/alvarodiez20/linkedin_games/actions/workflows/docs.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

</div>

Automated solvers for LinkedIn's daily puzzle games using **Python + Playwright**.  
Each solver connects to your already-running Chrome session — no login automation, no anti-bot risk.

---

## Supported Games

| Game | Description | Status |
|------|-------------|--------|
| **Mini Sudoku** | Classic 6×6 Sudoku | ✅ Ready |
| **Tango** | Sun/Moon constraint grid | ✅ Ready |
| **Patches** | Rectangle-packing (Shikaku variant) | ✅ Ready |
| **Queens** | Colour-region N-Queens with adjacency constraint | ✅ Ready |

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.10+ |
| Google Chrome | Any recent version |
| [uv](https://github.com/astral-sh/uv) | Latest |

You also need a **LinkedIn account** already logged in to Chrome.

---

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/alvarodiez20/linkedin_games.git
cd linkedin_games

# 2. Install dependencies (creates .venv automatically)
uv sync

# 3. Install Playwright browser binaries (one-time)
uv run playwright install chromium
```

---

## Usage

### Step 1 — Launch Chrome with Remote Debugging

> ⚠️ **Close ALL existing Chrome windows first**, then run one of:

```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.chrome-debug-profile"
```

```powershell
# Windows
& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --remote-debugging-port=9222 `
  --user-data-dir="$env:USERPROFILE\.chrome-debug-profile"
```

```bash
# Linux
google-chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.chrome-debug-profile"
```

### Step 2 — Log in to LinkedIn

In the Chrome window that opens, sign in to **linkedin.com**.  
The solver navigates to the game automatically if the tab isn't already open.

### Step 3 — Run a Solver

```bash
# Solve today's Mini Sudoku
uv run python -m linkedin_games.sudoku

# Solve today's Tango
uv run python -m linkedin_games.tango

# Solve today's Patches
uv run python -m linkedin_games.patches

# Solve today's Queens
uv run python -m linkedin_games.queens
```

All commands are also available as installed scripts after `uv sync`:

```bash
sudoku | tango | patches | queens
```

---

## Project Structure

```
linkedin_games/
├── pyproject.toml              # Project config & dependencies (uv)
├── mkdocs.yml                  # Documentation config
├── .github/workflows/
│   ├── ci.yml                  # CI: lint, typecheck, test, docs build
│   └── docs.yml                # Deploy MkDocs to GitHub Pages
├── docs/                       # MkDocs source
│   ├── games/                  # Per-game: overview, algorithm, DOM extraction
│   ├── architecture/           # Browser automation & adding new games
│   ├── reference/              # Auto-generated API reference
│   └── development/            # Setup, testing, contributing, changelog
├── tests/
│   ├── patches/test_solver.py  # 29 solver unit tests
│   ├── queens/test_solver.py   # 32 solver unit tests
│   ├── sudoku/test_solver.py
│   └── tango/test_solver.py
└── linkedin_games/
    ├── browser.py              # Shared CDP connection logic
    ├── config.py               # Configuration (CDP_URL, etc.)
    ├── sudoku/
    │   ├── extractor.py        # DOM → 6×6 grid
    │   ├── solver.py           # Backtracking Sudoku solver
    │   └── player.py           # Click-to-fill input
    ├── tango/
    │   ├── extractor.py        # DOM → grid + edge constraints
    │   ├── solver.py           # Constraint propagation + backtracking
    │   └── player.py           # Click-to-cycle (☀/🌙) input
    ├── patches/
    │   ├── extractor.py        # DOM → shape/size clues (dynamic grid size)
    │   ├── solver.py           # CSP backtracking with MRV + forward checking
    │   └── player.py           # Mouse-drag input
    └── queens/
        ├── extractor.py        # DOM → colour map (3-strategy detection)
        ├── solver.py           # Row-by-row backtracking (col+colour+adjacency)
        └── player.py           # Double-click to place queens
```

---

## Development

```bash
# Install development dependencies
uv sync --extra dev

# Run all tests
uv run python -m pytest

# Run tests with coverage
uv run python -m pytest --cov=linkedin_games --cov-report=term-missing

# Lint & format
uv run ruff check .
uv run ruff format .

# Type check
uv run mypy linkedin_games/

# Serve docs locally
uv run mkdocs serve
```

---

## How it Works

Every solver follows the same three-step pipeline:

```
┌─────────────────────────────────────────────────────────┐
│  1. EXTRACT  │  Read puzzle state from the live DOM     │
│  2. SOLVE    │  Run a pure-Python constraint solver     │
│  3. PLAY     │  Simulate browser input via Playwright   │
└─────────────────────────────────────────────────────────┘
```

The Chrome connection uses the **Chrome DevTools Protocol (CDP)** — the solver
attaches to your existing, logged-in Chrome instance rather than launching a
new one, entirely sidestepping authentication challenges.

---

## Adding a New Game

1. Create a package: `linkedin_games/<game>/`
2. Implement `extractor.py` → reads DOM state into a dataclass.
3. Implement `solver.py` → pure Python, no browser dependency.
4. Implement `player.py` → uses `page.mouse` / `page.click` to input solution.
5. Add `__main__.py` tying the three together.
6. Register in `pyproject.toml` under `[project.scripts]`.
7. Add tests under `tests/<game>/`.
8. Add docs under `docs/games/<game>/`.

See [Architecture → Adding a Game](docs/architecture/adding-a-game.md) for details.

---

## License

MIT — use responsibly. LinkedIn's Terms of Service apply; this tool is intended
for personal, educational use only.
