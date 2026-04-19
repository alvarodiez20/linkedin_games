# Browser Setup

The solvers connect to Chrome via the [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/) (CDP). You must launch Chrome with remote debugging enabled **before** running a solver.

## macOS

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.chrome-debug-profile"
```

## Linux

```bash
google-chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.chrome-debug-profile"
```

## Windows

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --remote-debugging-port=9222 `
  --user-data-dir="$env:USERPROFILE\.chrome-debug-profile"
```

## After launching

1. Navigate to [linkedin.com](https://www.linkedin.com) and log in.
2. You do **not** need to open the game page — the solver opens it automatically.
3. Run a solver: `sudoku`, `tango`, or `patches`.

!!! tip "Custom CDP URL"
    If Chrome is running on a different host or port, set the `CDP_URL` environment variable:
    ```bash
    CDP_URL=http://localhost:9333 sudoku
    ```
