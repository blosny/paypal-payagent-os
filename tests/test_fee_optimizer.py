"""
PayAgent OS - Test Suite for Fee Optimizer & Smart Payment Rail Routing
Tests rail selection algorithms, ACH fee caps, instant urgency filtering,
cross-border local clearing FX arbitrage, and API endpoints.
"""

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.fee_optimizer import PaymentRail, PaymentUrgency

client = TestClient(app)


def test_fee_summary_and_history():
    # 1. Summary
    res_sum = client.get("/api/v1/fees/summary")
    assert res_sum.status_code == 200
    summary = res_sum.json()
    assert summary["total_optimized_transactions"] >= 4
    assert summary["cumulative_fees_saved_usd"] > 0
    assert summary["average_fee_reduction_pct"] > 0
    assert "rail_distribution" in summary

    # 2. History
    res_hist = client.get("/api/v1/fees/history?limit=5")
    assert res_hist.status_code == 200
    history = res_hist.json()
    assert len(history) <= 5
    assert len(history) > 0
    first = history[0]
    assert "optimization_id" in first
    assert "optimal_rail" in first
    assert first["paypal_routing_token"].startswith("PP-ROUTE-")


def test_evaluate_high_ticket_standard_ach():
    payload = {
        "amount": 2500.00,
        "currency": "USD",
        "vendor_name": "Snowflake Enterprise Data Warehouse",
        "vendor_country": "US",
        "urgency": "STANDARD",
        "agent_id": "agent-devops-01",
    }
    res = client.post("/api/v1/fees/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()

    # For $2,500:
    # Card = 2500 * 2.9% + 0.30 = $72.80
    # ACH = cap $5.00 + 0.15 = $5.15
    # Optimal should be ACH
    assert data["optimal_rail"] == PaymentRail.PAYPAL_ACH_BANK.value
    assert data["standard_fee_usd"] == 72.80
    assert data["optimal_fee_usd"] == 5.15
    assert data["fee_saved_usd"] == 67.65
    assert data["fee_reduction_pct"] > 90.0
    assert "saves $67.65" in data["routing_verdict"]


def test_evaluate_instant_urgency_filters_ach():
    payload = {
        "amount": 200.00,
        "currency": "USD",
        "vendor_name": "Emergency Anthropic API Burst",
        "vendor_country": "US",
        "urgency": "INSTANT",
        "agent_id": "agent-growth-01",
    }
    res = client.post("/api/v1/fees/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()

    # Instant cannot use ACH (which takes 1-2 days)
    # Balance (1% + 0.05 = $2.05) vs Card (2.9% + 0.30 = $6.10)
    assert data["optimal_rail"] == PaymentRail.PAYPAL_BALANCE.value
    assert data["optimal_fee_usd"] < data["standard_fee_usd"]
    assert data["fee_saved_usd"] > 0


def test_evaluate_cross_border_fx():
    payload = {
        "amount": 400.00,
        "currency": "EUR",
        "vendor_name": "Mistral AI Paris API",
        "vendor_country": "FR",
        "urgency": "STANDARD",
        "agent_id": "agent-research-01",
    }
    res = client.post("/api/v1/fees/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()

    rails_present = [q["rail"] for q in data["quotes"]]
    assert PaymentRail.CROSS_BORDER_LOCAL_CLEARING.value in rails_present
    assert data["fee_saved_usd"] > 0


def test_run_fleet_benchmark():
    res = client.post("/api/v1/fees/benchmark")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 3
    for item in data:
        assert item["optimization_id"].startswith("OPT-")
        assert item["fee_saved_usd"] >= 0
        assert item["paypal_routing_token"].startswith("PP-ROUTE-")


def test_evaluate_batch_urgency_prefers_ach():
    payload = {
        "amount": 5000.00,
        "currency": "USD",
        "vendor_name": "Datadog Annual Platform Invoice",
        "vendor_country": "US",
        "urgency": "BATCH",
        "agent_id": "agent-devops-01",
    }
    res = client.post("/api/v1/fees/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["optimal_rail"] == PaymentRail.PAYPAL_ACH_BANK.value
    assert data["standard_fee_usd"] == 145.30
    assert data["optimal_fee_usd"] == 5.15
    assert data["fee_saved_usd"] == 140.15
    assert data["fee_reduction_pct"] > 95.0


def test_micro_transaction_routing():
    payload = {
        "amount": 10.00,
        "currency": "USD",
        "vendor_name": "GitHub Copilot Extra Seat",
        "vendor_country": "US",
        "urgency": "INSTANT",
        "agent_id": "agent-growth-01",
    }
    res = client.post("/api/v1/fees/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["amount"] == 10.00
    assert data["optimal_rail"] == PaymentRail.PAYPAL_BALANCE.value
    # Balance fee on $10: 10 * 1% + 0.05 = $0.15 vs Card: 10 * 2.9% + 0.30 = $0.59
    assert data["optimal_fee_usd"] < data["standard_fee_usd"]

