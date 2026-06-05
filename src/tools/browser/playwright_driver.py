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
            # NOTE: /assistant path-hint removed — the old tool_agent_vuln Tailwind app
            # that used div.text-indigo-400 selectors has been deleted. Keeping the hint
            # causes stale selectors to fire on any real app at /assistant.
            # The runtime fallback-probe in _wait_for_response will discover the real
            # bot_message selector automatically.
            _PATH_HINTS: dict[str, str] = {
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
        self.network_traces: list[dict] = []

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
        
        async def _log_response(response):
            if response.request.resource_type in ["fetch", "xhr"]:
                try:
                    if response.status == 200:
                        content_type = response.headers.get("content-type", "").lower()
                        # Limit to avoid blocking on huge files / media
                        content_length = int(response.headers.get("content-length", 0))
                        if content_length > 1024000: # 1MB limit
                            return
                        
                        body = None
                        if "application/json" in content_type:
                            body = await response.json()
                        elif "text/" in content_type or "javascript" in content_type:
                            body_text = await response.text()
                            if len(body_text) < 10000:
                                body = body_text
                                
                        if body:
                            self.network_traces.append({
                                "url": response.url,
                                "method": response.request.method,
                                "body": body
                            })
                except Exception:
                    pass
        
        def _log_websocket(ws):
            url = ws.url
            def _on_frame_received(payload):
                try:
                    if isinstance(payload, bytes):
                        text = payload.decode("utf-8", errors="ignore")
                    else:
                        text = str(payload)
                    if 0 < len(text) < 20000:
                        self.network_traces.append({
                            "url": url,
                            "method": "WS_RECV",
                            "body": text
                        })
                except Exception:
                    pass
            def _on_frame_sent(payload):
                try:
                    if isinstance(payload, bytes):
                        text = payload.decode("utf-8", errors="ignore")
                    else:
                        text = str(payload)
                    if 0 < len(text) < 20000:
                        self.network_traces.append({
                            "url": url,
                            "method": "WS_SENT",
                            "body": text
                        })
                except Exception:
                    pass
            ws.on("framereceived", _on_frame_received)
            ws.on("framesent", _on_frame_sent)

        self._page.on("response", _log_response)
        self._page.on("websocket", _log_websocket)
        
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
        # Use domcontentloaded — avoids hanging on sites with continuous background
        # polling (ChatGPT, Gemini) that never reach networkidle.
        # Then attempt a short networkidle settle as best-effort for slower apps.
        await self._page.goto(self.url, wait_until="domcontentloaded", timeout=30000)
        try:
            await self._page.wait_for_load_state("networkidle", timeout=3000)
        except Exception:
            pass  # Expected on ChatGPT / Gemini — proceed with whatever is rendered

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
        Uses .first on every locator to avoid Playwright strict-mode violations
        when the selector matches multiple elements (e.g. ChatGPT's dual textarea+div).

        Returns:
            (response_text, duration_ms)
        """
        assert self._page is not None
        page = self._page
        sel = self._selectors

        # Count existing bot messages before submission so we can detect the new one
        before_count = await page.locator(sel["bot_message"]).count()

        # Always use .first — avoids strict mode crash when selector matches 2-3 elements
        input_loc = page.locator(sel["chat_input"]).first

        # Click to focus
        await input_loc.click()

        # Try .fill() first (works on textarea, input, contenteditable=plaintext-only)
        # Fall back to .type() for ProseMirror / rich contenteditable divs
        try:
            await input_loc.fill(message)
        except Exception:
            await input_loc.type(message, delay=10)

        logger.debug("Typed payload (%d chars)", len(message))

        # Submit
        t_start = time.monotonic()
        try:
            await input_loc.press("Enter")
            logger.debug("Submitted via Enter key")
        except Exception:
            pass

        try:
            await page.locator(sel["send_button"]).first.click(timeout=3000)
            logger.debug("Submitted via Button click")
        except Exception:
            logger.debug("Button click failed or timed out (Enter likely worked)")

        # Wait for bot response
        response_text = await self._wait_for_response(before_count, page)
        
        # Guard: if response is empty, suspiciously short, or is just the
        # typing indicator's dot animation ('...' / '• • •' / similar),
        # don't accept it — mark as no-response.
        _is_typing_artifact = (
            not response_text
            or len(response_text.strip()) < 15
            or all(c in ".•· \u2022\u00b7" for c in response_text.strip())
        )
        if _is_typing_artifact:
            response_text = "[AEGIS_NO_RESPONSE: Bot returned empty response — result invalid]"
            
        duration_ms = int((time.monotonic() - t_start) * 1000)

        logger.info(
            "[%s] Got response in %dms: %.120s...",
            self.target_name, duration_ms, response_text,
        )

        return response_text, duration_ms

    async def _wait_for_response(self, before_count: int, panel=None) -> str:
        """
        Poll until a new bot message appears after the typing indicator is gone.
        Includes fallback detection when bot_message selector matches nothing —
        common when cached selectors are stale for a target site.
        """
        assert self._page is not None
        scope = panel if panel is not None else self._page
        sel = self._selectors
        bot_selector    = sel["bot_message"]
        typing_selector = sel["typing_indicator"]

        # Broad fallback selectors tried when bot_message never matches.
        # Ordered from most specific to most general.
        _FALLBACK_BOT_SELECTORS = [
            # LLM chat-specific elements
            "model-response p", "model-response", ".model-response-text",
            "[data-message-author-role='assistant'] p",
            "[data-message-author-role='assistant']",
            "[data-role='assistant']",
            # Markdown / prose renderers
            ".markdown p", ".markdown", "[class*='prose'] p",
            ".agent-turn p", ".response-content p",
            "message-content p", "message-content",
            # Class-name patterns
            "[class*='response'] p", "[class*='message'] p",
            "[class*='assistant'] p", "[class*='assistant']",
            "[class*='bot-message']", "[class*='bot_message']",
            ".ai-message", ".chat-message.assistant",
            # Tailwind flex-based layouts (tool-agent style)
            "div.text-indigo-400 > div.flex-1",
            "div.flex.gap-3.text-indigo-400 > div.flex-1",
            "div.text-indigo-400 > div",
            "div.justify-start > div",
            "div.flex.gap-3 > div",
            # Streamlit
            "[data-testid='stChatMessage']",
        ]


        elapsed          = 0
        selector_probed  = False  # whether we've tried fallback selectors yet

        while elapsed < RESPONSE_TIMEOUT_MS:
            typing_count  = await scope.locator(typing_selector).count()
            current_count = await scope.locator(bot_selector).count()

            # ── Happy path: selector is working ──────────────────────────────
            if typing_count == 0 and current_count > before_count:
                messages = scope.locator(bot_selector)
                last     = messages.last
                text     = (await last.inner_text()).strip()
                # Settle logic: wait if text is still streaming in or is only typing dots.
                # We must NOT return a dot-only string — that's the typing indicator bubble,
                # not a real response (e.g. hardened_variants bubble.assistant.typing).
                _is_dots = all(c in ".•· \u2022\u00b7 " for c in text) if text else True
                if len(text) < 20 or text.endswith(">") or _is_dots:
                    last_len = len(text)
                    for _ in range(10):
                        await asyncio.sleep(0.2)
                        new_text = (await last.inner_text()).strip()
                        if len(new_text) > last_len:
                            text, last_len = new_text, len(new_text)
                        elif new_text:
                            break
                # After settle, re-check: if text is still dots-only or too short,
                # the typing indicator is still active — re-enter the wait loop.
                _still_dots = all(c in ".•· \u2022\u00b7 " for c in text) if text else True
                if _still_dots or len(text) < 15:
                    await asyncio.sleep(POLL_INTERVAL_MS / 1000)
                    elapsed += POLL_INTERVAL_MS
                    continue
                return text


            # ── Stale selector probe: if 3s have passed and bot_message still
            #    matches 0 elements, our cached selector is wrong for this page.
            #    Try broad fallbacks and update self._selectors in-place. ─────
            if not selector_probed and elapsed >= 3000:
                selector_probed = True
                logger.warning(
                    "[%s] bot_message selector '%s' matched 0 elements after 3s — "
                    "trying fallback selectors", self.target_name, bot_selector
                )
                for fb in _FALLBACK_BOT_SELECTORS:
                    try:
                        cnt = await scope.locator(fb).count()
                        if cnt > 0:
                            logger.info(
                                "[%s] Fallback bot_message selector found: '%s' (%d matches)",
                                self.target_name, fb, cnt
                            )
                            # Patch selectors in-place so remaining polls use this
                            self._selectors["bot_message"] = fb
                            bot_selector = fb
                            before_count = max(0, cnt - 1)  # assume last is the new msg
                            # Persist the fix to selector cache
                            from .selector_manager import save_to_cache
                            from urllib.parse import urlparse
                            domain = urlparse(self.url).netloc
                            if domain:
                                updated = dict(self._selectors)
                                save_to_cache(domain, updated)
                                logger.info("[%s] Updated selector cache with fallback bot_message", self.target_name)
                            break
                    except Exception:
                        continue

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

    async def get_network_traces(self) -> list[dict]:
        """Return captured JSON network responses (fetch/xhr)."""
        return self.network_traces

    async def get_page_metadata(self) -> dict:
        """Return page title and stream/framework detection tags."""
        if not self._page:
            return {}
        title = await self._page.title()
        html = await self._page.content()
        return {
            "title": title,
            "has_streamlit": "streamlit" in html.lower() or "stapp" in html.lower() or "stchatinput" in html.lower(),
            "has_vercel": "vercel" in html.lower(),
        }

    async def reset_conversation(self) -> None:
        """Hard-reset by reloading the page — clears React state."""
        logger.info("Resetting conversation for %s", self.target_name)
        await self._navigate()
