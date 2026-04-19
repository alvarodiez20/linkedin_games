# LinkedIn Games Solver

Automated solvers for LinkedIn's daily puzzle games using Python + Playwright.

> **Note:** This project connects to an already-running Chrome instance. It does **not** attempt to log in — you handle authentication manually.

## Supported Games

| Game | Status |
|------|--------|
| Mini Sudoku (6×6) | ✅ Ready |
| Tango (Sun/Moon) | ✅ Ready |
| Patches (Shikaku) | ✅ Ready |

## Prerequisites

- Python 3.10+
- Google Chrome
- A LinkedIn account (logged in manually)

## Installation

```bash
cd /path/to/linkedin_games

# Install dependencies (creates venv automatically)
uv sync

# Install Playwright's Chromium browser binaries (one-time)
uv run playwright install chromium
```

## Usage

### Step 1 — Launch Chrome with Remote Debugging

> ⚠️ **Close ALL existing Chrome windows first**, then run:

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

### Step 2 — Log in

1. In the Chrome window that opens, log in to **linkedin.com**.
2. The solver will automatically navigate to the game page if it is not already open.

### Step 3 — Run the Solver

```bash
# Solve today's Mini Sudoku
uv run python -m linkedin_games.sudoku

# Solve today's Tango
uv run python -m linkedin_games.tango

# Solve today's Patches
uv run python -m linkedin_games.patches
```

## Project Structure

```
linkedin_games/
├── pyproject.toml          # Project config & dependencies (uv)
├── linkedin_games/
│   ├── __init__.py
│   ├── browser.py          # Shared browser connection logic
│   ├── sudoku/
│   │   ├── __init__.py
│   │   ├── __main__.py     # Entry point
│   │   ├── extractor.py    # DOM → 2D grid state extraction
│   │   ├── solver.py       # Backtracking solver for 6×6 Sudoku
│   │   └── player.py       # Automated input via Playwright
│   └── tango/
│       ├── __init__.py
│       ├── __main__.py     # Entry point
│       ├── extractor.py    # DOM → state extraction (cells + constraints)
│       ├── solver.py       # Constraint propagation + backtracking
│       └── player.py       # Click-to-cycle input
│   └── patches/
│       ├── __init__.py
│       ├── __main__.py     # Entry point
│       ├── extractor.py    # DOM → shape/size constraints extraction
│       ├── solver.py       # Contraint-satisfaction backtracking
│       └── player.py       # Mouse-drag input
└── ... (future games)
```

## Adding a New Game

1. Create a new package under `linkedin_games/` (e.g., `linkedin_games/queens/`).
2. Implement three modules: `extractor.py`, `solver.py`, `player.py`.
3. Add a `__main__.py` entry point that ties them together.
4. Reuse `linkedin_games.browser` for the Chrome connection.

## License

MIT — use responsibly.
