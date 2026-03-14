import json
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

CACHE_FILE = Path("src/tools/browser/selector_cache.json")

def load_cache() -> dict:
    if not CACHE_FILE.exists():
        return {}
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load selector cache: {e}")
        return {}

def save_to_cache(domain: str, selectors: dict):
    cache = load_cache()
    cache[domain] = selectors
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=4)
        logger.info(f"Persistent Selector Memory updated for: {domain}")
    except Exception as e:
        logger.error(f"Failed to save to selector cache: {e}")

def get_cached_selectors(url: str) -> dict | None:
    from urllib.parse import urlparse
    domain = urlparse(url).netloc
    return load_cache().get(domain)
