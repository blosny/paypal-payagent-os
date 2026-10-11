import uuid
from typing import Dict, List, Optional
from datetime import datetime, timezone
from ..models.dispute import (
    DisputeSpeaker,
    DisputeStrategy,
    DisputeRound,
    InvoiceDisputeRecord,
    DisputeInitiateRequest,
)


class InvoiceDisputeService:
    """Autonomous negotiation & dispute settlement bot for SaaS and cloud infrastructure invoices."""

    def __init__(self):
        self._history: Dict[str, InvoiceDisputeRecord] = {}
        self._init_mock_disputes()

    def _init_mock_disputes(self):
        now = datetime.now(timezone.utc).isoformat()
        sample = InvoiceDisputeRecord(
            dispute_id="disp_ddg_9912",
            vendor_name="Datadog APM & Logs",
            invoice_ref="INV-DDG-88210",
            original_amount=240.00,
            agreed_amount=196.80,
            saved_amount=43.20,
            discount_rate_percent=18.0,
            strategy=DisputeStrategy.VOLUME_COMMITMENT,
            status="SETTLED",
            rounds=[
                DisputeRound(
                    round_num=1,
                    speaker=DisputeSpeaker.AGENT,
                    speaker_name="PayAgent Autonomous Negotiator",
                    message="Our fleet is scaling infrastructure to 500+ agent hours next quarter. We request an 18% annual tier discount on this invoice.",
                    offered_amount=196.80,
                ),
                DisputeRound(
                    round_num=2,
                    speaker=DisputeSpeaker.VENDOR_BOT,
                    speaker_name="Datadog Automated Billing Bot",
                    message="Commitment verified against agent workload projections. Tier discount approved. Updating PayPal invoice.",
                    offered_amount=196.80,
                ),
            ],
            settled_at=now,
            paypal_settlement_id="PP-INV-SETTLED-88210",
        )
        self._history[sample.dispute_id] = sample

    def list_disputes(self) -> List[InvoiceDisputeRecord]:
        return list(self._history.values())

    def get_dispute(self, dispute_id: str) -> Optional[InvoiceDisputeRecord]:
        return self._history.get(dispute_id)

    def initiate_negotiation(self, request: DisputeInitiateRequest) -> InvoiceDisputeRecord:
        now_iso = datetime.now(timezone.utc).isoformat()
        dispute_id = f"disp_{uuid.uuid4().hex[:8]}"

        # Calculate realistic settlement based on target and strategy
        target_discount = min(30.0, max(5.0, request.target_discount_percent))
        actual_discount_percent = round(target_discount * 0.9, 1)  # Settles slightly under max request
        saved = round((actual_discount_percent / 100.0) * request.original_amount, 2)
        agreed_amount = round(request.original_amount - saved, 2)

        rounds = []
        if request.strategy == DisputeStrategy.VOLUME_COMMITMENT:
            rounds.append(
                DisputeRound(
                    round_num=1,
                    speaker=DisputeSpeaker.AGENT,
                    speaker_name="PayAgent Autonomous Negotiator",
                    message=f"Our agent fleet commits to expanded monthly usage across {request.vendor_name}. We formally request a {target_discount:.0f}% enterprise commitment credit.",
                    offered_amount=round(request.original_amount * (1.0 - (target_discount / 100.0)), 2),
                )
            )
            rounds.append(
                DisputeRound(
                    round_num=2,
                    speaker=DisputeSpeaker.VENDOR_BOT,
                    speaker_name=f"{request.vendor_name} Billing Bot",
                    message=f"Telemetry verified. Counter-offering a {actual_discount_percent}% recurring rebate settled via PayPal Orders v2.",
                    offered_amount=agreed_amount,
                )
            )
            rounds.append(
                DisputeRound(
                    round_num=3,
                    speaker=DisputeSpeaker.AGENT,
                    speaker_name="PayAgent Autonomous Negotiator",
                    message=f"Counter-offer accepted at ${agreed_amount:.2f}. Executing discounted settlement via PayPal.",
                    offered_amount=agreed_amount,
                )
            )
        elif request.strategy == DisputeStrategy.SLA_DOWNTIME_CREDIT:
            rounds.append(
                DisputeRound(
                    round_num=1,
                    speaker=DisputeSpeaker.AGENT,
                    speaker_name="PayAgent Autonomous Negotiator",
                    message=f"Telemetry logs show 99.3% availability vs. 99.9% contractual SLA on {request.vendor_name}. Requesting ${saved:.2f} service outage credit.",
                    offered_amount=agreed_amount,
                )
            )
            rounds.append(
                DisputeRound(
                    round_num=2,
                    speaker=DisputeSpeaker.VENDOR_BOT,
                    speaker_name=f"{request.vendor_name} Billing Bot",
                    message=f"Downtime ticket corroborated. Credit of ${saved:.2f} credited to invoice balance.",
                    offered_amount=agreed_amount,
                )
            )
        else:  # UNUSED_SEATS_RECLAMATION
            rounds.append(
                DisputeRound(
                    round_num=1,
                    speaker=DisputeSpeaker.AGENT,
                    speaker_name="PayAgent Autonomous Negotiator",
                    message=f"PayPal Vault seat audit detected 0 active agent queries on provisioned seats in {request.vendor_name}. Reclaiming unutilized quota.",
                    offered_amount=agreed_amount,
                )
            )
            rounds.append(
                DisputeRound(
                    round_num=2,
                    speaker=DisputeSpeaker.VENDOR_BOT,
                    speaker_name=f"{request.vendor_name} Billing Bot",
                    message=f"Idle seat telemetry validated. Idle seat charges deducted. Final payable: ${agreed_amount:.2f}.",
                    offered_amount=agreed_amount,
                )
            )

        record = InvoiceDisputeRecord(
            dispute_id=dispute_id,
            vendor_name=request.vendor_name,
            invoice_ref=request.invoice_ref,
            original_amount=request.original_amount,
            agreed_amount=agreed_amount,
            saved_amount=saved,
            discount_rate_percent=actual_discount_percent,
            strategy=request.strategy,
            status="SETTLED",
            rounds=rounds,
            settled_at=now_iso,
            paypal_settlement_id=f"PP-SETTLED-{uuid.uuid4().hex[:8].upper()}",
        )
        self._history[dispute_id] = record
        return record


dispute_service = InvoiceDisputeService()
