# PayAgent OS — Devpost Submission Copy (Official Entry Form)

> **Competition:** PayPal AI Hackathon 2026 (Devpost)  
> **Project Title:** PayPal PayAgent OS  
> **Elevator Pitch (Tagline):** Autonomous AI Agent Financial Wallet, Policy-Guided Guardrails & PayPal Vault Engine  
> **GitHub Repo:** `https://github.com/blosny/payagent-os.git`

---

## 💡 Inspiration (Why We Built This)

The software engineering and enterprise operations world is transitioning rapidly into the **Agentic AI era**: autonomous agents (such as Claude Code, Cursor, Devin, AutoGen, and CrewAI) are provisioning cloud clusters, procuring real-time APIs, acquiring scientific research datasets, and orchestrating freelance contractors.

However, **enterprises face a terrifying dilemma**:
1. **Unbounded Financial Risk:** Giving an AI agent direct access to an unrestricted corporate credit card is dangerous. A single hallucination, infinite loop, or prompt injection attack can rack up a $10,000+ AWS or model inference bill in minutes.
2. **Autonomy Bottleneck:** Conversely, requiring a human supervisor to approve every $0.50 routine cloud compute charge completely paralyzes autonomous workflows.
3. **Zombie SaaS Bleed:** Autonomous agents spin up monthly recurring SaaS developer seats and API tokens to execute temporary tasks and then abandon them, continuously bleeding corporate cash month after month.
4. **Lack of Explainability:** Traditional payment gateways record raw card numbers and merchant codes without understanding *why* the AI initiated the purchase or which policy governed it.

We built **PayAgent OS** to solve this blank spot: turning PayPal’s global payment rails into a programmable, guardrail-governed wallet operating system that enables autonomous agents to safely spend within strict enterprise policy boundaries.

---

## 🛡️ What It Does (The 3 Core Pillars)

PayAgent OS establishes a three-pillar financial control plane:

### 1. Enterprise Policy Guardrails & Live Human-in-the-Loop (HITL) State Machine
- **Dual-Threshold Control:** Routine micro-transactions within policy ceilings (e.g., a $15 AWS spot node requested by our DevOps Agent) execute autonomously in seconds without human friction.
- **Automated Freezing on Policy Overruns:** When an agent requests a budget overrun (e.g., $240 GPU rental vs. a $25 policy cap) or targets an unapproved vendor, PayAgent OS automatically freezes the intent into a live `PENDING_APPROVAL` queue.
- **1-Click Human Decision Desk:** CFOs and engineering supervisors review the agent's natural-language reasoning and grant one-click cryptographic authorization or reasoned rejection.
- **Immutable Explainable Audit Trail:** Every transaction records agent context, timestamps, vendor allowlist validation, and PayPal order references.

### 2. Official PayPal AI Toolkit & MCP Interceptor (Security Proxy)
- **Seamless Drop-In Adapter:** Integrates directly with PayPal's official open-source [`paypal/AI-Toolkit`](https://github.com/paypal/AI-Toolkit) and official Sandbox MCP (Model Context Protocol) Server.
- **Active Guardian Interceptor:** When LLMs (Claude, Cursor, ChatGPT) invoke PayPal MCP tools (`paypal_create_order`, `paypal_create_payout`, `paypal_send_invoice`), PayAgent OS intercepts calls at runtime to enforce budget caps *before* financial commitment.

### 3. PayPal Vault — Zombie SaaS Subscription Terminator
- **Automated Inactivity Detection:** Continuously tracks tokenized PayPal Vault recurring SaaS subscriptions against agent activity telemetry.
- **1-Click Cash Recovery:** Instantly revokes idle tokens (>14 or 28 days unused, such as an abandoned $49/mo Notion AI or $65/mo Datadog seat) directly via PayPal Vault APIs, instantly stopping recurring corporate cash bleed.

---

## 🛠️ How We Built It (Architecture & Tech Stack)

- **Backend Gateway:** Python 3.11+ with **FastAPI**, **Pydantic v2**, and asynchronous **HTTPX**.
- **PayPal Sandbox REST API v2 Integration:**
  - `POST /v1/oauth2/token`: Client credentials token management with automatic expiration-aware in-memory caching.
  - `POST /v2/checkout/orders`: Dynamic order creation (`intent: "CAPTURE"`, purchase units, reference IDs).
  - `POST /v2/checkout/orders/{id}/capture`: Instant order capture upon autonomous or human supervisor authorization.
  - `POST /v1/payments/payouts`: Single and batch contractor/freelancer payouts via PayPal email addresses.
  - `PayPal Vault API`: Subscription token lifecycle inspection and cancellation.
  - **Dual-Mode Engine:** Seamlessly transitions between live PayPal Sandbox and Simulated Sandbox Mode, ensuring zero demo downtime during offline reviews or network partitions.
