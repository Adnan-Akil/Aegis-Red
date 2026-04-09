"""
core_framework/orchestrator/state.py

LangGraph State definitions for the Attack Graph.
"""
import operator
from typing import TypedDict, Annotated, Literal

from src.memory.schemas import (
    TargetProfile, 
    AttackPayload, 
    AttackAttempt, 
    EvaluationResult, 
    VulnerabilityFinding
)

class AttackState(TypedDict):
    """LangGraph State for an attack session."""
    session_id: str
    target: TargetProfile
    
    # Current loop variables
    current_payload: AttackPayload | None
    current_attempt: AttackAttempt | None
    current_evaluation: EvaluationResult | None
    
    # History tracking
    # operator.add ensures that returning a list from a node appends to the state
    history: Annotated[list[tuple[AttackAttempt, EvaluationResult]], operator.add]
    findings: Annotated[list[VulnerabilityFinding], operator.add]
    
    mutations_for_current: int
    
    iteration: int
    max_iterations: int
    status: Literal["init", "planning", "executing", "evaluating", "mutating", "done"]
