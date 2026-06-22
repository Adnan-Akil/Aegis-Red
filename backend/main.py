"""
backend/main.py

FastAPI server that exposes the Aegis-Red attack pipeline over HTTP.
Designed to be deployed separately (Railway, Render, VPS, etc.)
and called by the Next.js frontend on Vercel.
"""
import asyncio
import logging
import os
import sys
import uuid
from pathlib import Path

# ── Windows: switch to ProactorEventLoop so Playwright can spawn subprocesses ─
# The default SelectorEventLoop on Windows does not support create_subprocess_exec.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel, HttpUrl

# ── Ensure project root is on sys.path so src/ is importable ─────────────────
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("playwright").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Aegis-Red Backend",
    description="Autonomous AI Security Testing Framework API",
    version="1.0.0",
)

# CORS — allow Vercel frontend and local dev
_allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)


# ── Schemas ───────────────────────────────────────────────────────────────────
class RunRequest(BaseModel):
    url: str
    iterations: int = 5
    mutations: int = 2
    headless: bool = True
    user_id: str = "00000000-0000-0000-0000-000000000000"

class PDFRequest(BaseModel):
    markdown: str


# ── Attack runner (streaming generator) ───────────────────────────────────────
async def _stream_attack(req: RunRequest, disconnect: asyncio.Event) -> None:
    """
    Import and invoke the same run() logic as run_attack.py,
    but yield stdout lines over SSE so the frontend can stream them.
    """
    import io
    import contextlib

    # Lazy import after sys.path is set
    from src.agents.mapper import map_surface
    from src.agents.threat_modeler import generate_threat_model
    from src.agents.prober import active_probe
    from src.pipelines.graph import app as orchestrator_app
    from src.evaluation.report_generator import generate_cybersec_report
    from src.memory.supabase_manager import SupabaseManager
    from src.memory.schemas import TargetProfile
    import urllib.parse

    db = SupabaseManager()

    url = req.url
    iterations = req.iterations
    mutations = req.mutations
    user_id = req.user_id

    # Resolve target type from URL vs named target
    target_names = {
        "chatbot": "chatbot_vuln",
        "rag": "rag_vuln",
        "tool_agent": "tool_agent_vuln",
    }
    target_type_map = {
        "chatbot": "chatbot",
        "rag": "rag",
        "tool_agent": "tool_agent",
    }

    if url.startswith("http"):
        parsed = urllib.parse.urlparse(url)
        name = parsed.netloc or "external_target"
        target_type = "unknown"
        actual_target_type = "unknown"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
    else:
        name = target_names.get(url, "unknown_target")
        actual_target_type = target_type_map.get(url, url)
        port = 80
        url = f"http://localhost:{port}"

    def _emit(msg: str) -> str:
        return msg + "\n"

    # ── Recon phase — wrap so any failure streams cleanly instead of killing the socket ──
    try:
        yield _emit(f"🔍 Mapping attack surface for {name}...")
        mapper_data = await map_surface(url, target_name=name, target_type=actual_target_type)

        yield _emit(f"🧠 Generating threat model...")
        target = await generate_threat_model(
            url,
            target_name=name,
            base_target_type=actual_target_type,
            port=port,
            mapper_data=mapper_data,
        )

        discovered_url = mapper_data.get("discovery_url", url)
        discovered_sels = mapper_data.get("selectors")
        target.url = discovered_url
        target.discovery_url = discovered_url
        if discovered_sels:
            target.discovered_selectors = discovered_sels

        yield _emit(f"\n🕵️ Active Prober: Interrogating target to discover capabilities...")
        target = await active_probe(target)

    except Exception as recon_err:
        logger.error(f"Recon phase failed: {recon_err}", exc_info=True)
        yield _emit(f"\n❌ Recon failed: {recon_err}")
        yield _emit("Session aborted during reconnaissance.")
        return

    db.create_session(
        user_id=user_id,
        target_name=target.name,
        target_url=target.url,
        target_type=target.target_type,
    )
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
        "status": "planning",
    }

    graph_config = {
        "configurable": {"thread_id": session_id},
        "recursion_limit": 150,
    }

    yield _emit(f"\n==================================================")
    yield _emit(f"🚀 Starting Attack Session: {session_id}")
    yield _emit(f"🎯 Target: {target.name} ({target.target_type}) at {target.url}")
    yield _emit(f"==================================================\n")


    last_attempt = None
    max_score = 0.0
    markdown_trace = f"# Aegis-Red Attack Trace: {session_id}\n"
    markdown_trace += f"**Target**: {target.url}\n**Type**: {target.target_type}\n\n---\n\n"
    _iter_verdict_written = True

    try:
        async for event in orchestrator_app.astream(initial_state, graph_config, stream_mode="updates"):
            # Abort if client disconnected
            if disconnect.is_set():
                logger.info(f"[{session_id}] Client disconnected — aborting stream.")
                break

            for node_name, state_update in event.items():
                if node_name == "planner":
                    if state_update.get("status") == "done":
                        continue
                    if not _iter_verdict_written:
                        markdown_trace += "**Response**: *(none — executor failed or timed out)*\n\n"
                        markdown_trace += "**Verdict**: INTERRUPTED (Score: 0.0)\n**Reasoning**: Iteration did not complete.\n\n---\n\n"
                        _iter_verdict_written = True

                    iteration = state_update.get("iteration", 0)
                    msg = f"\n[Iteration {iteration}] 🔄 Planning next attack vector..."
                    yield _emit(msg)
                    db.add_log("PLANNING", f"Planning iteration {iteration}", "info")
                    markdown_trace += f"## Iteration {iteration}\n"
                    _iter_verdict_written = False

                elif node_name == "executor":
                    attempt = state_update.get("current_attempt")
                    if attempt:
                        last_attempt = attempt
                        sent_text = attempt.payload_text.replace("\n", " ")
                        if len(sent_text) > 100:
                            sent_text = sent_text[:100] + "..."
                        yield _emit(f" ├── 🗡️ Attack: {attempt.category.upper()} (Payload ID: {attempt.payload_id})")
                        yield _emit(f' ├── 💬 Sent: "{sent_text}"')
                        db.add_log("ATTACK_SENT", f"Sent {attempt.category} payload", "action")
                        markdown_trace += f"### {attempt.category.upper()}\n**Payload**:\n> {attempt.payload_text}\n\n"

                elif node_name == "evaluator":
                    eval_res = state_update.get("current_evaluation")
                    if eval_res and last_attempt:
                        max_score = max(max_score, eval_res.score)
                        rcvd_text = last_attempt.response_text.replace("\n", " ")
                        preview_len = 250 if eval_res.score > 0 else 100
                        if len(rcvd_text) > preview_len:
                            rcvd_text = rcvd_text[:preview_len] + "..."
                        yield _emit(f' ├── 🛡️ Rcvd: "{rcvd_text}" ({last_attempt.duration_ms}ms)')

                        reason = (
                            eval_res.reasoning
                            .replace("VERDICT: YES\n", "")
                            .replace("VERDICT: NO\n", "")
                            .replace("VERDICT: PARTIAL\n", "")
                            .strip()
                        )
                        verdict_icon = "✅" if eval_res.score == 1.0 else ("⚠️" if eval_res.score > 0 else "❌")
                        yield _emit(f" └── {verdict_icon} Verdict: {eval_res.verdict.upper()} (Score {eval_res.score}) - {reason}")

                        db.add_log(
                            "EVALUATION",
                            f"Verdict: {eval_res.verdict.upper()} (Score: {eval_res.score})",
                            "info" if eval_res.score == 0 else "warning",
                        )
                        markdown_trace += f"**Response**:\n> {last_attempt.response_text}\n\n"
                        markdown_trace += f"**Verdict**: {eval_res.verdict.upper()} (Score: {eval_res.score})\n**Reasoning**: {reason}\n\n---\n\n"
                        _iter_verdict_written = True

                        for indicator in eval_res.matched_indicators:
                            if indicator.startswith("SECRET_LEAK:"):
                                secret_val = indicator.split("SECRET_LEAK:")[1]
                                yield _emit(f"\n     🚨 CRITICAL LEAK CAUGHT: {secret_val}")
                                db.add_finding("SECRET_LEAK", secret_val)

    except asyncio.CancelledError:
        yield _emit("\n\n⚠️  Session cancelled.")
        markdown_trace += "\n> ⚠️ **Session was cancelled before completion.**\n"

    except Exception as e:
        logger.error(f"Orchestrator crashed: {e}", exc_info=True)
        yield _emit(f"\n\n❌ Session crashed: {e}")
        markdown_trace += f"\n> ❌ **Session terminated with error:** `{str(e)[:300]}`\n"

    # Finalize
    final_verdict = "Secure"
    final_score = 0.0
    if max_score == 1.0:
        final_verdict = "Critical"
        final_score = 10.0
    elif max_score > 0:
        final_verdict = "Warning"
        final_score = 5.0

    yield _emit("\n==================================================")
    yield _emit("Generating formal penetration test report...")
    report_content = await generate_cybersec_report(markdown_trace, target.url, session_id)

    db.complete_session(
        verdict=final_verdict,
        overall_score=final_score,
        payload_content=markdown_trace,
        report_content=report_content,
    )

    yield _emit(f"✅ Session Complete. Trace and Report uploaded to Supabase Storage.")
    yield _emit("==================================================\n")


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health() -> dict:
    import asyncio
    loop = asyncio.get_running_loop()
    return {"status": "ok", "service": "aegis-red-backend", "loop_type": str(type(loop))}


