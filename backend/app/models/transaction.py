from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class TransactionStatus(str, Enum):
    APPROVED_AUTONOMOUS = "APPROVED_AUTONOMOUS"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED_BY_HUMAN = "APPROVED_BY_HUMAN"
    REJECTED_BY_HUMAN = "REJECTED_BY_HUMAN"
    REJECTED_BY_POLICY = "REJECTED_BY_POLICY"
    FAILED = "FAILED"
    SETTLED = "SETTLED"


class TransactionType(str, Enum):
    PAYPAL_ORDER = "PAYPAL_ORDER"
    PAYPAL_PAYOUT = "PAYPAL_PAYOUT"


class TransactionIntent(BaseModel):
    agent_id: str = Field(..., description="ID of the autonomous calling agent")
    amount: float = Field(..., gt=0, description="Amount to be paid")
    currency: str = Field(default="USD")
    recipient: str = Field(..., description="Vendor name or PayPal email/receiver")
    recipient_type: str = Field(default="VENDOR", description="VENDOR or PAYPAL_EMAIL")
    category: str = Field(default="API_QUOTA", description="Category of purchase e.g. INFRASTRUCTURE, DATASET, FREELANCE")
    reasoning: str = Field(..., description="AI's natural language reasoning for why this payment is required")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ApprovalAction(BaseModel):
    decision: str = Field(..., description="'APPROVE' or 'REJECT'")
    reviewer_notes: Optional[str] = Field(default=None)


class TransactionRecord(BaseModel):
    id: str
    agent_id: str
    agent_name: str
    amount: float
    currency: str
    recipient: str
    category: str
    reasoning: str
    policy_evaluation_reason: str
    status: TransactionStatus
    transaction_type: TransactionType = TransactionType.PAYPAL_ORDER
    paypal_order_id: Optional[str] = None
    paypal_capture_id: Optional[str] = None
    paypal_payout_batch_id: Optional[str] = None
    shortfall_amount: Optional[float] = None
    proposed_donor_agent_id: Optional[str] = None
    proposed_donor_agent_name: Optional[str] = None
    borrowing_proposal_note: Optional[str] = None
    risk_score: Optional[float] = None
    risk_flags: Optional[list] = None
    verification_status: Optional[str] = "VERIFIED_SANDBOX"
    paypal_debug_id: Optional[str] = None
    paypal_sandbox_environment: Optional[str] = "https://api-m.sandbox.paypal.com"
    sandbox_dashboard_url: Optional[str] = "https://developer.paypal.com/dashboard/applications/sandbox"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    reviewer_notes: Optional[str] = None

