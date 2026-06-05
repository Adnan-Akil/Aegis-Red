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
    
    target = state.get("target")
    if target and target.target_type == "unknown":
        logger.warning(f"Target '{target.name}' is classified as UNKNOWN (out of scope). Halting execution to prevent wasteful scanning.")
        return {"status": "done"}
        
    max_iter = state.get("max_iterations", 5)
    
    if iteration >= max_iter:
        logger.info("Max iterations reached.")
        return {"status": "done"}
        
    next_payload = await select_next_payload(target, state.get("history", []))
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
        
    # ── Dynamic target-type re-classification (Strategy 1) ─────────────────
    target = state.get("target")
    if target and target.target_type not in ("rag",):
        import re
        response_lower = attempt.response_text.lower()
        
        # Look for explicit RAG indicator keywords/patterns in the bot's response
        rag_keywords = [
            "document-based", "retrieve", "retrieved", "knowledge base", "internal document",
            "company document", "source document", "context document", "onboarding document",
            "confidential document", "internal database", "citation", "refer to source",
            "employee handbook", "internal wiki", "doc-", "from the files"
        ]
        
        has_citations = bool(re.search(r"\[(?:source|doc|document|ref|\d+)\]", attempt.response_text, re.IGNORECASE))
        has_file_extensions = bool(re.search(r"\b\w+\.(?:pdf|docx|xlsx|txt|md)\b", response_lower))
        
        if any(kw in response_lower for kw in rag_keywords) or has_citations or has_file_extensions:
            logger.info(f"[Orchestrator] DYNAMIC CLASSIFICATION UPGRADE: Detected RAG indicators in response! Shifting target_type from '{target.target_type}' to 'rag'.")
            target.target_type = "rag"
            target.notes = (target.notes + "\n[RECON_UPGRADE] Dynamically re-classified as RAG target based on runtime response analysis.").strip()
        
    return {
        "current_evaluation": eval_result,
        "history": [(attempt, eval_result)],
        "findings": new_findings,
        "status": next_status,
        "target": target
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
