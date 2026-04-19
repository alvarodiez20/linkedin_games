# Browser Automation

The solvers use [Playwright](https://playwright.dev/python/) in **synchronous mode**, connected to a user-launched Chrome instance via the Chrome DevTools Protocol (CDP).

## Why CDP instead of launching a new browser?

CDP connects to an **existing** Chrome session where the user is already logged in to LinkedIn. Launching a fresh browser would require automating the login flow, which is fragile and against LinkedIn's terms of service.

## Connection flow

```python
# linkedin_games/browser.py
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    context = browser.contexts[0]
    page = find_or_open_game_tab(context, game_url)
```

## Tab management

`browser.py` scans existing tabs for one whose URL matches the target game. If found, it navigates to it. If not, it opens a new tab.

## Input simulation

Each `player.py` uses a different input strategy depending on the game's interaction model:

| Game | Interaction | API used |
|------|-------------|----------|
| Sudoku | Click cell → click number button | `locator.click()` |
| Tango | Click to cycle Sun → Moon → Empty | `page.mouse.click()` |
| Patches | Mouse drag through cells | `page.mouse.move()` / `page.mouse.down()` |

All interactions use **native browser events** (not injected JavaScript) to ensure React synthetic event handlers fire correctly.

## Timing

Random delays between inputs (configurable via `config.py`) reduce the risk of rate limiting and make the interaction look human.
