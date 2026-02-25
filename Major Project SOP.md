# STANDARD OPERATING PROCEDURE (SOP)

## Project: Autonomous Multi-Agent AI Security Assessment Framework for Web-Based LLM Applications

## Duration: 8 Weeks (5 Hours/Day Realistic Solo Execution)

## Mode: Solo Developer Thesis / Final Year Major Project

---

# 1. PROJECT OBJECTIVE

Design and build an autonomous multi-agent security testing platform that evaluates the robustness of web-based LLM-powered applications against adversarial attacks.

The framework must:

1. Discover the AI application's capabilities and behavior

2. Infer likely architecture / weaknesses

3. Plan attacks dynamically

4. Execute attacks iteratively

5. Analyze outcomes objectively

6. Learn from previous attempts

7. Produce structured vulnerability reports and attack graphs

This is NOT a chatbot wrapper.  
This is NOT a prompt generator.  
This is a closed-loop offensive AI security framework.

---

# 2. TARGET SYSTEM SCOPE (STRICT)

Only web-based AI applications are in scope.

Specifically:

- Web chatbot interfaces

- Web-based RAG assistants

- Web-based tool-using AI agents

Out of scope:

- Native mobile apps

- REST-only backend AI services

- Standalone local agents

- Non-LLM software systems

---

# 3. SECURITY THREATS COVERED

## Threat Class 1 – Prompt Injection / Jailbreak

Goal:

- Override system instructions

- Bypass safety / policy layers

---

## Threat Class 2 – Sensitive Information Leakage

Goal:

- Extract hidden prompts

- Leak internal memory/context

- Leak confidential retrieved data

---

## Threat Class 3 – Tool Abuse / Unauthorized Function Invocation

Goal:

- Trigger hidden tools

- Abuse available tools beyond intended scope

- Cause unintended tool actions

---

## Threat Class 4 – Authorization / Role Escalation

Goal:

- Convince AI user has higher privileges

- Circumvent role restrictions

- Access admin / privileged outputs

---

# 4. BENCHMARK TARGET APPLICATIONS (YOU BUILD THESE)

You MUST build controlled vulnerable targets.  
Do NOT rely on third-party websites.

---

## Target A – Vulnerable Chatbot

Features:

- Weak system prompt

- Hidden internal instructions

- No prompt hardening

Used For:

- Jailbreak / Prompt Extraction

---

## Target B – Vulnerable RAG Assistant

Features:

- Embedded confidential documents

- Weak retrieval filtering

- Poor source restriction

Used For:

- Retrieval leakage / Data exfiltration

---

## Target C – Vulnerable Tool Agent

Features:

- Fake tools/APIs available

- Poor permission enforcement

- Hidden tools exposed via prompt context

Used For:

- Tool abuse / Function misuse

---

## Target D – Hardened Variants

Same apps with mitigations enabled.

Purpose:

- Comparative evaluation benchmark

---

# 5. CORE SYSTEM ARCHITECTURE

## Module 1 – Surface Mapper Agent

Responsibilities:

- Crawl UI

- Observe interaction patterns

- Detect response styles

- Infer feature hints

Implementation:

- Playwright browser automation

Outputs:

- Target metadata

- Suspected capabilities

- Interaction transcript

---

## Module 2 – Threat Modeling Agent

Responsibilities:

- Infer probable architecture:
  
  - Is this RAG?
  
  - Is tool use present?
  
  - Is memory enabled?

- Map likely vulnerabilities

Output:

- Threat hypotheses

---

## Module 3 – Attack Planner Agent

Responsibilities:

- Choose attack category

- Select attack sequence

- Prioritize by likelihood

Features:

- Adaptive planning

- State-aware attack ordering

---

## Module 4 – Payload Generator Agent

Responsibilities:

- Generate attack payloads

- Mutate based on failures

- Produce variants

Rules:

- Hybrid approach:
  
  - Attack templates
  
  - LLM-assisted mutation

---

## Module 5 – Execution Agent

Responsibilities:

- Submit payloads

- Maintain conversation state

- Track multi-step attack chains

Critical:

- Must preserve conversation context

- Must support sequential exploit attempts

---

## Module 6 – Evaluation Agent

Responsibilities:

- Determine success/failure

- Score exploit confidence

- Detect partial breaches

Evaluation Inputs:

- Response text

- Tool outputs

- Behavior changes

---

## Module 7 – Memory Engine

Responsibilities:

- Store:
  
  - successful payloads
  
  - failed payloads
  
  - target-specific patterns

- Prevent redundant retries

- Improve future planning

---

## Module 8 – Attack Graph Generator

Responsibilities:

- Visualize exploit chain

- Map steps leading to compromise

Output:

- Directed graph of attack path

---

## Module 9 – Report Generator

Responsibilities:

