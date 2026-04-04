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
        
    async with PlaywrightDriver(
        target_name=target.name,
        url=target.url,
        hardened_tab=hardened_tab
    ) as driver:
        # First turn
        response_text, _ = await driver.send_message(payload.template)
        
        # Follow-up turns for multi-turn chains
        for i, follow_up in enumerate(payload.follow_up_turns):
            logger.debug(f"Sending follow-up turn {i+1}...")
            response_text, _ = await driver.send_message(follow_up)
            
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        attempt = AttackAttempt(
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
        return attempt
