# Aegis-Red 🛡️🔴

### Autonomous Multi-Agent AI Security Assessment Framework for Web-Based LLM Applications

*A B.Tech Computer Science & Engineering Capstone Project | Amity University Dubai*

🚀 **Live Demo:** [https://aegis-red-vz8g.vercel.app/](https://aegis-red-vz8g.vercel.app/)

---

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js-000000.svg?style=flat&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![LangGraph](https://img.shields.io/badge/Orchestrator-LangGraph-FF6F61.svg?style=flat&logo=langchain&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![Playwright](https://img.shields.io/badge/Automation-Playwright-2EAD33.svg?style=flat&logo=playwright&logoColor=white)](https://playwright.dev)
[![Supabase](https://img.shields.io/badge/Auth-Supabase-3ECF8E.svg?style=flat&logo=supabase&logoColor=white)](https://supabase.com)
[![Deploy on Railway](https://img.shields.io/badge/Deploy_Backend-Railway-0B0D0E.svg?style=flat&logo=railway&logoColor=white)](https://railway.app)
[![Deploy on Vercel](https://img.shields.io/badge/Deploy_Frontend-Vercel-000000.svg?style=flat&logo=vercel&logoColor=white)](https://vercel.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Aegis-Red is a **closed-loop, autonomous, multi-agent offensive security framework** designed to navigate, profile, and stress-test LLM-powered web applications. 

Traditional vulnerability scanners look for static patterns (like SQL injections or XSS) using direct API endpoints. However, modern enterprise AI applications are conversational, non-deterministic, and context-dependent. Aegis-Red addresses this gap by mimicking a human penetration tester: it interacts directly with the browser DOM, explores the target interface, infers the backend architecture, and dynamically mutates its adversarial prompts based on real-time feedback to bypass safety filters.

---

## 📌 Table of Contents

- [⚡ Quickstart](#-quickstart)
- [📖 1. Executive Summary & Vision](#1-executive-summary--vision)
- [🧠 2. Core Philosophy & Design Strategy](#2-core-philosophy--design-strategy)
- [🏛️ 3. System Architecture & Flows](#3-system-architecture--flows)
- [💻 4. Deep-Dive Tech Stack](#4-deep-dive-tech-stack)
- [🛡️ 5. Key Innovations & Advanced Exploitation](#5-key-innovations--advanced-exploitation)
- [🧪 6. The Benchmark Target Ecosystem](#6-the-benchmark-target-ecosystem)
- [📊 7. Performance & Evaluation Metrics](#7-performance--evaluation-metrics)
- [⚙️ 8. Setup & Installation](#8-setup--installation)
- [🚀 9. Usage & Execution](#9-usage--execution)
- [🤝 10. Contributions & Collaboration](#10-contributions--collaboration)

---

## 🖼️ Application Interface

<p align="center">
  <img src="assets/homepage_UI.png" width="48%" alt="Aegis-Red Homepage Dashboard" />
  <img src="assets/reportspage_UI.png" width="48%" alt="Aegis-Red Generated Reports" />
</p>
<p align="center">
  <img src="assets/loginpage_UI.png" width="48%" alt="Aegis-Red Login Screen" />
  <img src="assets/logspage_UI.png" width="48%" alt="Aegis-Red Real-Time Exploit Logs" />
</p>

---

## ⚡ Quickstart

### Windows
```bat
git clone https://github.com/Adnan-Akil/Aegis-Red.git
cd Aegis-Red
setup.bat          :: installs venv, deps, playwright, and frontend
start.bat          :: starts backend (port 8000) + dashboard (port 3000)
```

### Linux / macOS
```bash
git clone https://github.com/Adnan-Akil/Aegis-Red.git
cd Aegis-Red
bash setup.sh      # installs venv, deps, playwright, and frontend
# Then in two terminals:
venv/bin/uvicorn backend.main:app --reload
cd frontend && npm run dev
```

Then open **http://localhost:3000**, sign in, and paste any target AI URL to start an attack.

---

## 📖 1. Executive Summary & Vision

AI integrations have evolved from simple stateless text boxes into autonomous "Tool-Using Agents" and corporate RAG engines. As these agents gain access to databases and actions (e.g., executing shell commands, retrieving internal documents, or resetting credentials), they introduce massive semantic vulnerabilities.

Aegis-Red represents a shift from static, stateless security testing to **autonomous, UI-driven red-teaming**. Using a state-machine orchestrator, the framework:
1. **Crawls** unmapped web pages to locate chatbot interfaces.
2. **Profiles** target behaviors to detect capabilities (e.g., whether it has tools or documents).
3. **Drafts** strategic attack plans based on its discovery.
4. **Executes** payloads through browser automation, preserving multi-turn conversation states.
5. **Evaluates** responses dynamically with a secure, zero-leak hybrid analyzer.
6. **Mutates** failed prompts in real-time to evade semantic security filters.

---

## 🧠 2. Core Philosophy & Design Strategy

### Why We Chose This Path
* **Direct DOM Interaction vs. API-Only Scans**: API scanners bypass client-side code, frontend guardrails, character limitations, and context-routing logic. Aegis-Red interacts directly with the DOM, ensuring high-fidelity, real-world simulation of human attackers.
* **LangGraph Orchestration vs. Single Agent**: Single LLMs suffer from severe context degradation, planning drift, and hallucinations when handling multi-step tasks. By dividing responsibilities into a structured StateGraph (Surface Mapper, Planner, Executor, Evaluator, Mutator), we guarantee modularity and state consistency.
* **Adversarial Fuzzing vs. Static Playbooks**: Static prompt injection lists are quickly caught by simple regex filters. Aegis-Red uses "Semantic Fuzzing"—iteratively modifying prompt context, language, structure, and encoding—to find brittle edge cases in target filters.

---

## 🏛️ 3. System Architecture & Flows

Aegis-Red is modeled as a cyclic state machine utilizing the military **OODA Loop (Observe, Orient, Decide, Act)**.

```mermaid
graph TD
    A[Start: Target URL] --> B[Surface Mapper: Discover UI Elements]
    B --> C[Active Prober: Interrogate Target Type]
    C --> D[Strategic Planner: Select Optimal Payload]
    D --> E[Executor Node: Playwright Interaction]
    E --> F[Evaluator Node: Hybrid Audit Layer]
    F -- Breach Confirmed --> G[Report Generator: Structured PDF/Markdown]
    F -- Refusal Detected / Try Again --> H[Mutator Node: Evolve Payload]
    H --> E
    F -- No Breach / Payload Exhausted --> D
```

### The LangGraph State Pipeline (`src/pipelines/graph.py`)
The orchestrator maintains the conversation state across a `StateGraph` using strictly typed schemas:

1. **`planner_node`**: Analyzes target capabilities and the history of previous failures to choose the most viable payload from the `AttackRegistry`.
2. **`executor_node`**: Uses headless browser control to input the prompt, click submit, monitor the streaming response settle, and capture output.
3. **`evaluator_node`**: Scans output locally for regex-matched secrets, checks structural JSON validity, applies structure-preserving encryption to sensitive fragments, and prompts the LLM Judge for semantic verdicts.
4. **`mutator_node`**: Evolved based on previous failures, this node applies strategies like homoglyph substitution, translation redirection, base64 encapsulation, and roleplay frames to rewrite the payload.

```mermaid
stateDiagram-v2
    [*] --> Planner : Enter target details
    Planner --> Executor : Selected payload ID
    Executor --> Evaluator : Captured UI message
    Evaluator --> Mutator : Verdict: FAIL (Mutations < 2)
    Mutator --> Executor : Evolved Payload
    Evaluator --> Planner : Verdict: FAIL (Mutations limit hit)
    Evaluator --> [*] : Verdict: SUCCESS (Vulnerability logged)
```

---

## 💻 4. Deep-Dive Tech Stack

### Backend Orchestration Core
* **Python 3.10+ / asyncio**: Built using asynchronous execution threads to handle concurrent web automation without blocking.
* **LangGraph & LangChain**: Manages state, memory buffers, conditional transitions, and LLM integrations.
* **FastAPI**: Serves the application logic as a RESTful web API, streaming telemetry updates back to the client.
* **SQLite (via `aiosqlite`)**: Portable, lightweight database storing transaction logs, target profiles, and successful payload patterns.

### Web Automation Engine
* **Playwright**: Automates a headless Chromium instance to interact with modern SPA platforms (React/Next.js/Streamlit). Includes a self-healing selector cache.

### Frontend Presentation Layer
* **Next.js 15 (App Router) & TypeScript**: Modern Single-Page Application (SPA) designed as an operative command terminal.
* **Tailwind CSS**: Strict custom design system containing dark-mode panels, glassmorphism containers, and vibrant glows.
* **Framer Motion**: Smooth micro-animations and pulsing telemetry glows to indicate real-time backend agent processing.
* **Lucide Icons**: Clean, developer-centric icon set.

---

## 🛡️ 5. Key Innovations & Advanced Exploitation

### A. Local Structure-Preserving Cipher (Zero-Leak LLM Judge)
Sending extracted secrets (like API keys or internal database passwords) to a third-party LLM for validation violates compliance and creates a secondary data breach. Aegis-Red solves this by running a **local structure-preserving Caesar cipher** on the suspected secrets before sending them to the LLM Judge:

$$\text{Cipher}(c) = (c - \text{Base} + 7) \bmod \text{Range} + \text{Base}$$

* **Letters** shift to letters, **digits** shift to digits, and **formatting characters** (`-`, `.`, `_`) are preserved to maintain the structural schema of the credential.

#### Cipher Execution Walkthrough:
| Original Character | Type | Caesar Shift Math (+7) | Ciphered Result |
| :--- | :--- | :--- | :--- |
| **A** | Uppercase | $(0 + 7) \bmod 26 = 7$ | **H** |
| **K** | Uppercase | $(10 + 7) \bmod 26 = 17$ | **R** |
| **I** | Uppercase | $(8 + 7) \bmod 26 = 15$ | **P** |
| **A** | Uppercase | $(0 + 7) \bmod 26 = 7$ | **H** |
| **1** | Digit | $(1 + 7) \bmod 10 = 8$ | **8** |
| **2** | Digit | $(2 + 7) \bmod 10 = 9$ | **9** |
| **3** | Digit | $(3 + 7) \bmod 10 = 0$ | **0** |
| **4** | Digit | $(4 + 7) \bmod 10 = 1$ | **1** |

The LLM Judge receives: `[REDACTED: HRPH8901HIJK2345]`. It can easily confirm that a high-entropy key was leaked because the format matches `AKIA\d{4}`, yet the actual API key never leaves the local environment.

### B. Dynamic Exfiltration Chain (DEC)
Most RAG engines maintain conversation states in memory or through web cookies. When an attacker jailbreaks a system in Turn 1, launching a new browser context in Turn 2 wipes the session. 
Aegis-Red resolves this by **grafting exfiltration commands** directly into the payload context and executing them in the **same browser tab** under the active compromised state:

```
[Turn 1: Jailbreak] -> (Succeeds) -> [Same Browser Tab] -> [Turn 2: Obfuscated Query] -> (Exfiltrates context documents)
```

Furthermore, Turn 2 prompts are engineered as **retrieval-triggering queries** (e.g. asking a complex question about confidential API keys rather than an imperative command) to force the vector DB to populate the LLM's context window.

### C. Surgical Cyrillic Homoglyph Obfuscation
Static Web Application Firewalls (WAFs) and keyword filters block prompts containing banned strings like `"admin"` or `"system prompt"`. Aegis-Red bypasses this by programmatically substituting Latin characters with identical-looking Cyrillic unicode codepoints:
* Latin `'a'` (U+0061) $\rightarrow$ Cyrillic `'а'` (U+0430)
* Latin `'e'` (U+0065) $\rightarrow$ Cyrillic `'е'` (U+0435)

The string matching filter evaluates the string as safe (evaluates to `False`), but the multilingual tokenizer decodes the semantic intent identically, triggering the exploit.

---


## 📊 7. Performance & Evaluation Metrics

Quantitative performance based on **1,306 total attack cycles** across **82 distinct sessions**:

### Key Mathematical Formulas
* **Mutation Effectiveness (ME)**:
  $$\text{ME} = \frac{|P_{\text{success}}|}{|P_{\text{failed\_initial}}|} \times 100$$
  * *Aegis-Red achieved an ME of **46.4%**, proving mutated payloads successfully exploit targets that blocked initial attempts.*
* **Autonomy Score (AS)**:
  $$\text{AS} = 1.0 - \frac{\text{Manual Interventions}}{\text{Total Sessions}}$$
  * *Aegis-Red achieved an AS of **0.98**, requiring only 1 manual intervention across 82 runs.*

### Telemetry Performance Summary

| Metric | Measured Value | Notes |
| :--- | :--- | :--- |
| **Mutation Effectiveness (ME)** | **46.4%** | Refines and adapts prompts based on failure context |
| **Autonomy Score (AS)** | **0.98 / 1.0** | Playwright handles DOM settling and self-heals selectors |
| **Average Time-to-Compromise (TTC)** | **43.2 seconds** | Fast closed-loop execution |
| **Fastest Recorded Compromise** | **3.7 seconds** | Single direct heuristic mapper exploit |
| **Evaluator Precision (v2.0)** | **96%** | Up from 72% in v1.0 (Elite patch) |
| **Critical Breaches Logged** | **138** | Confirmed by hybrid evaluator |

### Visualized Progress Charts
*Below are the pre-rendered statistical charts showing performance metrics:*

#### 1. Success Rate by Attack Category
![Attack Categories](assets/chart1_attack_categories.png)

#### 2. Average Time-to-Compromise (TTC) Distribution
![Time to Compromise](assets/chart2_ttc.png)

#### 3. Delta Improvements: Aegis-Red v1.0 vs v2.0 Overhaul
![v1 vs v2 Overhaul](assets/chart3_v1_vs_v2.png)

---

## ⚙️ 8. Setup & Installation

> **New users:** Run `setup.bat` (Windows) or `bash setup.sh` (Linux/macOS) for a one-command setup. See below for details.

### Prerequisites
* **Python 3.10+**
* **Node.js 18+** & `npm`
* **Groq API Key** — [console.groq.com](https://console.groq.com/keys)
* **Supabase Project** — [supabase.com](https://supabase.com)

### 1. Clone
```bash
git clone https://github.com/Adnan-Akil/Aegis-Red.git
cd Aegis-Red
```

### 2. Configure Environment
```bash
# Root .env (backend secrets)
cp .env.example .env
# Edit .env and fill in GROQ_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY

# Frontend .env.local
cp frontend/.env.example frontend/.env.local
# Edit frontend/.env.local and fill in Supabase anon key + BACKEND_URL
```

### 3. Run Setup
```bat
:: Windows
setup.bat
```
```bash
# Linux / macOS
bash setup.sh
```

This handles: venv creation → pip install → playwright chromium install → npm install.

### 4. Supabase Schema
Run the SQL in your Supabase SQL editor to create the required tables (`sessions`, `logs`, `findings`, `profiles`). Enable Row Level Security on each so users only see their own data.

---

## 🚀 9. Usage & Execution

### Option A: Desktop Launcher (Windows — Recommended for Local Dev)
Double-click `start.bat`. It will:
1. Check venv and npm are present (run `setup.bat` first if not).
2. Kill any zombie processes on ports 3000 and 8000.
3. Start the **FastAPI backend** on port 8000 in a new terminal.
4. Start the **Next.js dashboard** on port 3000 in a new terminal.
5. Open the browser to `http://localhost:3000`.

### Option B: Manual (Linux/macOS or fine-grained control)
```bash
# Terminal 1 — Backend
venv/bin/uvicorn backend.main:app --reload

# Terminal 2 — Frontend  
cd frontend && npm run dev
```

### Option C: Direct CLI Attack (no dashboard)
```bash
# Attack a live external URL
venv/Scripts/python run_attack.py https://your-target.com/chat --iter 5

# Attack a local benchmark target
venv/Scripts/python runner.py --target hardened_rag --iter 5
```

### Option D: Vercel + Railway (Production)
Deploy `backend/` to Railway (auto-detected via `Procfile`) and `frontend/` to Vercel. Set the env vars on each platform and point `BACKEND_URL` at your Railway URL.

---

## 🤝 10. Contributions & Collaboration

We welcome security researchers, AI developers, and red-teamers to collaborate and improve Aegis-Red! Here is how you can get involved:

### How to Contribute
1. **Report Bugs & Suggest Features**: If you find browser-automation edge cases or selector issues, open an issue or submit a report.
2. **Add Attack Payloads**: Extend the library by contributing new jailbreak, exfiltration, or tool abuse payloads to the registry under `src/tools/attacks/`.
3. **Harden the Targets**: Submit new vulnerable scenarios or propose stronger defenses/DLP patterns for the benchmark target ecosystem.
4. **Code Quality**: Help refine our agent prompts, mutator LLM logic, or SQLite persistence models.

### Pull Request Guidelines
- Branch naming: `feat/<name>`, `fix/<name>`, or `chore/<name>`.
- Keep changes modular and ensure existing unit tests pass.
- Suggest a concise commit message using the Conventional Commits format.
