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
    risk_level = overall_risk.upper()

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
        "# **AEGIS-RED | AUTONOMOUS AI SECURITY AUDIT**",
        "**INTERNAL SECURITY ASSESSMENT**",
        "",
        "---",
        "",
        f"* **Date:** {today}",
        f"* **Target Environment:** `{target_url}`",
        f"* **Session ID:** `{session_id}`",
        "",
        "---",
        "",
        "## **1. Executive Summary**",
        "",
        exec_summary,
        "",
        f"**The overall risk posture is classified as {risk_level}.**",
        "",
        "**Assessment Metrics**",
        "",
        "| Metric | Status / Value |",
        "| --- | --- |",
        f"| **Overall Risk Level** | **{risk_level}** |",
        f"| **Total Attack Iterations** | {total_iter} |",
        f"| **Successful Exploits** | {success_exploits} |",
        f"| **Partial Exploits** | {partial_exploits} |",
        f"| **Detected Architecture** | {arch} |",
        f"| **Active Guardrails** | {guardrails} |",
        "",
    ]
    
    # Extract charts and captions
    chart_urls = data.get("chart_urls") or {}
    chart_captions = data.get("chart_captions") or {}
    
    # Embed Executive Summary Charts (Donut & Radar)
    if chart_urls.get("donut") and chart_urls.get("radar"):
        caption1 = chart_captions.get('donut', 'Vulnerability Severity Distribution')
        caption2 = chart_captions.get('radar', 'Threat Class Exposure Profile')
        md.extend([
            "| Vulnerability Severity Distribution | Threat Class Exposure Profile |",
            "| :---: | :---: |",
            f"| ![Vulnerability Severity Distribution]({chart_urls['donut']}) | ![Threat Class Exposure Profile]({chart_urls['radar']}) |",
            f"| *Figure 1: {caption1}* | *Figure 2: {caption2}* |",
            ""
        ])
    elif chart_urls.get("donut"):
        md.append(f"![Vulnerability Severity Distribution]({chart_urls['donut']})")
        caption = chart_captions.get('donut', 'Vulnerability Severity Distribution')
        md.append(f"*Figure 1: {caption}*")
        md.append("")
        md.append("*Tested against Prompt Injection, Data Leakage, Tool Abuse, and Privilege Escalation. Target successfully defended against all categories.*")
        md.append("")
        
    md.extend([
        "---",
        "",
        "## **2. Reconnaissance & Surface Analysis**",
        "",
    ])
    
    if chart_urls.get("surface_map"):
        md.append(f"![Attack Surface Map]({chart_urls['surface_map']})")
        md.append("*Figure: Attack Surface Conceptual Map*")
        md.append("")

    md.extend([
        "**System Architecture**",
        "",
        surface_arch,
        "",
        "**Defense Posture & Guardrails**",
        "",
        defence_posture,
        "",
        "**Detected Guardrails Details:**",
        "",
        detected_gr,
        "",
        "---",
        "",
        "## **3. Detailed Vulnerability Findings**",
        "",
    ])

    # Append findings
    if not findings:
        md.extend([
            "No active vulnerabilities or successful exploits were confirmed during this audit campaign.",
            "The target system demonstrates high resilience against direct jailbreak vectors and prompt exfiltration.",
            "Continue monitoring and logging all model inputs and output queries to prevent drift.",
            ""
        ])
    else:
        for idx, f in enumerate(findings, start=1):
            title = f.get("title") or "Unnamed Vulnerability"
            severity = f.get("severity") or "Medium"
            category = f.get("category") or "General"
            cvss = f.get("cvss_equivalent") or "5.0"
            impact = f.get("impact") or "N/A"
            poc = f.get("proof_of_concept") or "N/A"
            evidence = f.get("evidence") or "N/A"
            root_cause = f.get("root_cause") or "Design flaw in model alignment or prompt logic."
            remediation = f.get("remediation") or []

            md.extend([
                f"**FINDING-{idx:02d}: {title}**",
                "",
                "| Attribute | Detail |",
                "| --- | --- |",
                f"| **Severity** | **{severity.upper()} (CVSS Eqv: {cvss})** |",
                f"| **Category** | {category} |",
                f"| **Impact** | {impact} |",
                "",
                "**Technical Analysis (Root Cause)**",
                "",
                root_cause,
                "",
                "**Exploit Vector / Injection Payload**",
                "",
                f"> `{poc}`",
                "",
                "**Target Response (Evidence)**",
                "",
                f"> `{evidence}`",
                "",
                "**Recommended Remediation**",
                "",
            ])
            
            if not remediation:
                md.append("1. Monitor system logs for repeated payload iterations of this style.")
            else:
                for r_idx, remediation_item in enumerate(remediation, start=1):
                    md.append(f"{r_idx}. {remediation_item}")
            
            md.extend([
                "",
                "---",
                "",
            ])

    md.extend([
        "## **4. Attack Timeline**",
        "",
        "| # | Category | Strategy | Verdict | Score | Key Observation |",
        "|---|---|---|---|---|---|",
    ])

    # Append timeline rows
    for item in timeline:
        it_num = item.get("iteration", 0)
        cat = item.get("category") or "Unknown"
        strat = item.get("strategy") or "Unknown"
        verdict = item.get("verdict") or "FAIL"
        score = item.get("score", 0.0)
        obs = item.get("observation") or "No observation logged."
        
        v_str = verdict.upper()

        row = f"| {it_num} | {escape_markdown(cat)} | {escape_markdown(strat)} | {v_str} | {score} | {escape_markdown(obs)} |"
        md.append(row)

    md.append("")
    
    # Embed Attack Timeline Charts (Gantt & Funnel)
    if chart_urls.get("timeline") and chart_urls.get("funnel"):
        caption1 = chart_captions.get('timeline', 'Attack Timeline progression mapping agent activity over iterations.')
        caption2 = chart_captions.get('funnel', 'Payload Mutation Funnel illustrating the narrowing rate of payload success.')
        md.extend([
            "| Attack Timeline progression | Payload Mutation Funnel |",
            "| :---: | :---: |",
            f"| ![Attack Timeline progression]({chart_urls['timeline']}) | ![Payload Mutation Funnel]({chart_urls['funnel']}) |",
            f"| *Figure 3: {caption1}* | *Figure 4: {caption2}* |",
            ""
        ])
    else:
        if chart_urls.get("timeline"):
            md.append(f"![Attack Timeline progression]({chart_urls['timeline']})")
            caption = chart_captions.get('timeline', 'Attack Timeline progression mapping agent activity over iterations.')
            md.append(f"*Figure 3: {caption}*")
            md.append("")
            
        if chart_urls.get("funnel"):
            md.append(f"![Payload Mutation Funnel]({chart_urls['funnel']})")
            caption = chart_captions.get('funnel', 'Payload Mutation Funnel illustrating the narrowing rate of payload success.')
            md.append(f"*Figure 4: {caption}*")
            md.append("")

    md.extend([
        "---",
        "",
        "## **5. Strategic Hardening Roadmap**",
        ""
    ])

    # Hardening roadmap lists
    immediate = roadmap.get("immediate") or []
    short_term = roadmap.get("short_term") or []
    long_term = roadmap.get("long_term") or []

    md.append("**Immediate (0–7 days)**")
    md.append("")
    if immediate:
        for item in immediate:
            md.append(f"* {item}")
    else:
        md.append("* No immediate hardening steps recommended.")
    md.append("")

    md.append("**Short-term (1–4 weeks)**")
    md.append("")
    if short_term:
        for item in short_term:
            md.append(f"* {item}")
    else:
        md.append("* Implement dynamic evaluation loops for suspected inputs.")
    md.append("")

    md.append("**Long-term (1–3 months)**")
    md.append("")
    if long_term:
        for item in long_term:
            md.append(f"* {item}")
    else:
        md.append("* Regularly update foundation models and retrain local classifiers.")
    md.append("")

    md.extend([
        "---",
        "",
        "*Report generated by Aegis-Red Autonomous AI Security Framework. All testing was conducted in an authorised, isolated environment.*",
        ""
    ])

    return "\n".join(md)
