"""
PayAgent OS - Fee Optimizer & Smart Payment Rail Routing Service
Analyzes transaction size, urgency, currency, and vendor country to compute the
most cost-efficient PayPal rail (Balance, ACH, Commercial Card, Cross-Border Clearing),
saving companies thousands of dollars in unnecessary interchange and gateway fees.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict
from ..models.fee_optimizer import (
    PaymentRail,
    PaymentUrgency,
    RailFeeQuote,
    FeeOptimizationRequest,
    FeeOptimizationResult,
    FleetFeeSavingsSummary,
)


class FeeOptimizerService:
    def __init__(self):
        # In-memory history with rich realistic seeds
        self._history: List[FeeOptimizationResult] = []
        self._seed_realistic_history()

    def _seed_realistic_history(self):
        sample_scenarios = [
            FeeOptimizationRequest(
                amount=1250.00,
                currency="USD",
                vendor_name="AWS Cloud Compute",
                vendor_country="US",
                urgency=PaymentUrgency.STANDARD,
                agent_id="agent-devops-01",
            ),
            FeeOptimizationRequest(
                amount=340.00,
                currency="EUR",
                vendor_name="HuggingFace Hub Pro",
                vendor_country="FR",
                urgency=PaymentUrgency.STANDARD,
                agent_id="agent-research-01",
            ),
            FeeOptimizationRequest(
                amount=45.00,
                currency="USD",
                vendor_name="OpenAI API Credits",
                vendor_country="US",
                urgency=PaymentUrgency.INSTANT,
                agent_id="agent-growth-01",
            ),
            FeeOptimizationRequest(
                amount=2400.00,
                currency="USD",
                vendor_name="Datadog Enterprise APM",
                vendor_country="US",
                urgency=PaymentUrgency.BATCH,
                agent_id="agent-devops-01",
            ),
        ]
        for req in sample_scenarios:
            self.evaluate_transaction(req)

    def evaluate_transaction(self, req: FeeOptimizationRequest) -> FeeOptimizationResult:
        opt_id = f"OPT-{uuid.uuid4().hex[:8].upper()}"
        quotes: List[RailFeeQuote] = []

        # 1. Commercial Card (Standard baseline rail)
        # Standard merchant interchange: 2.9% + $0.30 fixed
        card_pct = 2.9
        card_fixed = 0.30
        card_fee = round((req.amount * (card_pct / 100.0)) + card_fixed, 2)
        card_quote = RailFeeQuote(
            rail=PaymentRail.PAYPAL_COMMERCIAL_CARD,
            rail_name="PayPal Commercial Card",
            fee_percentage=card_pct,
            fixed_fee_usd=card_fixed,
            total_fee_usd=card_fee,
            settlement_speed="Instant",
            recommendation_reason="Standard credit rail with highest interchange fee.",
        )
        quotes.append(card_quote)

        # 2. PayPal Balance (Intra-ecosystem wallet transfer)
        # Stored balance: 1.0% + $0.05 (capped at $10.00)
        balance_pct = 1.0
        balance_fixed = 0.05
        raw_balance_fee = (req.amount * (balance_pct / 100.0)) + balance_fixed
        balance_fee = round(min(raw_balance_fee, 10.00), 2)
        balance_quote = RailFeeQuote(
            rail=PaymentRail.PAYPAL_BALANCE,
            rail_name="PayPal Treasury Balance",
            fee_percentage=balance_pct,
            fixed_fee_usd=balance_fixed,
            total_fee_usd=balance_fee,
            settlement_speed="Instant (Zero Settlement Latency)",
            recommendation_reason="Flat 1% fee with $10 cap; best for instant sub-$500 transactions.",
        )
        quotes.append(balance_quote)

        # 3. PayPal ACH Bank Direct Debit
        # B2B direct debit: 0.8% capped at $5.00 + $0.15 fixed
        ach_pct = 0.8
        ach_fixed = 0.15
        raw_ach_fee = (req.amount * (ach_pct / 100.0))
        capped_ach_fee = min(raw_ach_fee, 5.00) + ach_fixed
        ach_fee = round(capped_ach_fee, 2)
        ach_quote = RailFeeQuote(
            rail=PaymentRail.PAYPAL_ACH_BANK,
            rail_name="PayPal ACH Direct Debit",
            fee_percentage=ach_pct,
            fixed_fee_usd=ach_fixed,
            total_fee_usd=ach_fee,
            settlement_speed="1-2 Business Days",
            recommendation_reason="Hard $5 fee ceiling; delivers massive 80%+ fee savings on high-ticket invoices.",
        )
        quotes.append(ach_quote)

        # 4. Cross-Border Local Clearing Rail
        is_cross_border = req.currency.upper() != "USD" or req.vendor_country.upper() != "US"
        if is_cross_border:
            # Native currency matching saves standard 3.5% FX spread
            xb_pct = 0.5
            xb_fixed = 0.20
            xb_fee = round((req.amount * (xb_pct / 100.0)) + xb_fixed, 2)
            xb_quote = RailFeeQuote(
                rail=PaymentRail.CROSS_BORDER_LOCAL_CLEARING,
                rail_name="PayPal Local Clearing & FX Arbitrage",
                fee_percentage=xb_pct,
                fixed_fee_usd=xb_fixed,
                total_fee_usd=xb_fee,
                settlement_speed="Instant (Local Domestic Rails)",
                recommendation_reason="Bypasses standard 3.5% cross-border FX markup via in-country liquidity pools.",
            )
            quotes.append(xb_quote)

        # Determine Optimal Rail based on urgency and fees:
        eligible_quotes = quotes.copy()
        if req.urgency == PaymentUrgency.INSTANT:
            # Instant urgency filters out ACH (which takes 1-2 days)
            eligible_quotes = [q for q in eligible_quotes if q.rail != PaymentRail.PAYPAL_ACH_BANK]

        # Best quote is the one with minimum total fee
        best_quote = min(eligible_quotes, key=lambda q: q.total_fee_usd)
        best_quote.is_optimal = True

        standard_fee = card_fee
        fee_saved = max(0.0, round(standard_fee - best_quote.total_fee_usd, 2))
        fee_reduction_pct = round((fee_saved / standard_fee * 100.0), 1) if standard_fee > 0 else 0.0

        verdict = (
            f"Routing via {best_quote.rail_name} saves ${fee_saved:.2f} ({fee_reduction_pct:.1f}% reduction) "
            f"vs commercial card interchange baseline."
        )

        routing_token = f"PP-ROUTE-{uuid.uuid4().hex[:10].upper()}"

        result = FeeOptimizationResult(
            optimization_id=opt_id,
            amount=req.amount,
            currency=req.currency,
            vendor_name=req.vendor_name,
            urgency=req.urgency,
            quotes=quotes,
            standard_rail=PaymentRail.PAYPAL_COMMERCIAL_CARD,
            standard_fee_usd=standard_fee,
            optimal_rail=best_quote.rail,
            optimal_fee_usd=best_quote.total_fee_usd,
            fee_saved_usd=fee_saved,
            fee_reduction_pct=fee_reduction_pct,
            routing_verdict=verdict,
            paypal_routing_token=routing_token,
        )

        self._history.insert(0, result)
        return result

    def get_history(self, limit: int = 15) -> List[FeeOptimizationResult]:
        return self._history[:limit]

    def get_summary(self) -> FleetFeeSavingsSummary:
        if not self._history:
            return FleetFeeSavingsSummary(
                total_optimized_transactions=0,
                cumulative_fees_saved_usd=0.0,
                average_fee_reduction_pct=0.0,
                top_recommended_rail=PaymentRail.PAYPAL_ACH_BANK,
                rail_distribution={},
                last_updated=datetime.now(timezone.utc).isoformat(),
            )

        total_tx = len(self._history)
        total_saved = round(sum(item.fee_saved_usd for item in self._history), 2)
        avg_pct = round(sum(item.fee_reduction_pct for item in self._history) / total_tx, 1)

        distribution: Dict[str, int] = {}
        for item in self._history:
            distribution[item.optimal_rail.value] = distribution.get(item.optimal_rail.value, 0) + 1

        top_rail_str = max(distribution, key=distribution.get) if distribution else PaymentRail.PAYPAL_ACH_BANK.value

        return FleetFeeSavingsSummary(
            total_optimized_transactions=total_tx,
            cumulative_fees_saved_usd=total_saved,
            average_fee_reduction_pct=avg_pct,
            top_recommended_rail=PaymentRail(top_rail_str),
            rail_distribution=distribution,
            last_updated=datetime.now(timezone.utc).isoformat(),
        )


# Global singleton instance
fee_optimizer_service = FeeOptimizerService()
