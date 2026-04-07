import asyncio
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

from src.memory.sqlite_manager import SQLiteManager

async def generate_report(target_id: str, output_dir: str = "reports"):
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    report_lines = []
    report_lines.append(f"# Security Assessment Report: {target_id}")
    report_lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    async with SQLiteManager() as db:
        # Get target info
        async with db._db.execute("SELECT * FROM targets WHERE target_id = ?", (target_id,)) as cursor:
            target_row = await cursor.fetchone()
            
        if not target_row:
            print(f"Target '{target_id}' not found in database.")
            return
            
        report_lines.append("## 🎯 Target Overview")
        report_lines.append(f"- **Name:** {target_row['name']}")
        report_lines.append(f"- **Type:** {target_row['target_type']}")
        report_lines.append(f"- **URL:** {target_row['url']}")
        report_lines.append("")
        
        # Get findings
        async with db._db.execute(
            "SELECT * FROM vulnerability_findings WHERE target_id = ? ORDER BY confidence DESC", 
            (target_id,)
        ) as cursor:
            findings = await cursor.fetchall()
            
        report_lines.append("## 🚨 Executive Summary & Findings")
        if not findings:
            report_lines.append("No successful exploits recorded for this target.")
            report_lines.append("")
        else:
            report_lines.append(f"Discovered **{len(findings)}** vulnerabilities during testing.")
            for f in findings:
                report_lines.append(f"### {f['title']} (Severity: {f['severity'].upper()})")
                report_lines.append(f"- **Category:** {f['category']}")
                report_lines.append(f"- **Confidence:** {f['confidence']}")
                report_lines.append(f"\n**Description:**\n{f['description']}")
                report_lines.append("")
                
        # Build Attack Graph using Mermaid
        report_lines.append("## 🗺️ Attack Graph")
        report_lines.append("This graph represents the sequence of payloads and mutations attempted across all sessions.")
        report_lines.append("")
        report_lines.append("```mermaid")
        report_lines.append("graph TD")
        
        # Get attempts
        async with db._db.execute("""
            SELECT a.session_id, a.payload_id, a.parent_payload_id, e.verdict, a.turn_index
            FROM attack_attempts a
            LEFT JOIN evaluation_results e ON a.attempt_id = e.attempt_id
            WHERE a.target_id = ?
            ORDER BY a.session_id, a.timestamp
        """, (target_id,)) as cursor:
            attempts = await cursor.fetchall()
            
        # Group by session
        sessions = {}
        for row in attempts:
            sid = row['session_id'][:8]
            if sid not in sessions:
                sessions[sid] = []
            sessions[sid].append(row)
            
        for sid, rows in sessions.items():
            report_lines.append(f"    subgraph Session_{sid}")
            for i, row in enumerate(rows):
                pid = row['payload_id']
                parent_pid = row['parent_payload_id']
                verdict = row['verdict'] or 'unknown'
                
                # Sanitize IDs for mermaid
                safe_pid = pid.replace("-", "_")
                node_id = f"{sid}_{safe_pid}"
                
                # Add node
                icon = "❌" if verdict == "fail" else "⚠️" if verdict == "partial" else "✅"
                report_lines.append(f"        {node_id}[\"{pid} <br> Verdict: {verdict.upper()} {icon}\"]")
                
                # Color code
                if verdict == "success":
                    report_lines.append(f"        style {node_id} fill:#d4edda,stroke:#28a745,stroke-width:2px")
                elif verdict == "fail":
                    report_lines.append(f"        style {node_id} fill:#f8d7da,stroke:#dc3545,stroke-width:2px")
                elif verdict == "partial":
                    report_lines.append(f"        style {node_id} fill:#fff3cd,stroke:#ffc107,stroke-width:2px")
                
                # Link
                if parent_pid:
                    safe_parent = parent_pid.replace("-", "_")
                    parent_node_id = f"{sid}_{safe_parent}"
                    report_lines.append(f"        {parent_node_id} --> {node_id}")
                
            report_lines.append("    end")
            
        report_lines.append("```")
        report_lines.append("")
        
        # Attack Details log
        report_lines.append("## 📜 Attack Logs")
        
        async with db._db.execute("""
            SELECT a.session_id, a.payload_id, a.payload_text, a.response_text, e.verdict, e.reasoning
            FROM attack_attempts a
            LEFT JOIN evaluation_results e ON a.attempt_id = e.attempt_id
            WHERE a.target_id = ?
            ORDER BY a.timestamp DESC
        """, (target_id,)) as cursor:
            details = await cursor.fetchall()
            
        for row in details:
            sid = row['session_id'][:8]
            report_lines.append(f"### Payload: {row['payload_id']} (Session: {sid})")
            report_lines.append(f"**Verdict:** {row['verdict'].upper() if row['verdict'] else 'UNKNOWN'}")
            report_lines.append(f"\n**Payload Sent:**\n```text\n{row['payload_text']}\n```")
            report_lines.append(f"\n**Target Response:**\n```text\n{row['response_text']}\n```")
            report_lines.append(f"\n**Evaluator Reasoning:**\n> {row['reasoning']}")
            report_lines.append("\n---\n")

    report_path = out_dir / f"report_{target_id}.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
    print(f"✅ Report generated successfully: {report_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Security Report for a target")
    parser.add_argument("--target", type=str, required=True, help="Target ID (e.g., chatbot, rag)")
    parser.add_argument("--out", type=str, default="reports", help="Output directory")
    args = parser.parse_args()
    
    asyncio.run(generate_report(args.target, args.out))
