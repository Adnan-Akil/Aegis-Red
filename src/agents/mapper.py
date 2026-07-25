"""
src/agents/mapper.py

Adaptive Surface Mapper — 3-stage detection pipeline:
  Stage 1 | Heuristic   — broad ordered CSS/ARIA candidate lists (fast, no LLM)
  Stage 2 | Proximity   — JS DOM traversal: find input, walk up to locate sibling button
  Stage 3 | LLM         — Groq analyses a cleaned HTML snapshot (slow, works on anything)

Returns a DiscoveredSurface with the URL AND the dynamically resolved selectors for
that specific target, so the executor doesn't need to rely on hardcoded SELECTORS.
"""

import json
import logging
import os
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

from groq import AsyncGroq
from src.config import FAST_MODEL
from src.utils.llm import call_llm_with_retry

from src.tools.browser.playwright_driver import PlaywrightDriver
from src.tools.browser.selectors import SELECTORS
from src.tools.browser.selector_manager import save_to_cache, get_cached_selectors

logger = logging.getLogger(__name__)

# ── Candidate selector lists (ordered: most specific → least specific) ──────

_INPUT_CANDIDATES = [
    "#prompt-textarea",
    "#chat-input",
    ".chat-input",
    "p[contenteditable='true']",
    "div[contenteditable='true']",
    "[contenteditable='true']",
    "rich-textarea",
    "[role='textbox']",
    "[role='searchbox']",
    "[data-testid*='input']",
    "[data-testid*='chat']",
    "[data-testid*='prompt']",
    "[aria-label*='message' i]",
    "[aria-label*='prompt' i]",
    "[aria-label*='chat' i]",
    "[aria-label*='ask' i]",
    "[aria-label*='type' i]",
    "[aria-label*='question' i]",
    "[placeholder*='message' i]",
    "[placeholder*='prompt' i]",
    "[placeholder*='ask' i]",
    "[placeholder*='question' i]",
    "[placeholder*='type' i]",
    "[placeholder*='chat' i]",
    "textarea",
    "input[type='text']",
]

_SEND_CANDIDATES = [
    "[data-testid*='send']",
    "[data-testid*='submit']",
    "button[aria-label*='send' i]",
    "button[aria-label*='submit' i]",
    "button[title*='send' i]",
    "button[type='submit']",
    "button:has(svg[class*='send' i])",
    "button:has(svg[class*='arrow' i])",
    "button:has(svg[class*='plane' i])",
    ".send-button",
    ".send-btn",
    "#send-button",
    "input[type='submit']",
]

_BOT_CANDIDATES = [
    # Explicit data attributes (most reliable)
    "[data-testid*='response']",
    "[data-testid*='assistant']",
    "[data-testid*='message']",
    "[data-role='assistant']",
    "[data-message-author-role='assistant']",
    "[aria-label*='response' i]",
    # Class-based — named patterns
    "[class*='assistant']",
    "[class*='bot-message']",
    "[class*='bot_message']",
    ".message.bot",
    ".assistant-message",
    ".ai-message",
    ".chat-message.assistant",
    ".response-message",
    # Common flex/layout chat structures
    "div.justify-start > div",
    "div.flex-col > div.flex > div",          # message row → bubble
    "div.flex.gap-3 > div",                    # gap-3 flex row
    "[class*='message'][class*='ai']",
    "[class*='message'][class*='bot']",
    "[class*='response']",
    # Tailwind utility combos used by tool-agent style apps
    "div.text-indigo-400 > div",
    "div.text-indigo-400 > div.flex-1",
    "div.flex.gap-3.text-indigo-400 > div.flex-1",
    # Streamlit-specific
    "[data-testid='stChatMessage']",
]

_TYPING_CANDIDATES = [
    "[aria-label*='loading' i]",
    "[aria-label*='thinking' i]",
    ".typing-indicator",
    ".animate-spin",
    "[class*='typing']",
    "[class*='loading']",
    ".loading",
]

_COMMON_PATHS = [
    "/chat", "/helpdesk", "/assistant", "/support", "/ai", "/bot",
    "/chatbot", "/help", "/contact", "/query", "/ask", "/agent", "/console",
]


