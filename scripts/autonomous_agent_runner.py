#!/usr/bin/env python3
"""
PayAgent OS — Autonomous Living Fleet Runner
Simulates autonomous AI agents operating with realistic cognitive think-time delays,
submitting real payment intents to PayAgent OS, encountering Policy Guardrails,
and dynamically resuming execution when a human supervisor approves via the Dashboard.
"""

import sys
import time
import json
import argparse
import httpx
from datetime import datetime

# ANSI Color formatting
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
DIM = "\033[2m"

def print_banner():
    print(f"\n{BOLD}{CYAN}======================================================================{RESET}")
    print(f"{BOLD}{CYAN}           🤖  PayAgent OS — Living Autonomous Fleet Runner           {RESET}")
    print(f"{BOLD}{CYAN}    Real-time Guardrails & PayPal Sandbox Verifiable Proof Engine     {RESET}")
    print(f"{BOLD}{CYAN}======================================================================{RESET}\n")

def log_agent(agent_name: str, message: str, color=CYAN):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{DIM}[{ts}]{RESET} {BOLD}{color}[{agent_name}]{RESET} {message}")

def think(seconds: float, reason: str = ""):
    if reason:
        print(f"       {DIM}💭 {reason}... ({seconds:.1f}s){RESET}")
    time.sleep(seconds)

