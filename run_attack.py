"""
run_attack.py

CLI entry point to execute an attack session against a target.
Demonstrates the full autonomous loop: Planning -> Execution -> Evaluation
"""
import asyncio
import logging
import argparse
import urllib.parse
import sys
from pathlib import Path

# Force UTF-8 encoding for standard output to support emojis on Windows
sys.stdout.reconfigure(encoding='utf-8')

from src.evaluation.report_generator import generate_cybersec_report  # noqa: E402
from src.evaluation.md_compiler import TraceBuilder  # noqa: E402

from src.memory.supabase_manager import SupabaseManager  # noqa: E402
from src.pipelines.graph import app as orchestrator_app  # noqa: E402
from src.agents.mapper import map_surface  # noqa: E402
from src.agents.threat_modeler import generate_threat_model  # noqa: E402

from logging.handlers import RotatingFileHandler  # noqa: E402

Path("logs").mkdir(exist_ok=True)
# Rotating log: max 2MB per file, keep 3 backups
_log_handler = RotatingFileHandler(
    "logs/attack_session.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8"
)
_log_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logging.basicConfig(level=logging.INFO, handlers=[_log_handler])

# Suppress noisy external logs
logging.getLogger("httpx").setLevel(logging.WARNING)

async def run(target_type: str, port: int, iterations: int, mutations: int, user_id: str = "00000000-0000-0000-0000-000000000000", declared_type: str | None = None):
    # Initialize Supabase Manager
    db = SupabaseManager()
    
    # Auto-resolve active user ID from database if default mock is provided
    if user_id == "00000000-0000-0000-0000-000000000000":
        try:
            response = db.supabase.table("attack_sessions").select("user_id").order("created_at", desc=True).limit(1).execute()
            if response.data:
                resolved_id = response.data[0]["user_id"]
                if resolved_id and resolved_id != "00000000-0000-0000-0000-000000000000":
                    user_id = resolved_id
                    logging.getLogger(__name__).info(f"Auto-resolved active user ID: {user_id}")
        except Exception as e:
            logging.getLogger(__name__).warning(f"Failed to auto-resolve active user ID: {e}")
    # Map input to our known targets
    target_names = {
        "chatbot": "chatbot_vuln",
        "target_1_chatbot": "chatbot_vuln",
        "rag": "rag_vuln",
        "target_2_rag": "rag_vuln",
        "tool_agent": "tool_agent_vuln",
        "target_3_tool_agent": "tool_agent_vuln",
        "sdk_chatbot": "vercel_boilerplate",
        "streamlit_rag": "streamlit_rag"
    }

    # Map the target label to a schema-compliant target_type
    target_type_map = {
        "sdk_chatbot": "chatbot",
        "streamlit_rag": "rag",
        "target_1_chatbot": "chatbot",
        "target_2_rag": "rag",
        "target_3_tool_agent": "tool_agent"
    }
    
    actual_target_type = target_type_map.get(target_type, target_type)
    
    if target_type.startswith("http"):
        # We received a direct URL, so this is a blind test on an unknown target.
        url = target_type
        parsed = urllib.parse.urlparse(url)
        name = parsed.netloc or "external_target"
        target_type = "unknown"
        actual_target_type = "unknown"
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    else:
        # Standard local benchmark target
        name = target_names.get(target_type, "unknown_target")
        url = f"http://localhost:{port}"

    # If caller explicitly declared the type (from YAML blueprint), it overrides
    # any heuristic or lookup — preventing misclassification during probing.
    if declared_type and declared_type in ("chatbot", "rag", "tool_agent"):
        actual_target_type = declared_type
        logging.getLogger(__name__).info(f"Using caller-declared target type: {actual_target_type}")
    
    from src.memory.schemas import ComponentScore, ThreatModel  # noqa: E402
    from src.agents.goal_resolver import resolve_attack_goal  # noqa: E402
    from src.memory.benchmark_store import BenchmarkStore  # noqa: E402

    # Reconnaissance Phase (Module 1 & 2)
    mapper_data = await map_surface(url, target_name=name, target_type=actual_target_type)
    target, tm_score = await generate_threat_model(url, target_name=name, base_target_type=actual_target_type, port=port, mapper_data=mapper_data)
    
    mapper_score = ComponentScore(
        session_id="",
        component="mapper",
        confidence=mapper_data.get("confidence", 0.85),
        method=mapper_data.get("strategy", "heuristic"),
        notes=f"Strategy: {mapper_data.get('strategy')}, Discovery URL: {mapper_data.get('discovery_url')}"
    )

    # Wire mapper discoveries into the target profile
    discovered_url = mapper_data.get("discovery_url", url)
    discovered_sels = mapper_data.get("selectors")
    if discovered_url != url:
        logging.getLogger(__name__).info(f"Mapper discovered chatbot at: {discovered_url} (updating from {url})")
    target.url = discovered_url
    target.discovery_url = discovered_url
    if discovered_sels:
        target.discovered_selectors = discovered_sels
        logging.getLogger(__name__).info(f"Mapper selectors applied to target (strategy={mapper_data.get('strategy','?')})")
    
    # Active Probing Phase
    from src.agents.prober import active_probe
    print("\n🕵️ Active Prober: Interrogating target to discover capabilities...")
    target, classifier_score = await active_probe(target)
    
    # Save target config & start session
    db.create_session(user_id=user_id, target_name=target.name, target_url=target.url, target_type=target.target_type)
    session_id = db.session_id
    db.add_log("RECON_COMPLETE", f"Discovered target type: {target.target_type}", "info")

    # Set session_id on pre-session component scores
    mapper_score.session_id = session_id
    tm_score.session_id = session_id
    classifier_score.session_id = session_id

    # Resolve Attack Goal & Assemble ThreatModel
    attack_goal, allowed_cats, rationale, goal_score = resolve_attack_goal(
        session_id=session_id,
        target_type=target.target_type,
        security_filter_detected=target.security_filter_detected,
    )

    threat_model = ThreatModel(
        session_id=session_id,
        target_id=target.target_id,
        target_type=target.target_type,
        security_level="moderate" if target.security_filter_detected else "basic",
        security_filter_detected=target.security_filter_detected,
        suspected_capabilities=target.suspected_capabilities,
        known_constraints=target.known_constraints,
        attack_goal=attack_goal,
        allowed_categories=allowed_cats,
        goal_rationale=rationale,
        threat_model_confidence=tm_score.confidence,
        raw_notes=target.notes,
    )
    
    initial_state = {
        "session_id": session_id,
        "target": target,
        "threat_model": threat_model,
        "current_payload": None,
        "current_attempt": None,
        "current_evaluation": None,
        "history": [],
        "findings": [],
        "component_scores": [mapper_score, tm_score, goal_score, classifier_score],
        "iteration": 0,
        "max_iterations": iterations,
        "max_mutations": mutations,
        "status": "planning"
    }
    
    config = {
        "configurable": {"thread_id": session_id},
        "recursion_limit": 150
    }

    
    print("\n==================================================")
    print(f"🚀 Starting Attack Session: {session_id}")
    print(f"🎯 Target: {target.name} ({target.target_type}) at {target.url}")
    print("==================================================\n")
    
    last_attempt = None
    max_score = 0.0
    trace_builder = TraceBuilder(session_id, target.url, target.target_type)

    try:
        async for event in orchestrator_app.astream(initial_state, config):
            for node_name, state_update in event.items():
                if node_name == "planner":
                    if state_update.get("status") == "done":
                        continue

                    iteration = state_update.get("iteration", 0)
                    print(f"\n[Iteration {iteration}] 🔄 Planning next attack vector...")
                    db.add_log("PLANNING", f"Planning iteration {iteration}", "info")
                    trace_builder.start_iteration(iteration)

                elif node_name == "mutator":
                    pass

                elif node_name == "executor":
                    attempt = state_update.get("current_attempt")
                    if attempt:
                        last_attempt = attempt
                        print(f" ├── 🗡️ Attack: {attempt.category.upper()} (Payload ID: {attempt.payload_id})")

                        sent_text = attempt.payload_text.replace('\n', ' ')
                        if len(sent_text) > 100:
                            sent_text = sent_text[:100] + "..."
                        print(f" ├── 💬 Sent: \"{sent_text}\"")

                        db.add_log("ATTACK_SENT", f"Sent {attempt.category} payload", "action")
                        trace_builder.add_payload(attempt.category, attempt.payload_text)

                elif node_name == "evaluator":
                    eval_res = state_update.get("current_evaluation")
                    if eval_res and last_attempt:
                        max_score = max(max_score, eval_res.score)

                        rcvd_text = last_attempt.response_text.replace('\n', ' ')
                        preview_len = 250 if eval_res.score > 0 else 100
                        if len(rcvd_text) > preview_len:
                            rcvd_text = rcvd_text[:preview_len] + "..."
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
                        trace_builder.add_evaluation(last_attempt.response_text, eval_res.verdict, eval_res.score, reason)

                        for indicator in eval_res.matched_indicators:
                            if indicator.startswith("SECRET_LEAK:"):
                                secret_val = indicator.split("SECRET_LEAK:")[1]
                                print(f"\n     🚨 \033[41m\033[97m CRITICAL LEAK CAUGHT: {secret_val} \033[0m")
                                db.add_finding("SECRET_LEAK", secret_val)

    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\n\n⚠️  Session cancelled by user.")
        trace_builder.close_pending("cancelled", "Session was interrupted by the operator.")
        trace_builder.set_termination("cancelled", "")

    except Exception as e:
        logging.getLogger(__name__).error(f"Orchestrator crashed: {e}", exc_info=True)
        print(f"\n\n❌ Session crashed: {e}")
        trace_builder.close_pending("error", f"Framework exception: {str(e)[:300]}")
        trace_builder.set_termination("error", str(e)[:300])
                
    # Finalize session
    final_verdict = "Secure"
    final_score = 0.0
    
    if max_score == 1.0:
        final_verdict = "Critical"
        final_score = 10.0
    elif max_score > 0:
        final_verdict = "Warning"
        final_score = 5.0

    markdown_trace = trace_builder.render()

    print("\n==================================================")
    print("Generating formal penetration test report...")
    report_content = await generate_cybersec_report(markdown_trace, target.url, session_id)

    db.complete_session(
        verdict=final_verdict, 
        overall_score=final_score, 
        payload_content=markdown_trace, 
        report_content=report_content
    )

    # Print Session Benchmark Performance Summary
    try:
        summary_store = BenchmarkStore()
        summary_data = await summary_store.get_session_summary(session_id)
        print("\n📊 PIPELINE COMPONENT BENCHMARK SUMMARY")
        print("--------------------------------------------------")
        print(f"Session ID              : {session_id}")
        print(f"Total Attack Attempts   : {summary_data.get('total_attempts', 0)}")
        print(f"Attack Success Rate     : {int(summary_data.get('success_rate', 0) * 100)}%")
        print(f"Mean Pipeline Confidence: {summary_data.get('mean_pipeline_confidence', 0.0)}")
        print("Component Confidence Means:")
        for comp, mean_c in summary_data.get("component_means", {}).items():
            print(f"  - {comp:<20}: {mean_c}")
        print("--------------------------------------------------\n")
    except Exception as e:
        logging.getLogger(__name__).warning(f"Could not print benchmark summary: {e}")

    print("✅ Session Complete. Trace and Report uploaded to Supabase Storage.")
    print("==================================================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the AI Red Team framework against a local target.")
    parser.add_argument("target", help="Target type (e.g. 'chatbot', 'rag') OR a full HTTP URL (e.g. 'https://my-target.com')")
    parser.add_argument("--port", type=int, default=5173, help="Local port for benchmark targets")
    parser.add_argument("--iter", type=int, default=3, help="Max iterations to run")
    parser.add_argument("--mutations", type=int, default=3, help="Max mutations")
    parser.add_argument("--user_id", default="00000000-0000-0000-0000-000000000000", help="Supabase User ID")
    parser.add_argument("--declared_type", default=None, help="Pre-declared target type from blueprint (chatbot/rag/tool_agent)")
    
    args = parser.parse_args()
    asyncio.run(run(args.target, args.port, args.iter, args.mutations, args.user_id, args.declared_type))
