"""
core_framework/agents/executor.py

Executor Agent module.
Responsible for taking an AttackPayload and executing it against a TargetProfile
using the PlaywrightDriver. Handles multi-turn payloads sequentially.
"""
import time
import logging
from datetime import datetime

from src.memory.schemas import AttackAttempt, TargetProfile, AttackPayload
from src.tools.browser.playwright_driver import PlaywrightDriver
from src.tools.browser.selectors import SELECTORS

logger = logging.getLogger(__name__)

async def execute_attack(
    session_id: str,
    target: TargetProfile,
    payload: AttackPayload,
) -> AttackAttempt:
    """
    Executes a single payload (including follow-ups) against the target.
    Returns the resulting AttackAttempt.
    """
    logger.info(f"Executing payload {payload.payload_id} ({payload.name}) against {target.name}")
    
    start_time = time.monotonic()

    # Map target_type to hardened tab if applicable
    hardened_tab = None
    if target.target_type == "hardened_bot":
        hardened_tab = "bot"
    elif target.target_type == "hardened_rag":
        hardened_tab = "rag"
    elif target.target_type == "hardened_tool":
        hardened_tab = "tool"

    nav_url = target.discovery_url or target.url
    override_selectors = target.discovered_selectors or None

    response_text = "[AEGIS_NO_RESPONSE: Execution did not complete]"

    try:
        async with PlaywrightDriver(
            target_name=target.name,
            url=nav_url,
            hardened_tab=hardened_tab,
            selector_override=override_selectors,
        ) as driver:
            # First turn
            response_text, _ = await driver.send_message(payload.template)

            # Guard: if response is empty or suspiciously short, mark as timeout
            if not response_text or len(response_text.strip()) < 3:
                response_text = "[AEGIS_NO_RESPONSE: Bot returned empty response — result invalid]"

            # Follow-up turns for multi-turn chains
            for i, follow_up in enumerate(payload.follow_up_turns):
                logger.debug(f"Sending follow-up turn {i+1}...")
                follow_text, _ = await driver.send_message(follow_up)
                if follow_text and len(follow_text.strip()) >= 3:
                    response_text = follow_text  # Only update if we got a real response

    except TimeoutError as e:
        logger.warning(f"Timeout waiting for bot response on attempt against {target.name}: {e}")
        response_text = f"[AEGIS_TIMEOUT: Bot did not respond within the time limit — result invalid. {e}]"
    except Exception as e:
        logger.error(f"Executor failed: {e}")
        response_text = f"[AEGIS_ERROR: Browser/execution error — result invalid. {str(e)[:200]}]"

    duration_ms = int((time.monotonic() - start_time) * 1000)

    return AttackAttempt(
        session_id=session_id,
        target_id=target.target_id,
        payload_id=payload.payload_id,
        category=payload.category,
        payload_text=payload.template,
        response_text=response_text,
        turn_index=len(payload.follow_up_turns),
        duration_ms=duration_ms,
        timestamp=datetime.utcnow(),
        parent_payload_id=payload.parent_payload_id
    )
