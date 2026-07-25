"""
core_framework/orchestrator/graph.py

LangGraph orchestrator that wires up Planner, Executor, and Evaluator.
"""
import logging
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from src.agents.evaluator import evaluate_attempt
from src.agents.executor import execute_attack
from src.agents.mutator import mutate_payload
from src.agents.planner import select_next_payload
from src.memory.benchmark_store import BenchmarkStore
from src.memory.schemas import BenchmarkRecord, ComponentScore, VulnerabilityFinding
from src.memory.sqlite_manager import SQLiteManager

from .state import AttackState

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
        
    threat_model = state.get("threat_model")
    next_payload, p_scores = await select_next_payload(target, state.get("history", []), threat_model=threat_model)
    if not next_payload:
        logger.info("No more payloads to try.")
        return {"status": "done"}
        
    return {
        "current_payload": next_payload,
        "component_scores": p_scores,
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
    
    # Save attempt to SQLite DB immediately
    async with SQLiteManager() as db:
        await db.save_attempt(attempt)

    # Dual-Sync to Supabase Cloud if available
    try:
        from src.memory.supabase_manager import SupabaseManager
        sp_db = SupabaseManager()
        if sp_db.supabase and state.get("session_id"):
            sp_db.session_id = state["session_id"]
            sp_db.add_log(
                event="EXECUTION_STEP",
                description=f"Attempt {attempt.attempt_id} executed payload '{payload.name}' ({payload.category})",
                log_type="info"
            )
    except Exception as sp_err:
        logger.debug(f"Supabase dual-sync skipped/failed in executor_node: {sp_err}")
    
    # Emit executor component score
    is_sentinel = any(attempt.response_text.startswith(s) for s in ("[AEGIS_TIMEOUT:", "[AEGIS_ERROR:", "[AEGIS_NO_RESPONSE:"))
    exec_score = ComponentScore(
        session_id=state["session_id"],
        component="executor",
        confidence=0.0 if is_sentinel else 1.0,
        method="deterministic",
        notes="Sentinel response detected" if is_sentinel else "Successful response execution",
    )

    return {
        "current_attempt": attempt,
        "component_scores": [exec_score],
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

    # Dual-Sync findings to Supabase Cloud if available
    try:
        from src.memory.supabase_manager import SupabaseManager
        sp_db = SupabaseManager()
        if sp_db.supabase and state.get("session_id"):
            sp_db.session_id = state["session_id"]
            sp_db.add_log(
                event="EVALUATION_STEP",
                description=f"Evaluation Verdict: {eval_result.verdict.upper()} (Score: {eval_result.score}) - {eval_result.reasoning[:120]}...",
                log_type="success" if eval_result.verdict == "success" else "info"
            )
            for f in new_findings:
                sp_db.add_finding(finding_type=f.category, extracted_value=f.description)
    except Exception as sp_err:
        logger.debug(f"Supabase dual-sync skipped/failed in evaluator_node: {sp_err}")
            
    # Emit evaluator component score
    eval_comp_score = ComponentScore(
        session_id=state["session_id"],
        component="evaluator",
        confidence=eval_result.score,
        method=eval_result.evaluation_method,
        notes=f"Verdict: {eval_result.verdict}. {eval_result.reasoning[:80]}",
    )

    all_scores = state.get("component_scores", []) + [eval_comp_score]
    comp_map = {s.component: s.confidence for s in all_scores}
    pipeline_conf = round(sum(comp_map.values()) / max(len(comp_map), 1), 2)

    threat_model = state.get("threat_model")
    sec_level = threat_model.security_level if threat_model else "unknown"
    attack_goal = threat_model.attack_goal if threat_model else "jailbreak"

    benchmark_record = BenchmarkRecord(
        session_id=state["session_id"],
        attack_id=attempt.attempt_id,
        target_id=state["target"].target_id,
        target_type=state["target"].target_type,
        security_level=sec_level,
        attack_goal=attack_goal,
        payload_category=payload.category,
        verdict=eval_result.verdict,
        score=eval_result.score,
        pipeline_confidence=pipeline_conf,
        component_scores=comp_map,
        evaluation_method=eval_result.evaluation_method,
    )

    store = BenchmarkStore()
    await store.record(benchmark_record)

    # Decide next step: Mutate or pick next payload
    mutations_count = state.get("mutations_for_current", 0)
    if eval_result.verdict != "success" and mutations_count < state.get("max_mutations", 3):
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
        "component_scores": [eval_comp_score],
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
