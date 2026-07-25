import asyncio
import logging
import re

from groq import RateLimitError

logger = logging.getLogger(__name__)

async def call_llm_with_retry(client_coro_func, *args, **kwargs):
    """
    Wraps an async LLM call with a retry mechanism for rate limits (429).
    """
    max_retries = 4
    base_wait = 10
    
    for attempt in range(max_retries):
        try:
            return await client_coro_func(*args, **kwargs)
        except RateLimitError as e:
            if attempt == max_retries - 1:
                logger.error(f"Rate limit exceeded after {max_retries} attempts.")
                raise
            
            # Try to extract the wait time from the error message.
            # Example message: "Please try again in 14.5s" or "Please try again in 8m43.71s"
            error_msg = str(e).lower()
            wait_seconds = base_wait * (2 ** attempt) # fallback exponential backoff
            
            match_s = re.search(r'try again in (?:[0-9]+m)?([0-9.]+)s', error_msg)
            match_m = re.search(r'try again in ([0-9]+)m', error_msg)
            
            if match_m or match_s:
                calc_wait = 0
                if match_m:
                    calc_wait += float(match_m.group(1)) * 60
                if match_s:
                    calc_wait += float(match_s.group(1))
                # Add a small buffer to the parsed wait time
                wait_seconds = calc_wait + 2.0
            
            logger.warning(f"Groq Rate Limit hit. Retrying in {wait_seconds:.1f} seconds (Attempt {attempt+1}/{max_retries})...")
            await asyncio.sleep(wait_seconds)
        except Exception:
            # For non-429 errors, just raise immediately to avoid silently looping on bad requests
            raise
