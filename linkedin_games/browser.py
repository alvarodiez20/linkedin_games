"""
Shared browser connection logic.

Connects to an already-running Chrome instance via CDP (Chrome DevTools Protocol).
This avoids login / anti-bot issues because the user has already authenticated
in that browser session.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

from playwright.sync_api import Browser, Page, sync_playwright

from linkedin_games.config import CDP_URL

logger = logging.getLogger(__name__)


@contextmanager
def connect_to_chrome(cdp_url: str = CDP_URL) -> Generator[Browser, None, None]:
    """Context manager that yields a Playwright ``Browser`` connected via CDP.

    Connects to an **existing** Chrome process rather than launching a new one,
    so the user's LinkedIn session is already active.

    Args:
        cdp_url: The Chrome DevTools Protocol endpoint.  Defaults to the
            ``CDP_URL`` setting (``http://localhost:9222`` unless overridden
            by the ``CDP_URL`` environment variable).

    Yields:
        A connected ``playwright.sync_api.Browser`` handle.

    Raises:
        SystemExit: If the CDP connection fails (e.g. Chrome is not running
            with ``--remote-debugging-port``).

    Example:
        >>> with connect_to_chrome() as browser:
        ...     page = find_tab(browser, "linkedin.com/games/sudoku")
    """
    with sync_playwright() as pw:
        try:
            logger.debug("Connecting to Chrome via CDP at %s", cdp_url)
            browser = pw.chromium.connect_over_cdp(cdp_url)
            logger.info("Connected to Chrome at %s", cdp_url)
        except Exception as exc:
            logger.error(
                "Could not connect to Chrome on %s. "
                "Make sure Chrome is running with: "
                "/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome "
                "--remote-debugging-port=9222 "
                "--user-data-dir=\"$HOME/.chrome-debug-profile\"",
                cdp_url,
            )
            raise SystemExit(1) from exc
        yield browser


def find_tab(browser: Browser, url_substring: str) -> Page:
    """Return the first browser tab whose URL contains *url_substring*.

    Searches all browser contexts and pages.  If a matching tab is found it
    is brought to the front.  If no tab matches, a new tab is opened and
    navigated to the URL.

    Args:
        browser: A connected Playwright ``Browser`` handle.
        url_substring: Substring to search for in tab URLs (e.g.
            ``"linkedin.com/games/tango"``).  If it does not start with
            ``"http"`` the prefix ``"https://www."`` is prepended when
            opening a new tab.

    Returns:
        The matching (or newly opened) ``playwright.sync_api.Page``.
    """
    for context in browser.contexts:
        for page in context.pages:
            if url_substring in page.url:
                logger.debug("Found existing tab: %s", page.url)
                try:
                    page.bring_to_front()
                except Exception:
                    pass
                return page

    logger.info("No existing tab found for %s — opening a new one", url_substring)
    context = browser.contexts[0] if browser.contexts else browser.new_context()
    page = context.new_page()
    full_url = (
        f"https://www.{url_substring}"
        if not url_substring.startswith("http")
        else url_substring
    )
    page.goto(full_url)
    logger.debug("Navigated new tab to %s", full_url)
    return page
