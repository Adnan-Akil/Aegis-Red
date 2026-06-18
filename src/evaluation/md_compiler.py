"""
md_compiler.py

Deterministic Markdown compiler for generating cybersecurity audit reports
and trace logs from structured data models.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

@dataclass
class TraceIteration:
    iteration: int
    category: str = "Unknown"
    payload_text: str = ""
    response_text: Optional[str] = None
    verdict: Optional[str] = None
    score: float = 0.0
    reasoning: Optional[str] = None
    status: str = "pending"  # "completed", "interrupted", "cancelled", "error"

class TraceBuilder:
    def __init__(self, session_id: str, target_url: str, target_type: str):
        self.session_id: str = session_id
        self.target_url: str = target_url
        self.target_type: str = target_type
        self.iterations: List[TraceIteration] = []
        self.termination_marker: Optional[str] = None

    def start_iteration(self, iteration_num: int):
        # If there is a pending iteration that never finished, mark it as interrupted
        self.close_pending("interrupted", "Iteration did not complete — executor exception or timeout.")
        self.iterations.append(TraceIteration(iteration=iteration_num))

    def add_payload(self, category: str, payload_text: str):
        if self.iterations:
            self.iterations[-1].category = category
            self.iterations[-1].payload_text = payload_text

    def add_evaluation(self, response_text: str, verdict: str, score: float, reasoning: str):
        if self.iterations:
            current = self.iterations[-1]
            current.response_text = response_text
            current.verdict = verdict
            current.score = score
            current.reasoning = reasoning
            current.status = "completed"

    def close_pending(self, status: str, reasoning: str, response_text: Optional[str] = None):
        if self.iterations and self.iterations[-1].status == "pending":
            current = self.iterations[-1]
            current.status = status
            current.reasoning = reasoning
            current.response_text = response_text
            current.score = 0.0
            current.verdict = status.upper()

    def set_termination(self, marker_type: str, message: str):
        if marker_type == "cancelled":
            self.termination_marker = f"\n> ⚠️ **Session was cancelled before completion.**\n"
        elif marker_type == "error":
            self.termination_marker = f"\n> ❌ **Session terminated with error:** `{message}`\n"

    def render(self) -> str:
        # Generate Markdown deterministically
        md = [
            f"# Aegis-Red Attack Trace: {self.session_id}",
            f"**Target**: {self.target_url}",
            f"**Type**: {self.target_type}",
            "",
            "---",
            ""
        ]

        for it in self.iterations:
            md.append(f"## Iteration {it.iteration}")
            md.append(f"### {it.category.upper()}")
            md.append("**Payload**:")
            md.append(format_blockquote(it.payload_text))
            md.append("")
            
            md.append("**Response**:")
            if it.response_text is not None:
                md.append(format_blockquote(it.response_text))
            else:
                if it.status == "interrupted":
                    md.append("> *(none — executor failed or timed out)*")
                elif it.status == "cancelled":
                    md.append("> *(none — session cancelled)*")
                elif it.status == "error":
                    md.append("> *(none — session crashed)*")
                else:
                    md.append("> *(none)*")
            md.append("")

            verdict_str = it.verdict or "UNKNOWN"
            reasoning_str = it.reasoning or "No reasoning provided."
            md.append(f"**Verdict**: {verdict_str} (Score: {it.score})")
            md.append(f"**Reasoning**: {reasoning_str}")
            md.append("")
            md.append("---")
            md.append("")

        if self.termination_marker:
            md.append(self.termination_marker)

        return "\n".join(md)

def escape_markdown(text: Optional[str]) -> str:
    """Escapes pipes and backslashes to prevent breaking markdown tables."""
    if not text:
        return ""
    # Replace markdown pipes
    return text.replace("|", "\\|").replace("\n", " ").strip()

def format_blockquote(text: Optional[str], truncate_len: int = 1000) -> str:
    """Formats a block of text as a clean markdown blockquote, truncating if too long."""
    if not text:
        return "> *(No text content provided)*"
    
    cleaned = text.strip()
    if len(cleaned) > truncate_len:
        cleaned = cleaned[:truncate_len] + "\n\n*(Truncated due to length)*"
    
    # Prefix every line with >
    lines = [f"> {line}" for line in cleaned.split("\n")]
    return "\n".join(lines)

def compile_report(data: Dict[str, Any], target_url: str, session_id: str) -> str:
    """
    Deterministically compiles structured LLM JSON output into a high-fidelity
    Markdown cybersecurity audit report.
    """
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    # Extract data with safe defaults
    exec_summary = data.get("executive_summary") or "No executive summary provided."
    overall_risk = data.get("overall_risk") or "Low"
    
    # Map risk to emoji representation
    risk_emojis = {
        "critical": "🔴 Critical",
        "high": "🟠 High",
        "medium": "🟡 Medium",
        "low": "🟢 Low"
    }
    risk_level = risk_emojis.get(overall_risk.lower(), f"🟢 {overall_risk}")

    metrics = data.get("metrics") or {}
    total_iter = metrics.get("total_iterations", 0)
    success_exploits = metrics.get("successful_exploits", 0)
    partial_exploits = metrics.get("partial_exploits", 0)
    arch = metrics.get("architecture") or "Unknown"
    guardrails = metrics.get("guardrails") or "None detected"

    recon = data.get("reconnaissance") or {}
    surface_arch = recon.get("surface_architecture") or "No architecture information available."
    detected_gr = recon.get("detected_guardrails") or "No guardrail information available."
    defence_posture = recon.get("defence_posture") or "No defence posture analysis available."

    timeline = data.get("attack_timeline") or []
    findings = data.get("findings") or []
    roadmap = data.get("hardening_roadmap") or {}
    
    # ─── 1. Title & Header ───
    md = [
        "# 🔴 Aegis-Red | AI Penetration Test Report",
        "> **Autonomous AI Security Audit** — Confidential | Aegis-Red Framework",
        "",
        f"**Date:** {today} | **Target:** `{target_url}` | **Session ID:** `{session_id}`",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        "",
        exec_summary,
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| **Overall Risk Level** | {risk_level} |",
        f"| **Total Iterations** | {total_iter} |",
        f"| **Successful Exploits** | {success_exploits} |",
        f"| **Partial Exploits** | {partial_exploits} |",
        f"| **Detected Architecture** | {arch} |",
        f"| **Guardrails Detected** | {guardrails} |",
        "",
        "---",
        "",
        "## 2. Reconnaissance & Surface Analysis",
        "",
        f"**Surface Architecture:** {surface_arch}",
        "",
        f"**Detected Guardrails:** {detected_gr}",
        "",
        f"**Defence Posture:** {defence_posture}",
        "",
        "---",
        "",
        "## 3. Attack Timeline",
        "",
        "| # | Category | Strategy | Verdict | Score | Key Observation |",
        "|---|---|---|---|---|---|",
    ]

    # Append timeline rows
    for item in timeline:
        it_num = item.get("iteration", 0)
        cat = item.get("category") or "Unknown"
        strat = item.get("strategy") or "Unknown"
        verdict = item.get("verdict") or "FAIL"
        score = item.get("score", 0.0)
        obs = item.get("observation") or "No observation logged."
        
        # Add emoji prefix to verdict
        verdict_upper = verdict.upper()
        if "SUCCESS" in verdict_upper:
            v_str = f"✅ {verdict_upper}"
        elif "PARTIAL" in verdict_upper:
            v_str = f"⚠️ {verdict_upper}"
        elif "INTERRUPTED" in verdict_upper:
            v_str = f"⚠️ {verdict_upper}"
        elif "CANCELLED" in verdict_upper:
            v_str = f"⚠️ {verdict_upper}"
        else:
            v_str = f"❌ {verdict_upper}"

        row = f"| {it_num} | {escape_markdown(cat)} | {escape_markdown(strat)} | {v_str} | {score} | {escape_markdown(obs)} |"
        md.append(row)

    md.extend([
        "",
        "---",
        "",
        "## 4. Confirmed Vulnerabilities",
        ""
    ])

    # Append findings
    if not findings:
        md.append("No active vulnerabilities or successful exploits were confirmed during this audit campaign.")
        md.append("The target system demonstrates high resilience against direct jailbreak vectors and prompt exfiltration.")
        md.append("Continue monitoring and logging all model inputs and output queries to prevent drift.")
    else:
        for idx, f in enumerate(findings, 1):
            title = f.get("title") or "Unnamed Vulnerability"
            severity = f.get("severity") or "Medium"
            category = f.get("category") or "General"
            cvss = f.get("cvss_equivalent") or "5.0"
            impact = f.get("impact") or "N/A"
            poc = f.get("proof_of_concept")
            evidence = f.get("evidence")
            root_cause = f.get("root_cause") or "Design flaw in model alignment or prompt logic."
            remediation = f.get("remediation") or []

            # Severity color/emoji mapping
            sev_upper = severity.upper()
            if "CRITICAL" in sev_upper:
                sev_str = "🔴 Critical"
            elif "HIGH" in sev_upper:
                sev_str = "🟠 High"
            elif "MEDIUM" in sev_upper:
                sev_str = "🟡 Medium"
            else:
                sev_str = "🟢 Low"

            md.extend([
                f"### 🚨 FINDING-{idx} — {title}",
                "",
                "| Field | Detail |",
                "|---|---|",
                f"| **Severity** | {sev_str} |",
                f"| **Category** | {category} |",
                f"| **CVSS-Equivalent** | {cvss} |",
                f"| **Impact** | {impact} |",
                "",
                "**Proof of Concept Payload:**",
                format_blockquote(poc),
                "",
                "**Target Response (Evidence):**",
                format_blockquote(evidence),
                "",
                "#### Root Cause",
                root_cause,
                "",
                "#### Remediation"
            ])

            if not remediation:
                md.append("1. Monitor system logs for repeated payload iterations of this style.")
            else:
                for rem_idx, item in enumerate(remediation, 1):
                    md.append(f"{rem_idx}. {item}")
            
            md.append("")

    md.extend([
        "---",
        "",
        "## 5. Strategic Hardening Roadmap",
        ""
    ])

    # Hardening roadmap lists
    immediate = roadmap.get("immediate") or []
    short_term = roadmap.get("short_term") or []
    long_term = roadmap.get("long_term") or []

    md.append("### Immediate (0–7 days)")
    if immediate:
        for item in immediate:
            md.append(f"- {item}")
    else:
        md.append("- No immediate hardening steps recommended.")
    md.append("")

    md.append("### Short-term (1–4 weeks)")
    if short_term:
        for item in short_term:
            md.append(f"- {item}")
    else:
        md.append("- Implement dynamic evaluation loops for suspected inputs.")
    md.append("")

    md.append("### Long-term (1–3 months)")
    if long_term:
        for item in long_term:
            md.append(f"- {item}")
    else:
        md.append("- Regularly update foundation models and retrain local classifiers.")
    md.append("")

    md.extend([
        "---",
        "",
        "*Report generated by Aegis-Red Autonomous AI Security Framework. All testing was conducted in an authorised, isolated environment.*",
        ""
    ])

    return "\n".join(md)
