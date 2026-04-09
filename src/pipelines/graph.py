"""
core_framework/orchestrator/graph.py

LangGraph orchestrator that wires up Planner, Executor, and Evaluator.
"""
import logging
from typing import Any

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import AttackState
from src.agents.planner import select_next_payload
from src.agents.executor import execute_attack
from src.agents.evaluator import evaluate_attempt
from src.agents.mutator import mutate_payload
from src.memory.schemas import VulnerabilityFinding
from src.memory.sqlite_manager import SQLiteManager

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Nodes
# ------------------------------------------------------------------

async def planner_node(state: AttackState) -> dict[str, Any]:
    iteration = state.get("iteration", 0)
    logger.info(f"--- Planner Node (Iter {iteration}) ---")
    
    max_iter = state.get("max_iterations", 5)
    
    if iteration >= max_iter:
        logger.info("Max iterations reached.")
        return {"status": "done"}
        
    next_payload = await select_next_payload(state["target"], state.get("history", []))
    if not next_payload:
        logger.info("No more payloads to try.")
        return {"status": "done"}
        
    return {
        "current_payload": next_payload,
        "mutations_for_current": 0,
        "iteration": iteration + 1,
        "status": "executing"
    }

async def executor_node(state: AttackState) -> dict[str, Any]:
    logger.info("--- Executor Node ---")
    payload = state.get("current_payload")
    if not payload:
        return {"status": "done"}
        
    attempt = await execute_attack(state["session_id"], state["target"], payload)
    
    # Save attempt to DB immediately
    async with SQLiteManager() as db:
        await db.save_attempt(attempt)
    
    return {
        "current_attempt": attempt,
        "status": "evaluating"
    }

async def evaluator_node(state: AttackState) -> dict[str, Any]:
    logger.info("--- Evaluator Node ---")
    attempt = state.get("current_attempt")
    payload = state.get("current_payload")
    
    if not attempt or not payload:
        return {"status": "done"}
        
    eval_result = await evaluate_attempt(attempt, payload)
    
    new_findings = []
    if eval_result.verdict == "success":
        finding = VulnerabilityFinding(
            session_id=state["session_id"],
            target_id=state["target"].target_id,
            category=payload.category,
            severity="high",
            title=f"Successful {payload.category} exploit",
            description=f"Payload '{payload.name}' succeeded.\nReasoning: {eval_result.reasoning}",
            exploit_chain=[attempt.attempt_id],
            reproduction_steps=[f"Send payload: {payload.template}"],
            confidence=eval_result.score
        )
        new_findings.append(finding)
        
    # Save evaluation and findings to DB
    async with SQLiteManager() as db:
        await db.save_evaluation(eval_result)
        for f in new_findings:
            await db.save_finding(f)
            
    # Decide next step: Mutate or pick next payload
    mutations_count = state.get("mutations_for_current", 0)
    if eval_result.verdict != "success" and mutations_count < 2:
        next_status = "mutating"
    else:
        next_status = "planning"
        
    return {
        "current_evaluation": eval_result,
        "history": [(attempt, eval_result)],
        "findings": new_findings,
        "status": next_status
    }

async def mutator_node(state: AttackState) -> dict[str, Any]:
    logger.info("--- Mutator Node ---")
    attempt = state.get("current_attempt")
    payload = state.get("current_payload")
    mutations_count = state.get("mutations_for_current", 0)
    
    mutated_payload = await mutate_payload(state["target"], payload, attempt)
    
    return {
        "current_payload": mutated_payload,
        "mutations_for_current": mutations_count + 1,
        "status": "executing"
    }

def route_next(state: AttackState) -> str:
    status = state.get("status", "done")
    if status == "executing":
        return "executor"
    elif status == "evaluating":
        return "evaluator"
    elif status == "mutating":
        return "mutator"
    elif status == "planning":
        return "planner"
    else:
        return END

# ------------------------------------------------------------------
# Graph Definition
# ------------------------------------------------------------------

workflow = StateGraph(AttackState)

workflow.add_node("planner", planner_node)
workflow.add_node("executor", executor_node)
workflow.add_node("evaluator", evaluator_node)
workflow.add_node("mutator", mutator_node)

workflow.set_entry_point("planner")

workflow.add_conditional_edges("planner", route_next)
workflow.add_conditional_edges("executor", route_next)
workflow.add_conditional_edges("evaluator", route_next)
workflow.add_conditional_edges("mutator", route_next)

# In-memory persistence for standard runs
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)
