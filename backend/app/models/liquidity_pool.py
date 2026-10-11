"""
PayAgent OS - Cross-Agent Liquidity Pool Models
Defines internal zero-interest micro-financing pools, idle capital contributions,
and automated drawdown/repayment contracts between agents.
"""

from enum import Enum
from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class LoanStatus(str, Enum):
    ACTIVE = "ACTIVE"
    REPAID = "REPAID"
    DEFAULTED = "DEFAULTED"


class PoolContribution(BaseModel):
    contribution_id: str
    agent_id: str
    agent_name: str
    amount: float
    deposited_at: str


class PoolDrawdown(BaseModel):
    loan_id: str
    borrower_agent_id: str
    borrower_agent_name: str
    amount: float
    purpose: str
    status: LoanStatus = LoanStatus.ACTIVE
    repaid_amount: float = 0.0
    borrower_fico_score: int
    created_at: str
    paypal_liquidity_ref: str


class PoolStatus(BaseModel):
    total_liquidity_usd: float
    available_liquidity_usd: float
    active_loans_usd: float
    utilization_rate_pct: float
    total_drawdowns_count: int
    contributions: List[PoolContribution]
    active_drawdowns: List[PoolDrawdown]
    last_updated: str


class DepositRequest(BaseModel):
    agent_id: str = Field(..., description="Agent depositing idle surplus")
    amount: float = Field(..., gt=0, description="Amount in USD to sweep into pool")


class DrawdownRequest(BaseModel):
    borrower_agent_id: str = Field(..., description="Agent requesting liquidity")
    amount: float = Field(..., gt=0, description="Amount in USD needed")
    purpose: str = Field(..., description="Reason for drawdown (e.g. Emergency GPU compute burst)")


class RepayRequest(BaseModel):
    loan_id: str = Field(..., description="Active loan ID to repay")
    amount: Optional[float] = Field(default=None, description="Amount to repay (defaults to full outstanding)")
