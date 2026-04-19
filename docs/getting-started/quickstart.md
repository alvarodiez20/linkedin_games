# Quickstart

This guide gets you from zero to a solved puzzle in under 5 minutes.

## 1. Install

```bash
uv sync && uv run playwright install chromium
```

## 2. Launch Chrome with remote debugging

=== "macOS"
    ```bash
    /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
      --remote-debugging-port=9222 \
      --user-data-dir="$HOME/.chrome-debug-profile"
    ```

=== "Linux"
    ```bash
    google-chrome --remote-debugging-port=9222 --user-data-dir="$HOME/.chrome-debug-profile"
    ```

=== "Windows"
    ```powershell
    & "C:\Program Files\Google\Chrome\Application\chrome.exe" `
      --remote-debugging-port=9222 --user-data-dir="$env:USERPROFILE\.chrome-debug-profile"
    ```

## 3. Log in to LinkedIn

Open `linkedin.com` in the browser you just launched and sign in.

## 4. Run a solver

```bash
sudoku    # or: tango  /  patches
```

The solver will:

1. Connect to Chrome via CDP
2. Find or open the LinkedIn game tab
3. Extract the puzzle state from the DOM
4. Solve the puzzle
5. Validate the solution
6. Play the moves back into the browser

!!! note
    The solver adds small random delays between inputs to mimic human interaction.
