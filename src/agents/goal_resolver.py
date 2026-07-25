"""
src/agents/goal_resolver.py

Deterministic Attack Goal Resolver module.
Assigns session-level attack goals and category constraints based on target metadata.
Zero LLM calls, zero I/O — fully deterministic lookup.
"""

import logging
from typing import Literal

from src.memory.schemas import ComponentScore

logger = logging.getLogger(__name__)


def resolve_attack_goal(
    session_id: str,
    target_type: str,
    security_filter_detected: bool,
) -> tuple[Literal["jailbreak", "mixed"], list[str], str, ComponentScore]:
    """
    Deterministically resolves (attack_goal, allowed_categories, rationale, ComponentScore).
    
    Matrix rules:
    - chatbot (False)    -> goal: jailbreak | categories: ["jailbreak"]
    - chatbot (True)     -> goal: jailbreak | categories: ["jailbreak", "obfuscation"]
    - rag (False)        -> goal: mixed     | categories: ["jailbreak", "leakage"]
    - rag (True)         -> goal: mixed     | categories: ["jailbreak", "leakage", "obfuscation"]
    - tool_agent (False) -> goal: mixed     | categories: ["escalation", "tool_abuse"]
    - tool_agent (True)  -> goal: mixed     | categories: ["escalation", "tool_abuse", "obfuscation"]
    - unknown (False)    -> goal: jailbreak | categories: ["jailbreak"]
    - unknown (True)     -> goal: jailbreak | categories: ["jailbreak", "obfuscation"]
    """
    logger.info(f"[GoalResolver] Resolving goal for type='{target_type}', filter={security_filter_detected}")

    if target_type == "chatbot":
        goal = "jailbreak"
        categories = ["jailbreak", "obfuscation"] if security_filter_detected else ["jailbreak"]
        rationale = (
            "Chatbot target: Goal is jailbreak/system prompt extraction. "
            + ("Obfuscation enabled due to security filter." if security_filter_detected else "Direct attack vector.")
        )
    elif target_type == "rag":
        goal = "mixed"
        categories = ["jailbreak", "leakage", "obfuscation"] if security_filter_detected else ["jailbreak", "leakage"]
        rationale = (
            "RAG target: Goal is mixed (jailbreak precursor -> data leakage exfiltration). "
            + ("Obfuscation enabled due to security filter." if security_filter_detected else "")
        )
    elif target_type == "tool_agent":
        goal = "mixed"
        categories = (
            ["escalation", "tool_abuse", "obfuscation"] if security_filter_detected else ["escalation", "tool_abuse"]
        )
        rationale = (
            "Tool Agent target: Goal is mixed (privilege escalation -> unauthorized tool abuse). "
            + ("Obfuscation enabled due to security filter." if security_filter_detected else "")
        )
    else:  # unknown
        goal = "jailbreak"
        categories = ["jailbreak", "obfuscation"] if security_filter_detected else ["jailbreak"]
        rationale = "Unknown target type: Defaulting to jailbreak baseline."

    score = ComponentScore(
        session_id=session_id,
        component="goal_resolver",
        confidence=1.0,
        method="lookup",
        notes=f"Deterministic resolution: goal={goal}, categories={categories}",
    )

    logger.info(f"[GoalResolver] Assigned goal='{goal}', allowed_categories={categories}")
    return goal, categories, rationale, score