# ── DiscoveredSurface ────────────────────────────────────────────────────────

@dataclass
class DiscoveredSurface:
    url: str
    chat_input: str
    send_button: str
    bot_message: str
    typing_indicator: str
    confidence: float   # 0.0 – 1.0
    strategy: str       # "heuristic" | "proximity" | "llm" | "fallback"

    def to_selector_dict(self) -> dict:
        return {
            "chat_input":          self.chat_input,
            "send_button":         self.send_button,
            "bot_message":         self.bot_message,
            "typing_indicator":    self.typing_indicator,
            "tab_button_template": "",
            "discovery_url":       self.url,
        }


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _wait(page, timeout: int = 5000) -> None:
    try:
        await page.wait_for_load_state("domcontentloaded", timeout=timeout)
        # Give JS frameworks an extra moment to render the UI
        await page.wait_for_timeout(2000)
    except Exception:
        pass


async def _first_match(page, candidates: list[str]) -> Optional[str]:
    """Return first selector from candidates that resolves to at least one element."""
    for sel in candidates:
        try:
            if await page.query_selector(sel):
                return sel
        except Exception:
            continue
    return None


# ── Stage 1: Heuristic ───────────────────────────────────────────────────────

async def _detect_heuristic(page) -> Optional[DiscoveredSurface]:
    """Broad ordered CSS/ARIA pattern matching. No LLM cost."""
    # Give SPA a moment to render
    try:
        await page.wait_for_selector(
            "textarea, input[type='text'], [contenteditable='true'], [role='textbox']", 
            timeout=5000, 
            state="attached"
        )
    except Exception:
        pass

    input_sel = await _first_match(page, _INPUT_CANDIDATES)
    if not input_sel:
        return None

    send_sel = await _first_match(page, _SEND_CANDIDATES)
    confidence = 0.85

    if not send_sel:
        # Loose fallback: any button alongside the input is enough
        send_sel = await _first_match(page, ["button", "[role='button']", "form"])
        if not send_sel:
            return None
        confidence = 0.5

    bot_sel  = await _first_match(page, _BOT_CANDIDATES)  or "div"
    typ_sel  = await _first_match(page, _TYPING_CANDIDATES) or ".animate-spin"

    logger.info(f"[Mapper][Heuristic] input={input_sel!r}  send={send_sel!r}  conf={confidence:.0%}")
    return DiscoveredSurface(
        url=page.url, chat_input=input_sel, send_button=send_sel,
        bot_message=bot_sel, typing_indicator=typ_sel,
        confidence=confidence, strategy="heuristic",
    )


# ── Stage 2: DOM Proximity ────────────────────────────────────────────────────

async def _detect_proximity(page) -> Optional[DiscoveredSurface]:
    """
    JavaScript DOM traversal: for every textarea/input/contenteditable,
    walk up the DOM tree up to 4 levels looking for a sibling button.
    Works on custom layouts where inputs and buttons are flex siblings.
    """
    result = await page.evaluate("""
    () => {
        const inputs = [...document.querySelectorAll(
            'textarea, input[type="text"], [contenteditable="true"], [role="textbox"]'
        )];
        for (const inp of inputs) {
            let node = inp;
            for (let i = 0; i < 4; i++) {
                node = node.parentElement;
                if (!node) break;
                const btn = node.querySelector(
                    'button, input[type="submit"], [role="button"]'
                );
                if (btn) {
                    const iSel = inp.id ? `#${inp.id}`
                               : inp.getAttribute('aria-label') ? `[aria-label="${inp.getAttribute('aria-label')}"]`
                               : inp.tagName.toLowerCase();
                    const bSel = btn.id  ? `#${btn.id}`
                               : btn.getAttribute('aria-label') ? `[aria-label="${btn.getAttribute('aria-label')}"]`
                               : btn.getAttribute('type') ? `${btn.tagName.toLowerCase()}[type="${btn.getAttribute('type')}"]`
                               : btn.tagName.toLowerCase();
                    return { iSel, bSel };
                }
            }
        }
        return null;
    }
    """)

    if not result:
        return None

    input_sel = result["iSel"]
    send_sel  = result["bSel"]
    bot_sel   = await _first_match(page, _BOT_CANDIDATES)   or "div"
    typ_sel   = await _first_match(page, _TYPING_CANDIDATES) or ".animate-spin"

    logger.info(f"[Mapper][Proximity] input={input_sel!r}  send={send_sel!r}")
    return DiscoveredSurface(
        url=page.url, chat_input=input_sel, send_button=send_sel,
        bot_message=bot_sel, typing_indicator=typ_sel,
        confidence=0.7, strategy="proximity",
    )


