"""
core_framework/attack_library/registry.py

Central registry of all attack payloads.
Agents query this — never import individual payload files directly.

Usage:
    from src.tools.attacks.registry import AttackRegistry

    # Get all jailbreak payloads
    payloads = AttackRegistry.get_by_category("jailbreak")

    # Get a specific payload by ID
    payload = AttackRegistry.get("jb-003")

    # Get all payloads for a given target type
    payloads = AttackRegistry.get_for_target("chatbot")
"""

from __future__ import annotations

from src.memory.schemas import AttackPayload
from .jailbreaks import JAILBREAK_PAYLOADS
from .leakage import LEAKAGE_PAYLOADS
from .tool_abuse import TOOL_ABUSE_PAYLOADS
from .escalation import ESCALATION_PAYLOADS
from .obfuscation import OBFUSCATION_PAYLOADS

__all__ = ["AttackRegistry"]

# Map target_type → which categories are most relevant
_TARGET_CATEGORY_MAP: dict[str, list[str]] = {
    "chatbot":        ["jailbreak", "escalation", "leakage"],
    "rag":            ["leakage", "jailbreak"],
    "tool_agent":     ["tool_abuse", "escalation", "leakage"],
    "hardened_bot":   ["jailbreak", "escalation", "obfuscation", "leakage"],
    "hardened_rag":   ["leakage", "jailbreak", "escalation", "obfuscation"],
    "hardened_tool":  ["tool_abuse", "escalation", "obfuscation", "leakage"],
    "unknown":        ["jailbreak", "leakage", "tool_abuse", "escalation", "obfuscation"],
}


class AttackRegistry:
    """
    Static registry. No instantiation needed.
    All methods are classmethods — call directly on the class.
    """

    _all: list[AttackPayload] = (
        JAILBREAK_PAYLOADS
        + LEAKAGE_PAYLOADS
        + TOOL_ABUSE_PAYLOADS
        + ESCALATION_PAYLOADS
        + OBFUSCATION_PAYLOADS
    )

    _by_id: dict[str, AttackPayload] = {p.payload_id: p for p in _all}

    _by_category: dict[str, list[AttackPayload]] = {}
    for _p in _all:
        _by_category.setdefault(_p.category, []).append(_p)

    # ------------------------------------------------------------------

    @classmethod
    def get(cls, payload_id: str) -> AttackPayload | None:
        """Fetch a single payload by its ID. Returns None if not found."""
        return cls._by_id.get(payload_id)

    @classmethod
    def get_by_category(cls, category: str) -> list[AttackPayload]:
        """Return all payloads in a given category."""
        return cls._by_category.get(category, [])

    @classmethod
    def get_for_target(cls, target_type: str) -> list[AttackPayload]:
        """
        Return all payloads relevant to a given target type.
        Falls back to all payloads if target_type is unrecognised.
        """
        categories = _TARGET_CATEGORY_MAP.get(target_type, list(cls._by_category.keys()))
        result: list[AttackPayload] = []
        for cat in categories:
            result.extend(cls.get_by_category(cat))
        return result

    @classmethod
    def get_by_tag(cls, tag: str) -> list[AttackPayload]:
        """Return all payloads that have a specific tag."""
        return [p for p in cls._all if tag in p.tags]

    @classmethod
    def get_multi_turn(cls) -> list[AttackPayload]:
        """Return only payloads that have follow-up turns (multi-turn chains)."""
        return [p for p in cls._all if p.follow_up_turns]

    @classmethod
    def all(cls) -> list[AttackPayload]:
        """Return every payload in the registry."""
        return cls._all

    @classmethod
    def summary(cls) -> dict[str, int]:
        """Return a count of payloads per category — useful for logging."""
        return {cat: len(payloads) for cat, payloads in cls._by_category.items()}
