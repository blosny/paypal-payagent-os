"""
PayAgent OS - Test Suite for Cross-Agent Liquidity Pool
Tests pool balance status, idle capital deposits, credit-verified drawdowns,
over-limit rejections, and atomic loan repayments.
"""

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.liquidity_pool import LoanStatus

client = TestClient(app)


def test_pool_status():
    res = client.get("/api/v1/liquidity-pool/status")
    assert res.status_code == 200
    data = res.json()
    assert data["total_liquidity_usd"] >= 600.0
    assert data["available_liquidity_usd"] > 0
    assert data["active_loans_usd"] >= 180.0
    assert data["utilization_rate_pct"] > 0
    assert len(data["contributions"]) >= 2
    assert len(data["active_drawdowns"]) >= 1


def test_deposit_idle_liquidity():
    payload = {
        "agent_id": "agent-devops-01",
        "amount": 200.00,
    }
    res = client.post("/api/v1/liquidity-pool/deposit", json=payload)
    assert res.status_code == 200
    contrib = res.json()
    assert contrib["contribution_id"].startswith("CONTRIB-")
    assert contrib["agent_id"] == "agent-devops-01"
    assert contrib["amount"] == 200.00

    # Verify pool status updated
    status_res = client.get("/api/v1/liquidity-pool/status")
    assert status_res.status_code == 200
    assert status_res.json()["total_liquidity_usd"] >= 800.0


def test_drawdown_success():
    payload = {
        "borrower_agent_id": "agent-research-01",
        "amount": 100.00,
        "purpose": "Sudden Fine-Tuning Batch Tokens on HuggingFace",
    }
    res = client.post("/api/v1/liquidity-pool/drawdown", json=payload)
    assert res.status_code == 200
    loan = res.json()
    assert loan["loan_id"].startswith("LOAN-")
    assert loan["borrower_agent_id"] == "agent-research-01"
    assert loan["amount"] == 100.00
    assert loan["status"] == LoanStatus.ACTIVE.value
    assert loan["borrower_fico_score"] >= 650
    assert loan["paypal_liquidity_ref"].startswith("PP-POOL-DRAW-")


def test_drawdown_exceeds_available_fails():
    payload = {
        "borrower_agent_id": "agent-devops-01",
        "amount": 50000.00,
        "purpose": "Gigantic cluster purchase beyond pool reserves",
    }
    res = client.post("/api/v1/liquidity-pool/drawdown", json=payload)
    assert res.status_code == 400
    assert "exceeds available pool liquidity" in res.json()["detail"]


def test_repay_loan():
    # First get an active loan
    status_res = client.get("/api/v1/liquidity-pool/status")
    active_loans = [d for d in status_res.json()["active_drawdowns"] if d["status"] == "ACTIVE"]
    assert len(active_loans) > 0
    loan_to_repay = active_loans[0]

    repay_payload = {
        "loan_id": loan_to_repay["loan_id"],
        "amount": loan_to_repay["amount"],
    }
    res = client.post("/api/v1/liquidity-pool/repay", json=repay_payload)
    assert res.status_code == 200
    repaid_data = res.json()
    assert repaid_data["loan_id"] == loan_to_repay["loan_id"]
    assert repaid_data["status"] == LoanStatus.REPAID.value
    assert repaid_data["repaid_amount"] == loan_to_repay["amount"]
