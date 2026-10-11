from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DisputeSpeaker(str, Enum):
    AGENT = "AGENT"
    VENDOR_BOT = "VENDOR_BOT"


class DisputeStrategy(str, Enum):
    VOLUME_COMMITMENT = "VOLUME_COMMITMENT"
    SLA_DOWNTIME_CREDIT = "SLA_DOWNTIME_CREDIT"
    UNUSED_SEATS_RECLAMATION = "UNUSED_SEATS_RECLAMATION"


class DisputeRound(BaseModel):
    round_num: int
    speaker: DisputeSpeaker
    speaker_name: str
    message: str
    offered_amount: float


class InvoiceDisputeRecord(BaseModel):
    dispute_id: str
    vendor_name: str
    invoice_ref: str
    original_amount: float
    agreed_amount: float
    saved_amount: float
    discount_rate_percent: float
    strategy: DisputeStrategy
    status: str = "SETTLED"  # SETTLED, IN_PROGRESS, ESCALATED
    rounds: List[DisputeRound] = Field(default_factory=list)
    settled_at: str
    paypal_settlement_id: str


class DisputeInitiateRequest(BaseModel):
    vendor_name: str = "Datadog APM"
    invoice_ref: str = "INV-DDG-9941"
    original_amount: float = 240.00
    strategy: DisputeStrategy = DisputeStrategy.VOLUME_COMMITMENT
    target_discount_percent: float = 20.0
