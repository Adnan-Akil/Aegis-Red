"""
core_framework/storage/schemas.py

Canonical Pydantic data models for the framework.
Every agent reads/writes these — do not add ad-hoc dicts elsewhere.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

__all__ = [
    "TargetProfile",
    "AttackPayload",
    "AttackAttempt",
    "EvaluationResult",
    "VulnerabilityFinding",
]

# ---------------------------------------------------------------------------
# Target
# ---------------------------------------------------------------------------

class TargetProfile(BaseModel):
    """Describes a benchmark target app."""

    target_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str                               # e.g. "chatbot_vuln"
    url: str                                # base URL of the frontend
    api_url: str                            # base URL of the FastAPI backend
    target_type: Literal["chatbot", "rag", "tool_agent", "hardened_bot",
                         "hardened_rag", "hardened_tool", "unknown"]
    port: int = 80
    suspected_capabilities: list[str] = Field(default_factory=list)
    known_constraints: list[str] = Field(default_factory=list)
    security_filter_detected: bool = False
    notes: str = ""
    # Populated by the Surface Mapper — overrides hardcoded SELECTORS when set
    discovered_selectors: dict | None = None
    discovery_url: str | None = None        # actual chat page URL (may differ from url)


# ---------------------------------------------------------------------------
# Attack Library
# ---------------------------------------------------------------------------

class AttackPayload(BaseModel):
    """A single attack payload template from the attack library."""

    payload_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: Literal["jailbreak", "leakage", "tool_abuse", "escalation", "obfuscation"]
    name: str                               # short human-readable name
    template: str                           # the actual prompt text
    # Strings in the response that strongly suggest success
    success_indicators: list[str] = Field(default_factory=list)
    # Optional multi-turn: list of follow-up messages keyed by turn index
    follow_up_turns: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    parent_payload_id: str | None = None


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

class AttackAttempt(BaseModel):
    """Records a single payload submission + raw response."""

    attempt_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str                         # groups attempts in one run
    target_id: str
    payload_id: str
    category: str
    payload_text: str                       # resolved (non-template) payload
    response_text: str
    tool_calls_triggered: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    turn_index: int = 0                     # for multi-turn chains
    duration_ms: int = 0
    parent_payload_id: str | None = None


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

class EvaluationResult(BaseModel):
    """Output of the Evaluator agent for a single AttackAttempt."""

    attempt_id: str
    verdict: Literal["success", "partial", "fail"]
    score: float = Field(ge=0.0, le=1.0)
    # Which layer produced the verdict
    evaluation_method: Literal["deterministic", "llm_judge", "hybrid", "deterministic_regex", "echo_guard", "crash_signal"]
    reasoning: str                          # human-readable explanation
    matched_indicators: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------

class VulnerabilityFinding(BaseModel):
    """A confirmed (or partial) vulnerability discovered during a session."""

    finding_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    target_id: str
    category: str
    severity: Literal["critical", "high", "medium", "low", "info"]
    title: str
    description: str
    exploit_chain: list[str]                # ordered list of attempt_ids
    reproduction_steps: list[str]           # human-readable steps
    confidence: float = Field(ge=0.0, le=1.0)
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
