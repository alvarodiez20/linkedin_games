"""
Shared browser connection logic.

Connects to an already-running Chrome instance via CDP (Chrome DevTools Protocol)
on localhost:9222. This avoids any login / anti-bot issues because the human user
has already authenticated in that browser session.
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from typing import Generator

from playwright.sync_api import Browser, Page, sync_playwright

CDP_URL = "http://localhost:9222"


@contextmanager
def connect_to_chrome(cdp_url: str = CDP_URL) -> Generator[Browser, None, None]:
    """
    Context manager that yields a Playwright ``Browser`` handle connected
    to an existing Chrome instance via CDP.

    Usage::

        with connect_to_chrome() as browser:
            page = find_tab(browser, "linkedin.com/games/sudoku")
            ...
    """
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.connect_over_cdp(cdp_url)
        except Exception as exc:
            print(
                "\n❌  Could not connect to Chrome on %s.\n"
                "    Make sure Chrome is running with:\n\n"
                '      /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\\n'
                '        --remote-debugging-port=9222 \\\n'
                '        --user-data-dir="$HOME/.chrome-debug-profile"\n',
                cdp_url,
                file=sys.stderr,
            )
            raise SystemExit(1) from exc
        yield browser


def find_tab(browser: Browser, url_substring: str) -> Page:
    """
    Return the first browser tab whose URL contains *url_substring*.

    If no matching tab is found, opens a new tab and navigates to the URL.
    """
    for context in browser.contexts:
        for page in context.pages:
            if url_substring in page.url:
                try:
                    page.bring_to_front()
                except Exception:
                    pass
                return page

    # No tab found, let's open one
    print(f"\n🌐  Opening new tab for {url_substring} …")
    context = browser.contexts[0] if browser.contexts else browser.new_context()
    page = context.new_page()
    full_url = f"https://www.{url_substring}" if not url_substring.startswith("http") else url_substring
    page.goto(full_url)
    return page