@app.post("/run")
async def run_attack(body: RunRequest, request: Request) -> StreamingResponse:
    # Basic validation
    safe_targets = {"chatbot", "rag", "tool_agent"}
    is_valid_url = body.url.startswith("http://") or body.url.startswith("https://")
    is_safe_target = body.url in safe_targets

    if not is_valid_url and not is_safe_target:
        raise HTTPException(
            status_code=400,
            detail="Invalid target. Must be a valid URL (http/https) or a predefined local target name.",
        )

    disconnect_event = asyncio.Event()

    async def streamer():
        try:
            async for chunk in _stream_attack(body, disconnect_event):
                yield chunk
        except asyncio.CancelledError:
            disconnect_event.set()

    return StreamingResponse(
        streamer(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disables Nginx buffering for real-time streaming
        },
    )

@app.post("/api/generate-pdf")
def generate_pdf(req: PDFRequest):
    import markdown
    from jinja2 import Environment, FileSystemLoader

    html_content = markdown.markdown(
        req.markdown,
        extensions=['extra', 'fenced_code', 'tables']
    )
    
    import re
    html_content = re.sub(
        r'<em>(Figure\b[^<]*)</em>',
        r'<em class="figure-caption">\1</em>',
        html_content
    )
    
    # ROOT is defined as the project root.
    template_dir = ROOT / "backend" / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template("report.html")
    rendered_html = template.render(content=html_content)

    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=rendered_html).write_pdf()
    except Exception as e:
        import sys
        error_msg = str(e)
        detail = (
            f"PDF Generation failed: {error_msg}. "
            "If running locally on Windows, this is usually because WeasyPrint requires the GTK3 runtime "
            "libraries (Cairo, Pango) to be installed. "
            "The hosted Hugging Face Docker deployment includes these libraries and will work out of the box."
        )
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=detail)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=report.pdf"
        }
    )