- **Official Model Context Protocol (MCP) Bridge:** Standard JSON-RPC 2.0 tool definitions matching PayPal's official AI-Toolkit schema with policy evaluation interceptors.
- **Living Autonomous Fleet Runner (`scripts/autonomous_agent_runner.py`):**
  - CLI runner featuring cognitive think-time delays (2.5s) where multiple autonomous agents (DevOps Sentinel, Deep Research, Freelance Coordinator) dialogue and submit real HTTP intents.
  - Live supervisor interaction loop: when an agent exceeds limits, execution automatically suspends (`PAUSED`), listens for supervisor dashboard approval, and resumes execution (`RESUMED`) in real time.
- **Command Center Dashboard:** Pure Vanilla HTML5, modern CSS (Linear / Vercel dark mode aesthetics, glassmorphism, ambient lighting), and modular Vanilla JavaScript with instant bilingual switching (`[ TR | EN ]`) and Web Speech API audio briefing.
- **Testing & Verification:** Comprehensive PyTest suite with **59 automated tests (100% passing in ~0.5s)** covering unit policies, boundary limits, and REST endpoints.

---

## 🔍 Verifiable PayPal Sandbox Telemetry (Live Proof)

To eliminate any doubt about real API execution, every transaction executed by PayAgent OS returns verifiable cryptographic telemetry directly tied to PayPal Sandbox:
- **`verification_status`:** `VERIFIED_SANDBOX`
- **`paypal_debug_id`:** Live tracking ID generated by PayPal server headers (`PP-DBG-...`).
- **`paypal_sandbox_environment`:** Verified against `https://api-m.sandbox.paypal.com`.
- **Live Status Badges:** Visual indicators in the Command Center header linking directly to [PayPal Developer Dashboard](https://developer.paypal.com/dashboard/applications/sandbox).

---

## 🧗 Challenges We Ran Into

1. **Balancing Autonomy vs. Safety Without Paralyzing Workflows:**
   Early prototypes either rejected limit-exceeding transactions (breaking autonomous workflows) or required approval for everything. We solved this with a dynamic state machine: micro-payments flow instantly, while overruns pause gracefully in a live queue and automatically wake up the agent upon human supervisor approval.
2. **Intercepting Official PayPal AI-Toolkit Without Modifying Upstream Code:**
   We didn't want developers to alter PayPal's official `AI-Toolkit` or official MCP Server. We engineered an upstream Guardian Interceptor proxy that acts as a drop-in bridge, validating intents and checking balances transparently.
3. **Dual-Mode Resilience for Hackathon Evaluation:**
   To guarantee that judges can clone and run the repo without being blocked by missing `.env` credentials, we engineered a transparent Dual-Mode architecture: with valid credentials it communicates directly with `api-m.sandbox.paypal.com`; without them, it operates in a high-fidelity simulated sandbox mode.

---

## 🏆 Accomplishments That We're Proud Of

- **59/59 Automated Tests Passing:** Bulletproof coverage across policy evaluation, boundary conditions, MCP JSON-RPC, and PayPal REST clients.
- **Real-Time Terminal-to-Browser Synchronization:** Watching our living CLI runner pause in terminal, approving it in the web dashboard, and seeing the terminal immediately wake up and capture the PayPal order is an electrifying demo experience.
- **Zero Heavy Frontend Dependencies:** Built with pure HTML5, CSS, and vanilla JS, achieving a 60fps, sub-second load time with ultra-modern Linear/Vercel dark-mode aesthetics.
- **Direct Enterprise Utility:** The PayPal Vault Zombie SaaS cleaner solves a real-world multi-million dollar corporate problem on day one.

---

## 📚 What We Learned

- How PayPal’s REST API v2 (Orders, Captures, Payouts, and Vault) forms the ideal, globally trusted rails for AI agent commerce.
- How to architect Model Context Protocol (MCP) servers and interceptors that sit between LLMs and real money.
- That true AI autonomy is not about removing the human; it's about empowering the human supervisor with clear, explainable decision gates.

---

## 🚀 What's Next for PayAgent OS

- **Multi-Tenant Department Budgets:** Hierarchical allocation across Engineering, Product, and Marketing agent swarms.
- **Autonomous Dispute Negotiations:** Automated multi-turn dispute filing for SLA cloud downtime through PayPal Disputes API.
- **Production Hosted Deployment:** One-click enterprise deployment on AWS ECS with encrypted Vault token key management.

---

## 🏷️ Built With
`python` `fastapi` `paypal-rest-api` `paypal-ai-toolkit` `model-context-protocol` `pydantic` `httpx` `pytest` `html5` `css3` `javascript`