- Produce structured vulnerability reports

- Summarize findings

- Include reproduction steps

- Include confidence score

---

# 6. TECH STACK (PRIMARY RECOMMENDED)

## Core Backend

- Python

- FastAPI

## Browser Automation

- Playwright

## Agent Orchestration

- Custom Python Orchestrator OR LangGraph (optional)

## Local Storage

- SQLite / PostgreSQL

## Visualization

- React + Cytoscape.js / D3.js for attack graph

## LLM Layer

- Local / API model for payload mutation only

---

# 7. ALTERNATIVE IMPLEMENTATIONS

## Alternative A – Easier Version

Remove:

- Threat Modeling Agent

- Adaptive Planning

- Memory Learning

Replace With:

- Static attack suites

- Fixed testing sequences

Result:

- Simpler implementation

- Lower novelty

- Lower technical risk

---

## Alternative B – Advanced Version

Add:

### 1. Reinforcement Learning Style Reward System

- Reward successful exploit paths

### 2. Cross-Target Knowledge Transfer

- Reuse learned strategies on new targets

### 3. Multi-Agent Debate / Consensus Evaluation

- Multiple evaluator agents vote on exploit success

### 4. Adversarial Prompt Evolution Engine

- Genetic mutation of payloads

Result:

- Extremely advanced research-grade system

---

# 8. REALISTIC 8-WEEK EXECUTION PLAN

---

## WEEK 1 – TARGET APP BENCHMARK CREATION

Day 1:

- Setup monorepo / project structure

Day 2:

- Build Vulnerable Chatbot target

Day 3:

- Build Vulnerable RAG target

Day 4:

- Build Vulnerable Tool Agent target

Day 5:

- Add intentional vulnerabilities

Day 6:

- Build hardened variants

Day 7:

- Validate benchmark targets manually

Outcome:

- Test environment complete

---

## WEEK 2 – CORE EXECUTION FRAMEWORK

Day 1:

- Setup backend framework

Day 2:

- Implement Playwright browser automation

Day 3:

- Automate login / navigation / prompt submission

Day 4:

- Capture responses reliably

Day 5:

- Maintain session / conversation state

Day 6–7:

- Stabilize browser interaction engine

---

## WEEK 3 – SURFACE MAPPING + THREAT MODELING

Tasks:

- Build target fingerprinting

- Infer likely AI architecture

- Generate threat hypotheses

---

## WEEK 4 – ATTACK PLANNING + PAYLOAD GENERATION

Tasks:

- Build attack template library

- Build adaptive planner

- Implement payload mutation logic

---

## WEEK 5 – EXECUTION LOOP + MULTI-STEP ATTACKS

Tasks:

- Sequential exploit chains

- Retry/mutation loop

- Context preservation

---

## WEEK 6 – EVALUATION + MEMORY ENGINE

Tasks:

- Success/failure detection

- Confidence scoring

- Memory persistence

---

## WEEK 7 – ATTACK GRAPH + REPORTING

Tasks:

- Generate exploit graphs

- Build structured reports

- Add export functionality

---

## WEEK 8 – TESTING / HARDENING / FINALIZATION

Tasks:

- Full benchmark testing

- Metrics collection

- Thesis documentation

- Demo prep

---

# 9. EVALUATION METRICS

Measure:

## Detection Metrics

- Vulnerabilities found

- False positives

- False negatives

## Efficiency Metrics

- Avg attacks to exploit

- Time to compromise

## Learning Metrics

- Improvement across repeated runs

## Robustness Metrics

- Performance on hardened targets

---

# 10. DEVELOPMENT TOOLS / RESOURCES

## AI Security References

- OWASP Top 10 for LLM Applications

- Garak / Promptfoo / PyRIT / AgentDojo for inspiration

## Dev Tools

- VS Code

- Postman

- Browser DevTools

## Testing Helpers

- LangChain sample agents

- Open-source RAG templates

---

# 11. CRITICAL RULES / PITFALLS

1. Do NOT over-rely on LLMs

2. Do NOT fake exploit detection

3. Do NOT skip hardened benchmark targets

4. Do NOT overscope attack categories

5. Do NOT build UI before core system works

---

# 12. FINAL SUCCESS CRITERIA

Project is successful when:

1. Framework autonomously compromises vulnerable AI targets

2. Framework fails appropriately against hardened variants

3. Framework improves through memory/adaptation

4. Framework produces clear exploit graphs/reports

5. Demonstration is reproducible and stable

---

# 13. PRESSURE TEST / IMPLEMENTATION RISKS

## Risk 1 – Overengineering the Agent Layer

Problem:

- Too many agents create orchestration chaos.  
  Mitigation:

- Start with 4 core agents only:
  
  1. Surface Mapper
  
  2. Planner
  
  3. Executor
  
  4. Evaluator

