# PayPal PayAgent OS

> **Autonomous AI Agent Financial Wallet, Policy-Guided Guardrails & PayPal Vault Engine**
> 
> *Built for the **PayPal AI Hackathon 2026** on Devpost.*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11+-brightgreen.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal.svg)](https://fastapi.tiangolo.com/)
[![PayPal: REST API v2](https://img.shields.io/badge/PayPal-REST%20API%20v2-003087.svg)](https://developer.paypal.com/)
[![PayPal AI Toolkit](https://img.shields.io/badge/PayPal-AI%20Toolkit%20%26%20MCP-0079C1.svg)](https://github.com/paypal/AI-Toolkit)
[![Test Suite: 59/59 Passed](https://img.shields.io/badge/Tests-59%2F59%20Passed-success.svg)](tests/)
[![Sandbox: Verified](https://img.shields.io/badge/PayPal%20Sandbox-Verified%20Proof-10b981.svg)](https://developer.paypal.com/dashboard/applications/sandbox)
[![Devpost](https://img.shields.io/badge/Devpost-Submission-003E54.svg?logo=devpost)](https://devpost.com/software/payagent-os-u61539)
[![YouTube Demo](https://img.shields.io/badge/YouTube-Watch%20Demo%20(3m)-FF0000.svg?logo=youtube)](https://youtu.be/1k-yRHFEzN0)

[![Watch Demo Video](https://img.shields.io/badge/▶_Watch_Demo_Video-YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://youtu.be/1k-yRHFEzN0)
[![View on Devpost](https://img.shields.io/badge/Devpost-Project_Showcase-003E54?style=for-the-badge&logo=devpost&logoColor=white)](https://devpost.com/software/payagent-os-u61539)


---

## 💡 The Core Vision & Problem

The agentic AI era is here: autonomous agents (Claude Code, Cursor, Devin, CrewAI, AutoGen) are provisioning cloud clusters, executing model fine-tuning, purchasing research datasets, and orchestrating contractors.

However, **enterprises cannot safely give AI agents unbounded corporate credit cards**:
1. **Uncontrolled Burn:** A single infinite loop or prompt injection can rack up a $10,000+ AWS/API bill in minutes.
2. **Autonomy Bottleneck:** Requiring human approval for every $0.50 routine API call paralyzes autonomous workflows.
3. **Zombie SaaS Subscriptions:** Agents spin up recurring SaaS tokens (APIs, developer seats, compute licenses) and abandon them, continuously bleeding corporate cash.
4. **Lack of Explainable Audit Trail:** Traditional payment gateways record raw card charges without knowing *why* the AI made the purchase.

---

## 🛡️ The 3 Core Pillars of PayAgent OS

PayAgent OS turns PayPal's global payment infrastructure into a programmable, guardrail-governed wallet operating system:

```text
       ┌─────────────────────────────────────────────────────────────┐
       │                 Autonomous AI Agents                        │
       │        (DevOps Sentinel · Deep Research · Freelance)         │
       └──────────────────────────────┬──────────────────────────────┘
                                      │
                         HTTP Intent / MCP Invocation
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                             PayAgent OS                                    │
│                                                                            │
│  [ PILLAR 1: Guardrail Engine ]       [ PILLAR 2: MCP Interceptor ]        │
│  • Per-Tx & Daily Policy Caps         • Official PayPal AI Toolkit Bridge  │
│  • LLM Prompt Injection Shield        • Model Context Protocol (MCP) Tools │
│  • Human-in-the-Loop (HITL) Queue     • Runtime Budget Interception        │
│                                                                            │
│                 [ PILLAR 3: PayPal Vault Cleaner ]                         │
│                 • Automated Zombie SaaS Inactivity Scan                    │
│                 • 1-Click Vault Token Cancellation & Cash Recovery         │
└─────────────────────────────────────┬──────────────────────────────────────┘
                                      │
                         Cryptographic Settlement
                                      │
                                      ▼
       ┌─────────────────────────────────────────────────────────────┐
       │                PayPal Sandbox REST API v2                   │
       │  (OAuth2 Token · Orders v2 · Capture · Payouts v1 · Vault)  │
       └─────────────────────────────────────────────────────────────┘
```

### 1. Enterprise Financial Guardrails & Live HITL State Machine
- **Dual-Threshold Control:** Micro-transactions within policy ceilings (e.g. routine $15 AWS compute) execute autonomously in seconds.
- **Human-in-the-Loop (HITL) Safety Gate:** Budget overruns (e.g. $240 GPU rental vs. $25 limit) or anomalous requests are frozen in a live supervisor queue for one-click authorization or reasoned rejection.
- **Immutable Audit Trail:** Every transaction records agent reasoning, timestamp, vendor, and cryptographic PayPal order telemetry.

### 2. Official PayPal AI Toolkit & MCP Interceptor (The Security Shield)
- **Seamless Drop-In Adapter:** Integrates directly with PayPal's official [`paypal/AI-Toolkit`](https://github.com/paypal/AI-Toolkit) and official Sandbox MCP Server.
- **Active Guardian Interceptor:** When Cursor or Claude Code agents invoke official tools (`paypal_create_order`, `paypal_create_payout`, `paypal_get_balance`), PayAgent OS intercepts calls to verify policy caps *before* financial commitment.

### 3. PayPal Vault — Zombie SaaS Subscription Killer
- **Automated Inactivity Detection:** Continuously scans PayPal Vault recurring tokens for SaaS seats unused for >14/28 days.
- **1-Click Cancellation:** Instantly revokes idle tokens via PayPal Vault APIs, directly returning recurring cash back to corporate treasury.

---

## 🔍 Verifiable PayPal Sandbox Telemetry (Live Proof)

Every operation executed by PayAgent OS returns verifiable cryptographic telemetry directly tied to PayPal Sandbox:
- **`verification_status`:** `VERIFIED_SANDBOX`
- **`paypal_debug_id`:** Live tracking ID corresponding to PayPal server headers (`PP-DBG-...`).
- **`paypal_sandbox_environment`:** Verified against `https://api-m.sandbox.paypal.com`.
- **Live Status Badges:** Visual indicators in the Command Center header linking directly to [PayPal Developer Dashboard](https://developer.paypal.com/dashboard/applications/sandbox).

---

## ⚡ Living Autonomous Fleet Runner (`scripts/autonomous_agent_runner.py`)

PayAgent OS includes a realistic, cognitive-paced CLI simulator where agents operate autonomously, think, dialogue, encounter guardrails, and resume upon human supervisor action:

```bash
# Run realistic autonomous agent simulation:
python scripts/autonomous_agent_runner.py
```

### 🎬 What Happens During the Live Run:
1. **DevOps Agent ($18.50 AWS):** Analyzes Prometheus metrics (2.5s think time) ➔ Within $50 limit ➔ **Autonomously Approved & Captured via PayPal Orders v2**.
2. **Research Agent ($240.00 RunPod GPU):** Allocates VRAM (2.5s think time) ➔ Exceeds $25 limit ➔ **Workload Suspended (`PAUSED`)**.
3. **Supervisor Approval:** Open `http://localhost:8000`, click **"ONAYLA"** on the pending card.
4. **Live Resume:** Terminal instantly detects approval ➔ **`[RESUMED]` ➔ Captures PayPal payment and continues execution**.
5. **Freelance Agent ($45.00 Payout):** Verifies code PR ➔ Disburses direct payment via **PayPal Payouts v1 REST API**.

---

## 🚀 Quick Start

### 1. Clone & Setup
```bash
git clone https://github.com/blosny/payagent-os.git
cd payagent-os

# Create virtual environment
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1
# Linux / macOS
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 2. Configure Environment (Optional)
```bash
cp .env.example .env
```
Edit `.env` with your PayPal Developer Sandbox credentials:
```env
PAYPAL_CLIENT_ID=your_sandbox_client_id
PAYPAL_CLIENT_SECRET=your_sandbox_client_secret
PAYPAL_MODE=sandbox
```
*(Note: If credentials are not provided, PayAgent OS automatically operates in Simulated Sandbox Mode for offline testing).*

### 3. Launch PayAgent OS Server
```bash
uvicorn backend.app.main:app --reload --port 8000
```
Open:
- **Interactive Command Center:** `http://localhost:8000`
- **Interactive Swagger REST Docs:** `http://localhost:8000/docs`

### 4. Run Test Suite
```bash
pytest
```
*(All 59 unit, integration, and security tests pass in ~0.5 seconds).*

---

## 🗂️ 3 Focused Workspaces in Command Center
1. **`⚡ Komuta Merkezi & Canlı HITL`:** Real-time agent status cards, quick scenario test chips, live HITL supervisor decision desk, and audit trail.
2. **`🛠️ Resmi PayPal AI Toolkit & MCP`:** Official PayPal AI Toolkit schema inspector and real-time interceptor stream.
3. **`🧹 PayPal Vault & SaaS Tasarruf Masası`:** PayPal Vault tokenized subscriptions list and 1-click inactive license terminator.

---

## 👥 Author
- **Taha Buğra Çiçek** — Fırat University, Computer Engineering
- GitHub: [@blosny](https://github.com/blosny)

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
