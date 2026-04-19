"""
Runtime configuration for linkedin-games solvers.

All values can be overridden via environment variables.
"""

from __future__ import annotations

import os

# --- Browser ---
CDP_URL: str = os.getenv("CDP_URL", "http://localhost:9222")

# --- Timing (seconds) ---
# Min/max random delay between individual cell inputs
INPUT_DELAY_MIN: float = float(os.getenv("INPUT_DELAY_MIN", "0.20"))
INPUT_DELAY_MAX: float = float(os.getenv("INPUT_DELAY_MAX", "0.50"))

# Delay between patches (longer drag gestures)
PATCH_DELAY_MIN: float = float(os.getenv("PATCH_DELAY_MIN", "0.30"))
PATCH_DELAY_MAX: float = float(os.getenv("PATCH_DELAY_MAX", "0.60"))

# Delay between cells during a drag
DRAG_CELL_DELAY: float = float(os.getenv("DRAG_CELL_DELAY", "0.03"))

# How long to wait for the game board to appear in the DOM
BOARD_TIMEOUT_MS: int = int(os.getenv("BOARD_TIMEOUT_MS", "15000"))
