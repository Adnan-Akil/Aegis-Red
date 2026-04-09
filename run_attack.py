"""
run_attack.py

CLI entry point to execute an attack session against a target.
Demonstrates the full autonomous loop: Planning -> Execution -> Evaluation
"""
import asyncio
import uuid
import logging
import argparse
import urllib.parse
from pathlib import Path
from src import config
from src.evaluation.report_generator import generate_cybersec_report

from src.memory.schemas import TargetProfile
from src.memory.supabase_manager import SupabaseManager
from src.pipelines.graph import app as orchestrator_app
from src.agents.mapper import map_surface
from src.agents.threat_modeler import generate_threat_model

from logging.handlers import RotatingFileHandler

Path("logs").mkdir(exist_ok=True)
# Rotating log: max 2MB per file, keep 3 backups
_log_handler = RotatingFileHandler(
    "logs/attack_session.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8"
)
_log_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logging.basicConfig(level=logging.INFO, handlers=[_log_handler])

# Suppress noisy external logs
logging.getLogger("httpx").setLevel(logging.WARNING)

async def run(target_type: str, port: int, iterations: int, mutations: int, user_id: str = "default"):
    # Initialize Supabase Manager
    db = SupabaseManager()
    # Map input to our known targets
    target_names = {
        "chatbot": "chatbot_vuln",
        "rag": "rag_vuln",
        "tool_agent": "tool_agent_vuln",
        "hardened_bot": "hardened_variants",
        "hardened_rag": "hardened_variants",
        "hardened_tool": "hardened_variants"
    }
    
    if target_type.startswith("http"):
        # We received a direct URL, so this is a blind test on an unknown target.
        url = target_type
        parsed = urllib.parse.urlparse(url)
        name = parsed.netloc or "external_target"
        target_type = "unknown"
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    else:
        # Standard local benchmark target
        name = target_names.get(target_type, "unknown_target")
        url = f"http://localhost:{port}"
    
    # Reconnaissance Phase (Module 1 & 2)
    mapper_data = await map_surface(url, target_name=name, target_type=target_type)
    target = await generate_threat_model(url, target_name=name, base_target_type=target_type, port=port, mapper_data=mapper_data)
    
    # KEY FIX: Persist the chatbot page URL discovered by the mapper.
    # The mapper may have found the real chat page at a subpath (e.g., /helpdesk).
    # All subsequent agents (Prober, Executor) must navigate to THAT page, not the root.
    discovered_url = mapper_data.get("discovery_url", url)
    if discovered_url != url:
        logging.getLogger(__name__).info(f"Mapper discovered chatbot at: {discovered_url} (updating from {url})")
        target.url = discovered_url
    
    # Active Probing Phase
    from src.agents.prober import active_probe
    print(f"\n🕵️ Active Prober: Interrogating target to discover capabilities...")
    target = await active_probe(target)
    
    # Save target config & start session
    db.create_session(user_id=user_id, target_name=target.name, target_url=target.url, target_type=target.target_type)
    session_id = db.session_id
    db.add_log("RECON_COMPLETE", f"Discovered target type: {target.target_type}", "info")
    
    initial_state = {
        "session_id": session_id,
        "target": target,
        "current_payload": None,
        "current_attempt": None,
        "current_evaluation": None,
        "history": [],
        "findings": [],
        "iteration": 0,
        "max_iterations": iterations,
        "max_mutations": mutations,
        "status": "planning"
    }
    
    config = {"configurable": {"thread_id": session_id}}
    
    print(f"\n==================================================")
    print(f"🚀 Starting Attack Session: {session_id}")
    print(f"🎯 Target: {target.name} ({target.target_type}) at {target.url}")
    print(f"==================================================\n")
    
    last_attempt = None
    max_score = 0.0
    markdown_trace = f"# Aegis-Red Attack Trace: {session_id}\n"
    markdown_trace += f"**Target**: {target.url}\n**Type**: {target.target_type}\n\n---\n\n"

    # Track whether the current iteration block has been properly closed with a verdict.
    # If it hasn't when we exit (crash/cancel), we append a clear INTERRUPTED marker.
    _iter_verdict_written = True  # True = no open block yet

    try:
        async for event in orchestrator_app.astream(initial_state, config):
            for node_name, state_update in event.items():
                if node_name == "planner":
                    if state_update.get("status") == "done":
                        continue
                    # Close any iteration that opened but never got a verdict
                    if not _iter_verdict_written:
                        markdown_trace += "**Response**: *(none — executor failed or timed out)*\n\n"
                        markdown_trace += "**Verdict**: INTERRUPTED (Score: 0.0)\n**Reasoning**: Iteration did not complete — executor exception or timeout.\n\n---\n\n"
                        _iter_verdict_written = True

                    iteration = state_update.get("iteration", 0)
                    print(f"\n[Iteration {iteration}] 🔄 Planning next attack vector...")
                    db.add_log("PLANNING", f"Planning iteration {iteration}", "info")
                    markdown_trace += f"## Iteration {iteration}\n"
                    _iter_verdict_written = False  # New open block

                elif node_name == "mutator":
                    pass

                elif node_name == "executor":
                    attempt = state_update.get("current_attempt")
                    if attempt:
                        last_attempt = attempt
                        print(f" ├── 🗡️ Attack: {attempt.category.upper()} (Payload ID: {attempt.payload_id})")

                        sent_text = attempt.payload_text.replace('\n', ' ')
                        if len(sent_text) > 100: sent_text = sent_text[:100] + "..."
                        print(f" ├── 💬 Sent: \"{sent_text}\"")

                        db.add_log("ATTACK_SENT", f"Sent {attempt.category} payload", "action")
                        markdown_trace += f"### {attempt.category.upper()}\n**Payload**:\n> {attempt.payload_text}\n\n"

                elif node_name == "evaluator":
                    eval_res = state_update.get("current_evaluation")
                    if eval_res and last_attempt:
                        max_score = max(max_score, eval_res.score)

                        rcvd_text = last_attempt.response_text.replace('\n', ' ')
                        preview_len = 250 if eval_res.score > 0 else 100
                        if len(rcvd_text) > preview_len: rcvd_text = rcvd_text[:preview_len] + "..."
                        print(f" ├── 🛡️ Rcvd: \"{rcvd_text}\" ({last_attempt.duration_ms}ms)")

                        if eval_res.score == 1.0:
                            icon, color_prefix = "✅", "\033[92m"
                        elif eval_res.score > 0:
                            icon, color_prefix = "⚠️", "\033[93m"
                        else:
                            icon, color_prefix = "❌", "\033[91m"

                        color_suffix = "\033[0m"
                        reason = eval_res.reasoning.replace('VERDICT: YES\n', '').replace('VERDICT: NO\n', '').replace('VERDICT: PARTIAL\n', '').strip()
                        print(f" └── {color_prefix}{icon} Verdict: {eval_res.verdict.upper()} (Score {eval_res.score}){color_suffix} - {reason}")

                        db.add_log("EVALUATION", f"Verdict: {eval_res.verdict.upper()} (Score: {eval_res.score})", "info" if eval_res.score == 0 else "warning")
                        markdown_trace += f"**Response**:\n> {last_attempt.response_text}\n\n"
                        markdown_trace += f"**Verdict**: {eval_res.verdict.upper()} (Score: {eval_res.score})\n**Reasoning**: {reason}\n\n---\n\n"
                        _iter_verdict_written = True  # Block properly closed

                        for indicator in eval_res.matched_indicators:
                            if indicator.startswith("SECRET_LEAK:"):
                                secret_val = indicator.split("SECRET_LEAK:")[1]
                                print(f"\n     🚨 \033[41m\033[97m CRITICAL LEAK CAUGHT: {secret_val} \033[0m")
                                db.add_finding("SECRET_LEAK", secret_val)

    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\n\n⚠️  Session cancelled by user.")
        if not _iter_verdict_written:
            markdown_trace += "**Response**: *(none — session cancelled)*\n\n"
            markdown_trace += "**Verdict**: CANCELLED (Score: 0.0)\n**Reasoning**: Session was interrupted by the operator.\n\n---\n\n"
        markdown_trace += "\n> ⚠️ **Session was cancelled before completion.**\n"

    except Exception as e:
        logging.getLogger(__name__).error(f"Orchestrator crashed: {e}", exc_info=True)
        print(f"\n\n❌ Session crashed: {e}")
        if not _iter_verdict_written:
            markdown_trace += f"**Response**: *(none — session crashed)*\n\n"
            markdown_trace += f"**Verdict**: ERROR (Score: 0.0)\n**Reasoning**: Framework exception: {str(e)[:300]}\n\n---\n\n"
        markdown_trace += f"\n> ❌ **Session terminated with error:** `{str(e)[:300]}`\n"
                
    # Finalize session
    final_verdict = "Secure"
    final_score = 0.0
    
    if max_score == 1.0:
        final_verdict = "Critical"
        final_score = 10.0
    elif max_score > 0:
        final_verdict = "Warning"
        final_score = 5.0

    print("\n==================================================")
    print(f"Generating formal penetration test report...")
    report_content = await generate_cybersec_report(markdown_trace, target.url, session_id)

    db.complete_session(
        verdict=final_verdict, 
        overall_score=final_score, 
        payload_content=markdown_trace, 
        report_content=report_content
    )

    print(f"✅ Session Complete. Trace and Report uploaded to Supabase Storage.")
    print("==================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the AI Red Team framework against a local target.")
    parser.add_argument("target", help="Target type (e.g. 'chatbot', 'rag') OR a full HTTP URL (e.g. 'https://my-target.com')")
    parser.add_argument("--port", type=int, default=5173, help="Local port for benchmark targets")
    parser.add_argument("--iter", type=int, default=3, help="Max iterations to run")
    parser.add_argument("--mutations", type=int, default=3, help="Max mutations")
    parser.add_argument("--user_id", default="default_user", help="Supabase User ID")
    
    args = parser.parse_args()
    asyncio.run(run(args.target, args.port, args.iter, args.mutations, args.user_id))