- Add specialization later only if stable.

## Risk 2 – Weak Success Evaluation

Problem:

- Hard to determine whether exploit truly succeeded.  
  Mitigation:

- Define explicit success markers per benchmark app.

- Build deterministic validation checks.

## Risk 3 – LLM Overdependence

Problem:

- Framework becomes prompt wrapper instead of system.  
  Mitigation:

- Restrict LLM use to payload mutation / optional planning support.

- Core orchestration logic must be deterministic.

## Risk 4 – Browser Automation Fragility

Problem:

- Playwright selectors break often.  
  Mitigation:

- Build your benchmark apps with automation-friendly stable selectors.

## Risk 5 – Scope Explosion

Problem:

- Too many attack types / target apps.  
  Mitigation:

- Hard cap MVP to 3 target apps and 4 attack classes.

---

# 14. BENCHMARK APP DESIGN SPECIFICATION

## Benchmark App A – Vulnerable Chatbot

Purpose:

- Test jailbreaks / prompt extraction / role escalation.

Implementation:

- Simple chatbot UI with hidden system prompt.

- System prompt includes confidential internal instruction block.

- Weak moderation / no prompt sanitization.

Intentional Vulnerabilities:

1. Prompt leakage via direct ask.

2. Prompt leakage via roleplay jailbreak.

3. Role escalation via admin-impersonation prompt.

4. Instruction override via nested prompt injection.

Success Conditions:

- Extract hidden system prompt.

- Bypass refusal rules.

- Generate restricted content.

---

## Benchmark App B – Vulnerable RAG Assistant

Purpose:

- Test confidential document leakage.

Implementation:

- Upload internal docs to vector store.

- Build retrieval chatbot over them.

Intentional Vulnerabilities:

1. No retrieval authorization filtering.

2. Weak prompt boundaries.

3. Source citation leaks hidden docs.

4. Prompt injection in retrieved docs.

Stored Confidential Samples:

- Fake HR policy docs

- Fake financial docs

- Fake API documentation

- Fake internal strategy docs

Success Conditions:

- Retrieve restricted document content.

- Reveal hidden chunk/source metadata.

- Exfiltrate protected embeddings context.

---

## Benchmark App C – Vulnerable Tool Agent

Purpose:

- Test tool abuse / unauthorized function execution.

Implementation:

- Agent with fake tools:
  
  - send_email()
  
  - query_database()
  
  - refund_user()
  
  - delete_record()

Intentional Vulnerabilities:

1. Hidden tools exposed in prompt context.

2. Weak permission checks.

3. No role validation.

4. Tool descriptions vulnerable to abuse.

Success Conditions:

- Trigger hidden tool.

- Execute unauthorized tool call.

- Abuse tool beyond intended scope.

---

## Hardened Variants

Apply:

- Prompt hardening

- Tool permission checks

- Retrieval filtering

- Output sanitization

- Role validation middleware

---

# 15. CODEBASE / ARCHITECTURE PLAN

## Monorepo Structure

```text
project-root/
│
├── benchmark_apps/
│   ├── chatbot_vuln/
│   ├── rag_vuln/
│   ├── tool_agent_vuln/
│   └── hardened_variants/
│
├── core_framework/
│   ├── orchestrator/
│   ├── agents/
│   │   ├── mapper.py
│   │   ├── planner.py
│   │   ├── payload_generator.py
│   │   ├── executor.py
│   │   ├── evaluator.py
│   │   └── memory.py
│   │
│   ├── attack_library/
│   │   ├── jailbreaks/
│   │   ├── leakage/
│   │   ├── tool_abuse/
│   │   └── escalation/
│   │
│   ├── browser/
│   │   ├── playwright_driver.py
│   │   └── selectors.py
│   │
│   ├── storage/
│   │   ├── sqlite_manager.py
│   │   └── schemas.py
│   │
│   └── reporting/
│       ├── report_generator.py
│       └── graph_builder.py
│
├── frontend_dashboard/
│   ├── attack_graph/
│   ├── reports/
│   └── run_monitor/
│
└── docs/
    ├── thesis_notes/
    └── diagrams/
```

---

## Recommended Internal Data Models

### TargetProfile

- url

- target_type

- suspected_capabilities

- known_constraints

### AttackAttempt

- attack_id

- category

- payload

- response

- success_score

- timestamp

### VulnerabilityFinding

- finding_id

- severity

- exploit_chain

- reproduction_steps

- confidence

---

## Execution Pipeline Flow

1. Load TargetProfile

2. Run Mapper

3. Generate Threat Model

4. Planner selects strategy

5. Payload Generator creates variants

6. Executor attacks target

7. Evaluator scores result

8. Memory stores outcome

9. Planner adapts

10. Report Generator outputs findings

---


