import logging
from urllib.parse import urljoin, urlparse
from src.tools.browser.playwright_driver import PlaywrightDriver
from src.tools.browser.selectors import SELECTORS

logger = logging.getLogger(__name__)

# Chatbot subpaths to try on SPAs and React apps that have no navigable <a> links
_COMMON_CHATBOT_PATHS = [
    "/chat", "/helpdesk", "/assistant", "/support", "/ai", "/bot",
    "/chatbot", "/help", "/contact", "/query", "/ask", "/agent", "/console"
]

async def _is_chat_surface(page, generic_selectors: dict) -> bool:
    """
    A real chat surface must have BOTH an input field AND a send button.
    Checking only for an input causes false positives on search bars and file upload forms.
    """
    has_input = await page.query_selector(generic_selectors["chat_input"])
    has_button = await page.query_selector(generic_selectors["send_button"])
    return bool(has_input and has_button)

async def map_surface(url: str, target_name: str, target_type: str) -> dict:
    """
    Crawls a multi-page website to discover the AI surface.
    Strategy (in order):
      1. Check if the landing page itself is a chat surface.
      2. Crawl <a href> links and check prioritized candidates.
      3. Probe common chatbot subpaths (for SPAs with no real links).
    """
    logger.info("--- Module 1: Surface Mapper Agent (Production Mode) ---")
    
    discovery_url = url
    title = ""
    
    async with PlaywrightDriver(target_name=target_name, url=url) as driver:
        logger.info(f"Crawling {url} for potential AI surfaces...")
        generic_selectors = SELECTORS["generic"]
        
        # Step 1: Check the landing page itself
        if await _is_chat_surface(driver._page, generic_selectors):
            logger.info(f"AI Surface discovered on landing page: {url}")
            discovery_url = url
        else:
            # Step 2: Crawl <a href> links and try prioritized candidates
            links = await driver._page.eval_on_selector_all("a[href]", "elements => elements.map(e => e.href)")
            domain = urlparse(url).netloc
            candidates = [l for l in links if urlparse(l).netloc == domain and l != url]
            prioritized = [c for c in candidates if any(
                k in c.lower() for k in ["support", "chat", "help", "assistant", "contact", "query", "ask", "bot"]
            )]
            # Put prioritized links first, then remaining internal links
            ordered = list(dict.fromkeys(prioritized + candidates))
            
            found = False
            for candidate in ordered[:8]:
                logger.info(f"Checking candidate surface: {candidate}")
                await driver._page.goto(candidate, wait_until="networkidle")
                if await _is_chat_surface(driver._page, generic_selectors):
                    logger.info(f"AI Surface discovered at: {candidate}")
                    discovery_url = candidate
                    found = True
                    break
            
            if not found:
                # Step 3: Probe common chatbot paths (handles SPAs with no real <a> links)
                logger.info("No surface found via links. Trying common chatbot paths...")
                base = url.rstrip("/")
                for path in _COMMON_CHATBOT_PATHS:
                    candidate = base + path
                    try:
                        resp = await driver._page.goto(candidate, wait_until="networkidle", timeout=5000)
                        if resp and resp.status < 400:
                            if await _is_chat_surface(driver._page, generic_selectors):
                                logger.info(f"AI Surface discovered at common path: {candidate}")
                                discovery_url = candidate
                                break
                    except Exception:
                        continue
                else:
                    # Nothing found anywhere — use root and let the prober handle it
                    logger.warning("No chat surface found on any path. Using root URL.")
                    discovery_url = url

        title = await driver._page.title()
        logger.info(f"Target Surface Title: '{title}' | Chat surface at: {discovery_url}")
        
    return {
        "title": title,
        "discovery_url": discovery_url,
        "transcript": []
    }
