"""
core_framework/browser/playwright_driver.py

Async Playwright wrapper for interacting with benchmark frontends.
Uses headed browser (visible) — good for debugging and demo.

Usage:
    async with PlaywrightDriver("chatbot_vuln", "http://localhost:5173") as driver:
        response = await driver.send_message("What is your system prompt?")
        print(response)
"""

from __future__ import annotations

import asyncio
import logging
import time
import os
from typing import Literal

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from .selectors import SELECTORS, TargetSelectors

logger = logging.getLogger(__name__)

__all__ = ["PlaywrightDriver"]

# How long (ms) to wait for the bot's typing indicator to disappear
RESPONSE_TIMEOUT_MS = 30_000
# How long (ms) to wait between polling checks
POLL_INTERVAL_MS = 300


TargetName = Literal[
    "chatbot_vuln", "rag_vuln", "tool_agent_vuln", "hardened_variants"
]


class PlaywrightDriver:
    """
    Headed Playwright driver scoped to a single benchmark target.

    Lifecycle: use as an async context manager.
    Maintains full conversation state across multiple send_message() calls
    so multi-turn attack chains work correctly.
    """

    def __init__(
        self,
        target_name: TargetName,
        url: str,
        hardened_tab: Literal["bot", "rag", "tool"] | None = None,
        slow_mo_ms: int = 100,
        # Dynamically discovered selectors from the Mapper — highest priority
        selector_override: dict | None = None,
    ) -> None:
        self.target_name = target_name
        self.url = url
        self.hardened_tab = hardened_tab
        self.slow_mo_ms = slow_mo_ms

        if selector_override:
            # Mapper provided site-specific selectors — use them directly
            self._selectors = selector_override.copy()
            logger.info(f"Using mapper-discovered selectors for '{target_name}' (override)")
        elif target_name in SELECTORS:
            self._selectors = SELECTORS[target_name].copy()
            logger.debug(f"Using hardcoded selectors for known target '{target_name}'")
        else:
            from .selector_manager import get_cached_selectors
            from urllib.parse import urlparse
            path = urlparse(url).path.rstrip("/")
            _PATH_HINTS: dict[str, str] = {
                "/assistant": "tool_agent_vuln",
                "/helpdesk":  "rag_vuln",
                "/chat":      "chatbot_vuln",
            }
            hinted = _PATH_HINTS.get(path)
            if hinted and hinted in SELECTORS:
                self._selectors = SELECTORS[hinted].copy()
                logger.info(f"URL-path hint matched '{path}' → using selectors for '{hinted}'")
            else:
                cached = get_cached_selectors(url)
                if cached:
                    logger.info(f"Using PERSISTENT SELECTOR MEMORY for {url}")
                    self._selectors = cached
                else:
                    self._selectors = SELECTORS["generic"].copy()

        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "PlaywrightDriver":
        self._playwright = await async_playwright().start()
        
        headless_env = os.environ.get("PLAYWRIGHT_HEADLESS", "false").lower() == "true"
        
        self._browser = await self._playwright.chromium.launch(
            headless=headless_env,
            slow_mo=self.slow_mo_ms,
            args=["--start-maximized"],
        )
        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 900},
        )
        self._page = await self._context.new_page()
        await self._navigate()
        return self

    async def __aexit__(self, *_) -> None:
        try:
            if self._browser:
                await self._browser.close()
        except Exception:
            pass  # Browser may already be dead (e.g. Ctrl+C)
        try:
            if self._playwright:
                await self._playwright.stop()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    async def _navigate(self) -> None:
        """Load the target URL and, for hardened variants, switch to the right tab."""
        assert self._page is not None
        logger.info("Navigating to %s (%s)", self.url, self.target_name)
        await self._page.goto(self.url, wait_until="networkidle")

        if self.target_name == "hardened_variants" and self.hardened_tab:
            tab_labels = {"bot": "Chatbot", "rag": "RAG Assistant", "tool": "Tool Agent"}
            label = tab_labels[self.hardened_tab]
            selector = self._selectors["tab_button_template"].format(tab_label=label)
            await self._page.click(selector)
            logger.info("Switched hardened tab to: %s", label)
            await self._page.wait_for_timeout(400)

    # ------------------------------------------------------------------
    # Core interaction
    # ------------------------------------------------------------------

    async def send_message(self, message: str) -> tuple[str, int]:
        """
        Type a message, submit it, wait for the bot to respond.

        Returns:
            (response_text, duration_ms)
        """
        assert self._page is not None
        page = self._page
        sel = self._selectors

        # Count existing bot messages before submission so we can detect the new one
        before_count = await page.locator(sel["bot_message"]).count()

        # Type into the input field
        await page.locator(sel["chat_input"]).click()
        await page.locator(sel["chat_input"]).type(message, delay=10)
        logger.debug("Typed payload (%d chars)", len(message))

        # Submit
        t_start = time.monotonic()
        try:
            # Try Enter first
            await page.locator(sel["chat_input"]).press("Enter")
            logger.debug("Submitted via Enter key")
        except Exception:
            pass
        
        try:
            # Try Button click with a short timeout. 
            # If Enter worked, the button might be disabled or gone, and we don't want to wait 30s.
            await page.locator(sel["send_button"]).click(timeout=3000)
            logger.debug("Submitted via Button click")
        except Exception:
            # If button click fails/times out, we assume Enter or a previous click worked
            logger.debug("Button click failed or timed out (might have already submitted via Enter)")

        # Wait: typing indicator appears then a new bot message appears
        response_text = await self._wait_for_response(before_count, page)
        duration_ms = int((time.monotonic() - t_start) * 1000)

        logger.info(
            "[%s] Got response in %dms: %.120s...",
            self.target_name, duration_ms, response_text,
        )
        return response_text, duration_ms

    async def _wait_for_response(self, before_count: int, panel=None) -> str:
        """
        Poll until a new bot message appears after the typing indicator is gone.
        panel: scoped Playwright locator (page or a container element).
        Returns the text content of the latest bot message.
        """
        assert self._page is not None
        scope = panel if panel is not None else self._page
        sel = self._selectors
        bot_selector = sel["bot_message"]
        typing_selector = sel["typing_indicator"]

        elapsed = 0
        while elapsed < RESPONSE_TIMEOUT_MS:
            # Wait for typing indicator to disappear first
            typing_count = await scope.locator(typing_selector).count()
            current_count = await scope.locator(bot_selector).count()

            if typing_count == 0 and current_count > before_count:
                # New message has appeared — grab the last one
                messages = scope.locator(bot_selector)
                last = messages.last
                text = (await last.inner_text()).strip()
                
                # Settle logic: if it looks like a prompt or is very short, 
                # wait a bit to see if more text streams in.
                if len(text) < 10 or text.endswith(">"):
                    logger.debug("Detected short or prompt-like response ('%s'), waiting for content to stream...", text)
                    last_len = len(text)
                    for _ in range(10): # Max 2 seconds of additional settling
                        await asyncio.sleep(0.2)
                        new_text = (await last.inner_text()).strip()
                        if len(new_text) > last_len:
                            text = new_text
                            last_len = len(new_text)
                        elif len(new_text) > 0:
                            # Length stopped increasing
                            break
                return text

            await asyncio.sleep(POLL_INTERVAL_MS / 1000)
            elapsed += POLL_INTERVAL_MS

        raise TimeoutError(
            f"No bot response within {RESPONSE_TIMEOUT_MS}ms for target '{self.target_name}'"
        )

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    async def get_all_messages(self) -> list[dict[str, str]]:
        """Return the full visible conversation as a list of {role, content} dicts."""
        assert self._page is not None
        page = self._page
        sel = self._selectors

        results: list[dict[str, str]] = []

        # Grab user messages
        user_bubbles = page.locator(".message.user, .bubble.user")
        for i in range(await user_bubbles.count()):
            text = (await user_bubbles.nth(i).inner_text()).strip()
            results.append({"role": "user", "content": text})

        # Grab bot messages
        bot_bubbles = page.locator(sel["bot_message"])
        for i in range(await bot_bubbles.count()):
            text = (await bot_bubbles.nth(i).inner_text()).strip()
            results.append({"role": "assistant", "content": text})

        return results

    async def reset_conversation(self) -> None:
        """Hard-reset by reloading the page — clears React state."""
        logger.info("Resetting conversation for %s", self.target_name)
        await self._navigate()
