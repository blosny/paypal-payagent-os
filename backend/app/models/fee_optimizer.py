"""
PayAgent OS - Fee Optimizer & Smart Payment Rail Routing Models
Evaluates payment rails (PayPal Balance, ACH Direct Debit, Commercial Card, Cross-Border Clearing)
to automatically route agent transactions through the lowest-fee rail.
"""

from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class PaymentRail(str, Enum):
    PAYPAL_BALANCE = "PAYPAL_BALANCE"
    PAYPAL_ACH_BANK = "PAYPAL_ACH_BANK"
    PAYPAL_COMMERCIAL_CARD = "PAYPAL_COMMERCIAL_CARD"
    CROSS_BORDER_LOCAL_CLEARING = "CROSS_BORDER_LOCAL_CLEARING"


class PaymentUrgency(str, Enum):
    STANDARD = "STANDARD"      # Cost-optimized, can take 1-2 business days (ACH eligible)
    INSTANT = "INSTANT"        # Millisecond settlement required (Balance or Card)
    BATCH = "BATCH"            # End-of-day consolidated bulk payout


class RailFeeQuote(BaseModel):
    rail: PaymentRail
    rail_name: str
    fee_percentage: float = Field(..., description="Variable percentage fee (e.g. 2.9 for 2.9%)")
    fixed_fee_usd: float = Field(..., description="Fixed fee per transaction in USD")
    total_fee_usd: float = Field(..., description="Calculated total fee in USD")
    settlement_speed: str = Field(..., description="Expected settlement time (e.g. 'Instant', '1-2 Days')")
    is_optimal: bool = False
    recommendation_reason: str = ""


class FeeOptimizationRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Transaction amount in target currency")
    currency: str = Field(default="USD", description="Currency code (USD, EUR, GBP, TRY)")
    vendor_name: str = Field(default="Vendor API", description="Recipient or merchant name")
    vendor_country: str = Field(default="US", description="Two-letter ISO country code")
    urgency: PaymentUrgency = Field(default=PaymentUrgency.STANDARD, description="Speed requirement")
    agent_id: Optional[str] = Field(default="agent-devops-01", description="Initiating agent ID")


class FeeOptimizationResult(BaseModel):
    optimization_id: str
    amount: float
    currency: str
    vendor_name: str
    urgency: PaymentUrgency
    quotes: List[RailFeeQuote]
    standard_rail: PaymentRail = PaymentRail.PAYPAL_COMMERCIAL_CARD
    standard_fee_usd: float
    optimal_rail: PaymentRail
    optimal_fee_usd: float
    fee_saved_usd: float
    fee_reduction_pct: float
    routing_verdict: str
    paypal_routing_token: str


class FleetFeeSavingsSummary(BaseModel):
    total_optimized_transactions: int
    cumulative_fees_saved_usd: float
    average_fee_reduction_pct: float
    top_recommended_rail: PaymentRail
    rail_distribution: Dict[str, int]
    last_updated: str
