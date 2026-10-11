"""
PayAgent OS - Fee Optimizer & Payment Rail API Routes
Allows agents and supervisors to evaluate payment rails, retrieve cumulative fee savings,
and benchmark payment routing across fleet ticket sizes.
"""

from typing import List
from fastapi import APIRouter, Query
from ...models.fee_optimizer import (
    FeeOptimizationRequest,
    FeeOptimizationResult,
    FleetFeeSavingsSummary,
    PaymentUrgency,
)
from ...services.fee_optimizer_service import fee_optimizer_service

router = APIRouter(prefix="/fees", tags=["Fee Optimizer & Smart Routing"])


@router.get("/summary", response_model=FleetFeeSavingsSummary)
def get_fleet_fee_summary():
    """
    Returns cumulative fee savings, top recommended payment rail, and rail distribution.
    """
    return fee_optimizer_service.get_summary()


@router.get("/history", response_model=List[FeeOptimizationResult])
def get_fee_optimization_history(limit: int = Query(default=15, ge=1, le=50)):
    """
    Returns the recent fee optimization evaluations and rail routing decisions.
    """
    return fee_optimizer_service.get_history(limit=limit)


@router.post("/evaluate", response_model=FeeOptimizationResult)
def evaluate_transaction_fee(req: FeeOptimizationRequest):
    """
    Evaluates payment rails for a given transaction amount, currency, and urgency.
    Selects the optimal PayPal rail and calculates exact fee savings vs commercial cards.
    """
    return fee_optimizer_service.evaluate_transaction(req)


@router.post("/benchmark", response_model=List[FeeOptimizationResult])
def run_fleet_benchmark():
    """
    Runs a benchmark evaluation across micro, medium, and high-ticket transactions.
    """
    benchmark_cases = [
        FeeOptimizationRequest(
            amount=25.00,
            currency="USD",
            vendor_name="Anthropic Claude Token Top-up",
            vendor_country="US",
            urgency=PaymentUrgency.INSTANT,
            agent_id="agent-growth-01",
        ),
        FeeOptimizationRequest(
            amount=500.00,
            currency="USD",
            vendor_name="RunPod GPU Cluster Pods",
            vendor_country="US",
            urgency=PaymentUrgency.STANDARD,
            agent_id="agent-devops-01",
        ),
        FeeOptimizationRequest(
            amount=3200.00,
            currency="USD",
            vendor_name="Snowflake Data Cloud Warehouse",
            vendor_country="US",
            urgency=PaymentUrgency.BATCH,
            agent_id="agent-research-01",
        ),
    ]
    results = [fee_optimizer_service.evaluate_transaction(c) for c in benchmark_cases]
    return results
