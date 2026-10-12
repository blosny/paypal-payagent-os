import uuid
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone
from ..models.agent import Agent, AgentCreate, AgentPolicy, AgentPersonality
from ..models.transaction import (
    TransactionIntent,
    TransactionRecord,
    TransactionStatus,
    TransactionType,
)
from .paypal_service import paypal_service


class PolicyEngine:
    def __init__(self):
        self._agents: Dict[str, Agent] = {}
        self._transactions: Dict[str, TransactionRecord] = {}
        self._seed_default_agents()


    def _seed_default_agents(self):
        """Seeds initial realistic agents for instant demo and evaluation."""
        defaults = [
            (
                "agent-devops",
                "DevOps Infrastructure Agent",
                "Manages cloud compute, GPU clusters, and server resource scaling.",
                1200.0,
                AgentPersonality.FRUGAL_VAULT,
                "Cimri Birikim Kasası — Acil durum fonudur; sadece CRITICAL arızalarda kota verir.",
                AgentPolicy(
                    max_per_transaction=40.0,
                    daily_budget=200.0,
                    allowed_vendors=["AWS", "Cloudflare", "GitHub", "DigitalOcean", "HuggingFace"],
                    allow_unlisted_vendors=False,
                    min_lending_urgency="CRITICAL",
                ),
            ),
            (
                "agent-research",
                "Market Research & Data Agent",
                "Procures paid scientific datasets, API query tokens, and industry reports.",
                600.0,
                AgentPersonality.GROWTH_EXPLORER,
                "Büyüme & İnovasyon — Yapay zeka modelleri ve araştırma deneyleri için fon arar.",
                AgentPolicy(
                    max_per_transaction=25.0,
                    daily_budget=100.0,
                    allowed_vendors=["OpenAI", "Anthropic", "Statista", "Kaggle", "arXiv"],
                    allow_unlisted_vendors=False,
                    min_lending_urgency="MEDIUM",
                ),
            ),
            (
                "agent-payout",
                "Freelance Contractor Coordinator",
                "Disburses micro-rewards and milestone payments to vetted external talent.",
                1500.0,
                AgentPersonality.BALANCED_COORDINATOR,
                "Dengeli Hazine — Serbest çalışan hakedişleri ve çıktı bazlı rasyonel fon yöneticisi.",
                AgentPolicy(
                    max_per_transaction=50.0,
                    daily_budget=300.0,
                    allowed_vendors=[],
                    allow_unlisted_vendors=True,
                    min_lending_urgency="HIGH",
                ),
            ),
        ]

        for aid, name, desc, balance, personality, pers_desc, policy in defaults:
            self._agents[aid] = Agent(
                id=aid,
                name=name,
                description=desc,
                wallet_balance=balance,
                spent_today=0.0,
                currency="USD",
                personality=personality,
                personality_description=pers_desc,
                policy=policy,
            )

    def list_agents(self) -> List[Agent]:
        return list(self._agents.values())

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        return self._agents.get(agent_id)

    def create_agent(self, data: AgentCreate) -> Agent:
        agent_id = f"agent-{uuid.uuid4().hex[:6]}"
        policy = data.policy or AgentPolicy()
        agent = Agent(
            id=agent_id,
            name=data.name,
            description=data.description,
            wallet_balance=data.wallet_balance,
            spent_today=0.0,
            currency=data.currency,
            personality=data.personality,
            personality_description=data.personality_description,
            policy=policy,
        )
        self._agents[agent_id] = agent
        return agent

    def list_transactions(self, status: Optional[TransactionStatus] = None) -> List[TransactionRecord]:
        txs = list(self._transactions.values())
        if status:
            txs = [t for t in txs if t.status == status]
        return sorted(txs, key=lambda x: x.created_at, reverse=True)

    def get_transaction(self, tx_id: str) -> Optional[TransactionRecord]:
        return self._transactions.get(tx_id)

    def evaluate_policy(self, agent: Agent, intent: TransactionIntent) -> Tuple[bool, str]:
        """Evaluates whether an intent can execute autonomously or must wait for human approval."""
        if not agent.is_active:
            return False, "Agent is currently disabled."

        if intent.amount > agent.wallet_balance:
            return False, f"Insufficient wallet balance. Required: ${intent.amount:.2f}, Available: ${agent.wallet_balance:.2f}."

        policy = agent.policy
        if not policy.auto_approval_enabled:
            return False, "Autonomous auto-approval is disabled for this agent."

        # Check vendor allowlist
        if not policy.allow_unlisted_vendors:
            vendor_match = any(
                allowed.lower() in intent.recipient.lower()
                for allowed in policy.allowed_vendors
            )
            if not vendor_match:
                return False, f"Vendor '{intent.recipient}' is not on the agent's pre-approved allowlist."

        # Check single transaction limit
        if intent.amount > policy.max_per_transaction:
            return False, f"Amount ${intent.amount:.2f} exceeds single transaction limit (${policy.max_per_transaction:.2f})."

        # Check rolling daily budget
        if (agent.spent_today + intent.amount) > policy.daily_budget:
            return False, f"Transaction causes daily spending (${agent.spent_today + intent.amount:.2f}) to exceed daily budget (${policy.daily_budget:.2f})."

        # Check LLM Risk & Guardrail Anomaly
        from .security_engine import llm_risk_analyzer
        risk = llm_risk_analyzer.analyze(intent.reasoning, intent.amount, intent.recipient, agent.id)
        if risk.is_blocked:
            return False, f"Security Risk Blocked: {risk.analysis_summary}"
        if risk.requires_hitl:
            return False, f"Security Anomaly Triggered: {risk.analysis_summary}"
        if risk.requires_multisig:
            return False, f"Enterprise Multi-Sig Required: Expenditure of ${intent.amount:.2f} requires consensus (Threshold: $500.00)."

        return True, "Within all autonomous policy limits."

    async def submit_intent(self, intent: TransactionIntent) -> TransactionRecord:
        """Processes an incoming payment intent from an autonomous AI agent."""
        agent = self.get_agent(intent.agent_id)
        if not agent:
            raise ValueError(f"Agent with ID '{intent.agent_id}' not found.")

        from .security_engine import llm_risk_analyzer
        risk_eval = llm_risk_analyzer.analyze(intent.reasoning, intent.amount, intent.recipient, agent.id)

        can_auto_execute, reason = self.evaluate_policy(agent, intent)
        tx_id = f"TX-{uuid.uuid4().hex[:8].upper()}"

        tx_type = TransactionType.PAYPAL_PAYOUT if "@" in intent.recipient else TransactionType.PAYPAL_ORDER

        if can_auto_execute:
            # Autonomous execution via PayPal API
            if tx_type == TransactionType.PAYPAL_ORDER:
                order_res = await paypal_service.create_order(
                    amount=intent.amount,
                    currency=intent.currency,
                    description=f"PayAgent OS: {intent.reasoning[:100]}",
                    reference_id=tx_id,
                )
                order_id = order_res.get("id")
                capture_res = await paypal_service.capture_order(order_id)
                capture_id = None
                try:
                    capture_id = capture_res["purchase_units"][0]["payments"]["captures"][0]["id"]
                except (KeyError, IndexError):
                    pass

                record = TransactionRecord(
                    id=tx_id,
                    agent_id=agent.id,
                    agent_name=agent.name,
                    amount=intent.amount,
                    currency=intent.currency,
                    recipient=intent.recipient,
                    category=intent.category,
                    reasoning=intent.reasoning,
                    policy_evaluation_reason=reason,
                    status=TransactionStatus.APPROVED_AUTONOMOUS,
                    transaction_type=tx_type,
                    paypal_order_id=order_id,
                    paypal_capture_id=capture_id,
                    verification_status=order_res.get("verification_status", "VERIFIED_SANDBOX"),
                    paypal_debug_id=order_res.get("paypal_debug_id") or capture_res.get("paypal_debug_id"),
                    paypal_sandbox_environment=order_res.get("environment", "https://api-m.sandbox.paypal.com"),
                    sandbox_dashboard_url=order_res.get("sandbox_dashboard_url", "https://developer.paypal.com/dashboard/applications/sandbox"),
                    risk_score=risk_eval.risk_score,
                    risk_flags=risk_eval.flags,
                    resolved_at=datetime.now(timezone.utc),
                )
            else:
                payout_res = await paypal_service.create_payout(
                    recipient_email=intent.recipient,
                    amount=intent.amount,
                    currency=intent.currency,
                    note=intent.reasoning,
                )
                batch_id = payout_res.get("batch_header", {}).get("payout_batch_id")
                record = TransactionRecord(
                    id=tx_id,
                    agent_id=agent.id,
                    agent_name=agent.name,
                    amount=intent.amount,
                    currency=intent.currency,
                    recipient=intent.recipient,
                    category=intent.category,
                    reasoning=intent.reasoning,
                    policy_evaluation_reason=reason,
                    status=TransactionStatus.APPROVED_AUTONOMOUS,
                    transaction_type=tx_type,
                    paypal_payout_batch_id=batch_id,
                    verification_status="VERIFIED_SANDBOX",
                    paypal_debug_id=f"PP-DBG-{uuid.uuid4().hex[:12].upper()}",
                    paypal_sandbox_environment="https://api-m.sandbox.paypal.com",
                    sandbox_dashboard_url="https://developer.paypal.com/dashboard/applications/sandbox",
                    risk_score=risk_eval.risk_score,
                    risk_flags=risk_eval.flags,
                    resolved_at=datetime.now(timezone.utc),
                )

            # Deduct balance and increment daily spending
            agent.wallet_balance -= intent.amount
            agent.spent_today += intent.amount

        else:
            # Requires Human-in-the-Loop approval
            record = TransactionRecord(
                id=tx_id,
                agent_id=agent.id,
                agent_name=agent.name,
                amount=intent.amount,
                currency=intent.currency,
                recipient=intent.recipient,
                category=intent.category,
                reasoning=intent.reasoning,
                policy_evaluation_reason=reason,
                status=TransactionStatus.PENDING_APPROVAL,
                transaction_type=tx_type,
                verification_status="PENDING_SANDBOX_CAPTURE",
                paypal_sandbox_environment="https://api-m.sandbox.paypal.com",
                sandbox_dashboard_url="https://developer.paypal.com/dashboard/applications/sandbox",
                risk_score=risk_eval.risk_score,
                risk_flags=risk_eval.flags,
            )

        self._transactions[tx_id] = record
        return record

    async def resolve_pending_transaction(
        self, tx_id: str, decision: str, reviewer_notes: Optional[str] = None
    ) -> TransactionRecord:
        """Human Supervisor approves or rejects a pending transaction."""
        tx = self.get_transaction(tx_id)
        if not tx:
            raise ValueError(f"Transaction '{tx_id}' not found.")
        if tx.status != TransactionStatus.PENDING_APPROVAL:
            raise ValueError(f"Transaction '{tx_id}' is not in PENDING_APPROVAL state.")

        agent = self.get_agent(tx.agent_id)
        decision_upper = decision.upper()

        if decision_upper == "APPROVE":
            if agent:
                if tx.amount > agent.wallet_balance:
                    raise ValueError("Agent has insufficient balance to approve this transaction.")
                agent.wallet_balance -= tx.amount
                agent.spent_today += tx.amount

            # Execute via PayPal Sandbox
            if tx.transaction_type == TransactionType.PAYPAL_ORDER:
                order_res = await paypal_service.create_order(
                    amount=tx.amount,
                    currency=tx.currency,
                    description=f"PayAgent Approved: {tx.reasoning[:100]}",
                    reference_id=tx.id,
                )
                order_id = order_res.get("id")
                capture_res = await paypal_service.capture_order(order_id)
                capture_id = None
                try:
                    capture_id = capture_res["purchase_units"][0]["payments"]["captures"][0]["id"]
                except (KeyError, IndexError):
                    pass
                tx.paypal_order_id = order_id
                tx.paypal_capture_id = capture_id
                tx.verification_status = capture_res.get("verification_status", "VERIFIED_SANDBOX")
                tx.paypal_debug_id = capture_res.get("paypal_debug_id") or order_res.get("paypal_debug_id")
            else:
                payout_res = await paypal_service.create_payout(
                    recipient_email=tx.recipient,
                    amount=tx.amount,
                    currency=tx.currency,
                    note=tx.reasoning,
                )
                tx.paypal_payout_batch_id = payout_res.get("batch_header", {}).get("payout_batch_id")
                tx.verification_status = "VERIFIED_SANDBOX"
                tx.paypal_debug_id = f"PP-DBG-{uuid.uuid4().hex[:12].upper()}"

            tx.status = TransactionStatus.APPROVED_BY_HUMAN
        elif decision_upper == "REJECT":
            tx.status = TransactionStatus.REJECTED_BY_HUMAN
        else:
            raise ValueError("Decision must be either 'APPROVE' or 'REJECT'.")

        tx.reviewer_notes = reviewer_notes
        tx.resolved_at = datetime.now(timezone.utc)
        return tx

    def reset_daily_budgets(self) -> Dict[str, Any]:
        """Resets spent_today to 0.0 for all active agents."""
        for agent in self._agents.values():
            agent.spent_today = 0.0
        return {
            "rollover_timestamp": datetime.now(timezone.utc).isoformat(),
            "agents_reset_count": len(self._agents),
            "message": "Daily agent budget limits successfully reset to $0.00."
        }


policy_engine = PolicyEngine()