# ── Stage 3: LLM ─────────────────────────────────────────────────────────────

_LLM_SYSTEM = """You are a web scraping expert. Given an HTML snippet, determine if the page
contains an AI chatbot or conversational interface.

If YES, return ONLY this JSON (no markdown, no extra text):
{
  "has_chat": true,
  "input_selector": "<valid CSS selector for the text input>",
  "send_selector": "<valid CSS selector for the send/submit button>",
  "bot_selector": "<valid CSS selector for bot response messages>",
  "typing_selector": "<valid CSS selector for loading indicator, or empty string>",
  "reasoning": "<one sentence>"
}

If NO chat interface: {"has_chat": false}

Selector rules: prefer #id > [aria-label] > tag[attr] > .class. Must be valid for querySelector()."""


async def _detect_llm(page) -> Optional[DiscoveredSurface]:
    """Groq LLM analyses a cleaned HTML snapshot. Last-resort fallback."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.warning("[Mapper][LLM] No GROQ_API_KEY — skipping LLM stage")
        return None

    try:
        html = await page.evaluate("""
        () => {
            const c = document.documentElement.cloneNode(true);
            c.querySelectorAll('script,style,svg,link,meta,noscript').forEach(e => e.remove());
            return c.outerHTML.slice(0, 12000);
        }
        """)
    except Exception as e:
        logger.warning(f"[Mapper][LLM] DOM snapshot failed: {e}")
        return None

    try:
        client = AsyncGroq(api_key=api_key)
        resp = await call_llm_with_retry(
            client.chat.completions.create,
            model=FAST_MODEL,
            messages=[
                {"role": "system", "content": _LLM_SYSTEM},
                {"role": "user",   "content": f"URL: {page.url}\n\nHTML:\n{html}"},
            ],
            max_tokens=400,
            temperature=0.1,
        )
        raw = resp.choices[0].message.content.strip()
        # Strip markdown fences if present
        if "```" in raw:
            raw = raw.split("```")[1].lstrip("json").strip()
        data = json.loads(raw)
    except Exception as e:
        logger.warning(f"[Mapper][LLM] Failed: {e}")
        return None

    if not data.get("has_chat"):
        logger.info("[Mapper][LLM] LLM found no chat surface on this page")
        return None

    input_sel = data.get("input_selector", "textarea")
    send_sel  = data.get("send_selector",  "button[type='submit']")
    bot_sel   = data.get("bot_selector",   "div")
    typ_sel   = data.get("typing_selector") or ".animate-spin"

    logger.info(f"[Mapper][LLM] input={input_sel!r}  send={send_sel!r}  | {data.get('reasoning','')}")
    return DiscoveredSurface(
        url=page.url, chat_input=input_sel, send_button=send_sel,
        bot_message=bot_sel, typing_indicator=typ_sel,
        confidence=0.9, strategy="llm",
    )


# ── Detection pipeline ────────────────────────────────────────────────────────

async def _pipeline(page) -> Optional[DiscoveredSurface]:
    """Run stages in order; return on first success. Persist on discovery."""
    await _wait(page)
    surface = await _detect_heuristic(page)
    if surface and surface.confidence >= 0.5:
        _persist(page.url, surface)
        return surface
    surface = await _detect_proximity(page)
    if surface:
        _persist(page.url, surface)
        return surface
    surface = await _detect_llm(page)
    if surface:
        _persist(page.url, surface)
    return surface


def _persist(url: str, surface: DiscoveredSurface) -> None:
    """Save discovered selectors to selector_cache.json keyed by domain."""
    domain = urlparse(url).netloc
    if domain:
        save_to_cache(domain, surface.to_selector_dict())
        logger.info(f"[Mapper] Selectors cached for domain: {domain} (strategy={surface.strategy})")


# ── Public entry point ────────────────────────────────────────────────────────

async def map_surface(url: str, target_name: str, target_type: str) -> dict:
    """
    Crawl strategy:
      1. Run detection pipeline on the landing page.
      2. Follow <a href> internal links (chat-sounding paths prioritised).
      3. Probe common chatbot subpaths (/chat, /assistant, etc.).
      4. Fallback: return root URL with generic selectors if nothing found.
    """
    logger.info("--- Module 1: Adaptive Surface Mapper ---")
    discovery_url = url
    surface: Optional[DiscoveredSurface] = None

    # ── Cache hit: skip detection entirely if domain was seen before ───────────
    domain = urlparse(url).netloc
    cached_sels = get_cached_selectors(url)
    if cached_sels:
        logger.info(f"[Mapper] Cache HIT for {domain} — skipping detection pipeline")
        
        # Copy so we don't mutate the cached dict; extract discovery_url separately
        sels_copy = dict(cached_sels)
        cached_url = sels_copy.pop("discovery_url", url)
        
        return {
            "title":         domain,
            "discovery_url": cached_url,
            "selectors":     sels_copy,
            "confidence":    1.0,
            "strategy":      "cached",
            "transcript":    [],
        }

    async with PlaywrightDriver(target_name=target_name, url=url) as driver:
        page = driver._page

        # ── Step 1: Landing page ────────────────────────────────────────────
        surface = await _pipeline(page)
        if surface:
            logger.info(
                f"[Mapper] Chat surface on landing page | "
                f"strategy={surface.strategy} confidence={surface.confidence:.0%}"
            )
        else:
            # ── Step 2: Internal links ──────────────────────────────────────
            links = await page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
            domain = urlparse(url).netloc
            internal = [link for link in links if urlparse(link).netloc == domain and link.rstrip("/") != url.rstrip("/")]
            priority = [link for link in internal if any(
                k in link.lower() for k in ["chat", "support", "help", "assistant", "contact", "ask", "bot", "ai"]
            )]
            ordered = list(dict.fromkeys(priority + internal))[:10]

            for link in ordered:
                logger.info(f"[Mapper] Checking link: {link}")
                try:
                    await page.goto(link, wait_until="domcontentloaded", timeout=10000)
                except Exception:
                    continue
                surface = await _pipeline(page)
                if surface:
                    discovery_url = link
                    logger.info(f"[Mapper] Found at {link} | strategy={surface.strategy}")
                    break

            if not surface:
                # ── Step 3: Common paths ────────────────────────────────────
                logger.info("[Mapper] Probing common chatbot subpaths...")
                base = url.rstrip("/")
                for path in _COMMON_PATHS:
                    candidate = base + path
                    try:
                        resp = await page.goto(candidate, wait_until="domcontentloaded", timeout=6000)
                        if resp and resp.status < 400:
                            surface = await _pipeline(page)
                            if surface:
                                discovery_url = candidate
                                logger.info(f"[Mapper] Found at common path: {candidate}")
                                break
                    except Exception:
                        continue

        # ── Step 4: Fallback ────────────────────────────────────────────────
        if not surface:
            logger.warning("[Mapper] No surface found anywhere — using root + generic selectors")
            g = SELECTORS["generic"]
            surface = DiscoveredSurface(
                url=url,
                chat_input=g["chat_input"],
                send_button=g["send_button"],
                bot_message=g["bot_message"],
                typing_indicator=g["typing_indicator"],
                confidence=0.1,
                strategy="fallback",
            )

        title = await page.title()
        logger.info(
            f"[Mapper] Done | title='{title}' url={discovery_url} "
            f"strategy={surface.strategy} confidence={surface.confidence:.0%}"
        )

    return {
        "title":         title,
        "discovery_url": discovery_url,
        "selectors":     surface.to_selector_dict(),
        "confidence":    surface.confidence,
        "strategy":      surface.strategy,
        "transcript":    [],
    }