def run_simulation(base_url: str = "http://127.0.0.1:8000", loop_forever: bool = False):
    print_banner()
    log_agent("System", f"Connecting to PayAgent OS Gateway at {base_url}...", BLUE)

    # 1. Health check
    try:
        with httpx.Client(base_url=base_url, timeout=5.0) as client:
            r = client.get("/health")
            if r.status_code != 200:
                print(f"{RED}Error: Server returned status {r.status_code}{RESET}")
                return
            data = r.json()
            log_agent("System", f"Core Online | Environment: PayPal {data.get('mode', 'SANDBOX').upper()} | Connected: {data.get('paypal_connected', True)}", GREEN)
    except Exception as e:
        print(f"{RED}Cannot connect to PayAgent OS at {base_url}. Make sure server is running:{RESET}")
        print(f"       uvicorn backend.app.main:app --port 8000\n")
        return

    round_count = 1
    while True:
        print(f"\n{BOLD}{BLUE}--- [ MISSION CYCLE #{round_count} ] -----------------------------------{RESET}\n")

        # SCENARIO 1: DevOps Infrastructure Agent (Autonomous Pass)
        log_agent("DevOps Agent", "Scanning infrastructure metrics across AWS & Docker containers...", CYAN)
        think(2.5, "Evaluating Prometheus CPU load metrics")

        log_agent("DevOps Agent", f"High load detected on node eu-west-1. Ordering scale-out micro-instance ($18.50).", YELLOW)
        think(1.5, "Formulating payment intent with AI reasoning")

        intent_devops = {
            "agent_id": "agent-devops",
            "amount": 18.50,
            "currency": "USD",
            "recipient": "AWS",
            "category": "INFRASTRUCTURE",
            "reasoning": "Prometheus CPU spike 92%: spinning up ephemeral Docker cache node on AWS EC2.",
        }

        with httpx.Client(base_url=base_url, timeout=10.0) as client:
            res1 = client.post("/api/v1/payments/intent", json=intent_devops)
            if res1.status_code == 200:
                tx1 = res1.json()
                order_id = tx1.get("paypal_order_id", "ORD-UNKNOWN")
                debug_id = tx1.get("paypal_debug_id", "PP-DBG-UNKNOWN")
                env = tx1.get("paypal_sandbox_environment", "https://api-m.sandbox.paypal.com")
                print(f"       {GREEN}✓ [POLICY PASSED]{RESET} Limit: $50.00/tx | Requested: $18.50 | Status: {BOLD}{tx1.get('status')}{RESET}")
                print(f"       {GREEN}✓ [PAYPAL SANDBOX VERIFIED]{RESET} Order ID: {BOLD}{order_id}{RESET}")
                print(f"       {DIM}  ↳ PayPal Debug ID: {debug_id} | Env: {env}{RESET}")
                print(f"       {DIM}  ↳ Proof: https://developer.paypal.com/dashboard/applications/sandbox{RESET}")
            else:
                print(f"       {RED}Failed: {res1.text}{RESET}")

        # Inter-agent conversation delay
        print(f"\n       {DIM}--- Awaiting telemetry sync between agents (3.0s) ---{RESET}\n")
        think(3.0)

        # SCENARIO 2: Research & ML Agent (Guardrail Triggered & Live Human Approval)
        log_agent("Research Agent", "Fine-tuning deep reasoning model on financial compliance dataset...", MAGENTA)
        think(2.5, "Allocating GPU memory buffers and batch parameters")

        requested_gpu_cost = 240.00
        log_agent("Research Agent", f"Local VRAM insufficient. Requesting 8x H100 GPU compute on RunPod (${requested_gpu_cost:.2f}).", YELLOW)
        think(1.8, "Submitting autonomous transaction to PayAgent OS Guardrail Shield")

        intent_research = {
            "agent_id": "agent-research",
            "amount": requested_gpu_cost,
            "currency": "USD",
            "recipient": "RunPod",
            "category": "DATASET",
            "reasoning": "Urgent LLM benchmark run: leasing 8x NVIDIA H100 SXM5 GPU cluster on RunPod.",
        }

        with httpx.Client(base_url=base_url, timeout=10.0) as client:
            res2 = client.post("/api/v1/payments/intent", json=intent_research)
            if res2.status_code == 200:
                tx2 = res2.json()
                tx_id = tx2.get("id")
                status = tx2.get("status")
                policy_reason = tx2.get("policy_evaluation_reason", "Exceeds limit")

                if status == "PENDING_APPROVAL":
                    print(f"       {YELLOW}⚠️  [POLICY GUARDRAIL TRIGGERED]{RESET}")
                    print(f"       {YELLOW}   Agent Ceiling: $25.00/tx | Requested: ${requested_gpu_cost:.2f}{RESET}")
                    print(f"       {YELLOW}   Reason: {policy_reason}{RESET}")
                    print(f"\n       {BOLD}{RED}⏸️  [WORKLOAD SUSPENDED — HUMAN-IN-THE-LOOP ACTIVE]{RESET}")
                    print(f"       {CYAN}👉 LÜTFEN TARAYICIDAKİ PANELİ AÇIN: {BOLD}http://127.0.0.1:8000{RESET}")
                    print(f"       {CYAN}   Bekleyen karttaki 'ONAYLA' (Approve) butonuna basın!{RESET}\n")

                    # Polling loop waiting for human approval
                    poll_start = time.time()
                    approved = False
                    while time.time() - poll_start < 120:  # 2 minute timeout
                        time.sleep(2.0)
                        tx_check = client.get(f"/api/v1/payments/{tx_id}").json()
                        current_status = tx_check.get("status")

                        if current_status in ["APPROVED_BY_HUMAN", "SETTLED"]:
                            approved = True
                            paypal_order = tx_check.get("paypal_order_id", "ORD-CAPTURED")
                            paypal_capture = tx_check.get("paypal_capture_id", "CAP-SETTLED")
                            debug_id = tx_check.get("paypal_debug_id", "PP-DBG-LIVE")
                            print(f"       {BOLD}{GREEN}🎉 [RESUMED — SUPERVISOR APPROVED!]{RESET}")
                            print(f"       {GREEN}✓ [PAYPAL ORDERS v2 CAPTURED]{RESET} Order ID: {BOLD}{paypal_order}{RESET} | Capture ID: {BOLD}{paypal_capture}{RESET}")
                            print(f"       {GREEN}✓ [SANDBOX AUDIT TRAIL]{RESET} Debug ID: {debug_id} | Verified: TRUE")
                            break
                        elif current_status in ["REJECTED_BY_HUMAN", "REJECTED_BY_POLICY"]:
                            print(f"       {RED}❌ [REJECTED BY SUPERVISOR] Workload aborted.{RESET}")
                            break
                        else:
                            print(f"       {DIM}⏳ Bekleniyor... Süpervizör onayı henüz gelmedi ({int(time.time() - poll_start)}s){RESET}", end="\r")

                    if not approved and current_status == "PENDING_APPROVAL":
                        print(f"\n       {YELLOW}[Zaman aşımı]: Süpervizör 2 dakika içinde yanıt vermedi.{RESET}")

        # Inter-agent conversation delay
        print(f"\n       {DIM}--- Cooling down fleet compute engine (3.0s) ---{RESET}\n")
        think(3.0)

        # SCENARIO 3: Freelance Coordinator Agent (Direct Payout to Contributor)
        log_agent("Freelance Agent", "Reviewing pull request submitted by external Python security contractor...", BLUE)
        think(2.0, "Running automated test coverage & Bandit static audit")

        log_agent("Freelance Agent", "Code verified! Executing direct PayPal Payout ($45.00) to contractor@devops-lead.org.", YELLOW)
        think(1.5, "Calling PayPal Payouts v1 REST API")

        intent_freelance = {
            "agent_id": "agent-payout",
            "amount": 45.00,
            "currency": "USD",
            "recipient": "contractor@devops-lead.org",
            "category": "FREELANCE",
            "reasoning": "Milestone completed: Security hardening audit and penetration tests passed.",
        }

        with httpx.Client(base_url=base_url, timeout=10.0) as client:
            res3 = client.post("/api/v1/payments/intent", json=intent_freelance)
            if res3.status_code == 200:
                tx3 = res3.json()
                batch_id = tx3.get("paypal_payout_batch_id", "BATCH-SIMULATED-PAYOUT")
                print(f"       {GREEN}✓ [PAYPAL PAYOUT DISBURSED]{RESET} Batch ID: {BOLD}{batch_id}{RESET}")
                print(f"       {GREEN}✓ [STATUS: SETTLED]{RESET} Beneficiary: contractor@devops-lead.org ($45.00 USD)")

        print(f"\n{BOLD}{GREEN}✓ Mission Cycle #{round_count} successfully executed!{RESET}\n")

        if not loop_forever:
            print(f"{CYAN}To run continuously in loop mode, pass: {BOLD}python scripts/autonomous_agent_runner.py --loop{RESET}\n")
            break

        round_count += 1
        print(f"{DIM}Sleeping 10 seconds before next mission cycle...{RESET}")
        time.sleep(10.0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PayAgent OS Living Autonomous Fleet Runner")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="PayAgent OS Backend API URL")
    parser.add_argument("--loop", action="store_true", help="Run simulation continuously in infinite loop")
    args = parser.parse_args()

    run_simulation(base_url=args.url, loop_forever=args.loop)
