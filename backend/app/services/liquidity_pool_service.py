"""
PayAgent OS - Cross-Agent Liquidity Pool Service
Orchestrates an internal, zero-interest liquidity pool where agents sweep idle capital
and borrow micro-advances for sudden compute surges, backed by FICO credit checks and PayPal Vault.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from ..models.liquidity_pool import (
    LoanStatus,
    PoolContribution,
    PoolDrawdown,
    PoolStatus,
    DepositRequest,
    DrawdownRequest,
    RepayRequest,
)
from .credit_service import credit_service


class LiquidityPoolService:
    def __init__(self):
        self._contributions: List[PoolContribution] = []
        self._drawdowns: List[PoolDrawdown] = []
        self._seed_pool()

    def _seed_pool(self):
        self._contributions.clear()
        self._drawdowns.clear()

        # Seed initial contributions from agents with surplus budget
        c1 = PoolContribution(
            contribution_id=f"CONTRIB-{uuid.uuid4().hex[:6].upper()}",
            agent_id="agent-research-01",
            agent_name="Research AI Lab Agent",
            amount=450.00,
            deposited_at=datetime.now(timezone.utc).isoformat(),
        )
        c2 = PoolContribution(
            contribution_id=f"CONTRIB-{uuid.uuid4().hex[:6].upper()}",
            agent_id="agent-growth-01",
            agent_name="Growth Marketing Agent",
            amount=150.00,
            deposited_at=datetime.now(timezone.utc).isoformat(),
        )
        self._contributions.extend([c1, c2])

        # Seed an active drawdown from DevOps agent
        loan = PoolDrawdown(
            loan_id=f"LOAN-{uuid.uuid4().hex[:6].upper()}",
            borrower_agent_id="agent-devops-01",
            borrower_agent_name="DevOps Infrastructure Agent",
            amount=180.00,
            purpose="Emergency Kubernetes Pods Scaling on AWS",
            status=LoanStatus.ACTIVE,
            repaid_amount=0.0,
            borrower_fico_score=780,
            created_at=datetime.now(timezone.utc).isoformat(),
            paypal_liquidity_ref=f"PP-POOL-DRAW-{uuid.uuid4().hex[:6].upper()}",
        )
        self._drawdowns.append(loan)

    def get_status(self) -> PoolStatus:
        total_liquidity = round(sum(c.amount for c in self._contributions), 2)
        active_loans = round(
            sum(
                max(0.0, d.amount - d.repaid_amount)
                for d in self._drawdowns
                if d.status == LoanStatus.ACTIVE
            ),
            2,
        )
        available_liquidity = max(0.0, round(total_liquidity - active_loans, 2))
        utilization = (
            round((active_loans / total_liquidity * 100.0), 1)
            if total_liquidity > 0
            else 0.0
        )

        return PoolStatus(
            total_liquidity_usd=total_liquidity,
            available_liquidity_usd=available_liquidity,
            active_loans_usd=active_loans,
            utilization_rate_pct=utilization,
            total_drawdowns_count=len(self._drawdowns),
            contributions=self._contributions,
            active_drawdowns=self._drawdowns,
            last_updated=datetime.now(timezone.utc).isoformat(),
        )

    def deposit_liquidity(self, req: DepositRequest) -> PoolContribution:
        agent_names = {
            "agent-devops-01": "DevOps Infrastructure Agent",
            "agent-research-01": "Research AI Lab Agent",
            "agent-growth-01": "Growth Marketing Agent",
        }
        name = agent_names.get(req.agent_id, f"Agent {req.agent_id}")

        contribution = PoolContribution(
            contribution_id=f"CONTRIB-{uuid.uuid4().hex[:6].upper()}",
            agent_id=req.agent_id,
            agent_name=name,
            amount=round(req.amount, 2),
            deposited_at=datetime.now(timezone.utc).isoformat(),
        )
        self._contributions.append(contribution)
        return contribution

    def request_drawdown(self, req: DrawdownRequest) -> PoolDrawdown:
        status = self.get_status()
        if req.amount > status.available_liquidity_usd:
            raise ValueError(
                f"Requested loan amount (${req.amount:.2f}) exceeds available pool liquidity (${status.available_liquidity_usd:.2f})"
            )

        # Verify Borrower's AI FICO Credit Score
        fico_record = credit_service.get_score(req.borrower_agent_id)
        fico_score = fico_record.score if fico_record else 720

        if fico_score < 650:
            raise ValueError(
                f"Agent FICO score ({fico_score}) is below minimum liquidity trust threshold (650 - Monitored/Restricted)"
            )

        agent_names = {
            "agent-devops-01": "DevOps Infrastructure Agent",
            "agent-research-01": "Research AI Lab Agent",
            "agent-growth-01": "Growth Marketing Agent",
        }
        name = agent_names.get(req.borrower_agent_id, f"Agent {req.borrower_agent_id}")

        drawdown = PoolDrawdown(
            loan_id=f"LOAN-{uuid.uuid4().hex[:6].upper()}",
            borrower_agent_id=req.borrower_agent_id,
            borrower_agent_name=name,
            amount=round(req.amount, 2),
            purpose=req.purpose,
            status=LoanStatus.ACTIVE,
            repaid_amount=0.0,
            borrower_fico_score=fico_score,
            created_at=datetime.now(timezone.utc).isoformat(),
            paypal_liquidity_ref=f"PP-POOL-DRAW-{uuid.uuid4().hex[:6].upper()}",
        )
        self._drawdowns.insert(0, drawdown)
        return drawdown

    def repay_loan(self, req: RepayRequest) -> PoolDrawdown:
        target_loan: Optional[PoolDrawdown] = None
        for d in self._drawdowns:
            if d.loan_id == req.loan_id:
                target_loan = d
                break

        if not target_loan:
            raise ValueError(f"Loan record {req.loan_id} not found")

        if target_loan.status == LoanStatus.REPAID:
            return target_loan

        remaining = target_loan.amount - target_loan.repaid_amount
        repay_amt = req.amount if req.amount is not None else remaining
        repay_amt = min(repay_amt, remaining)

        target_loan.repaid_amount = round(target_loan.repaid_amount + repay_amt, 2)
        if target_loan.repaid_amount >= target_loan.amount:
            target_loan.status = LoanStatus.REPAID

        return target_loan


# Global singleton instance
liquidity_pool_service = LiquidityPoolService()
