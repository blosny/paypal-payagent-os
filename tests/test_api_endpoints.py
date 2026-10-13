import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.policy_engine import policy_engine
from backend.app.models.transaction import TransactionStatus

client = TestClient(app)


def test_health_check_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "mode" in data
    assert "paypal_connected" in data


def test_list_agents_endpoint():
    res = client.get("/api/v1/agents")
    assert res.status_code == 200
    agents = res.json()
    assert isinstance(agents, list)
    assert len(agents) >= 3
    ids = [a["id"] for a in agents]
    assert "agent-devops" in ids
    assert "agent-research" in ids
    assert "agent-payout" in ids


def test_get_agent_success():
    res = client.get("/api/v1/agents/agent-devops")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "agent-devops"
    assert data["name"] == "DevOps Infrastructure Agent"
    assert "policy" in data
    assert data["policy"]["max_per_transaction"] == 40.0


def test_get_agent_not_found():
    res = client.get("/api/v1/agents/non-existent-agent-id")
    assert res.status_code == 404
    assert res.json()["detail"] == "Agent not found"


def test_create_custom_agent():
    payload = {
        "name": "Security Audit Bot",
        "description": "Performs external penetration and vulnerability testing",
        "wallet_balance": 500.0,
        "currency": "USD",
        "personality": "FRUGAL_VAULT",
        "personality_description": "Strict Security Auditor",
        "policy": {
            "max_per_transaction": 30.0,
            "daily_budget": 120.0,
            "allowed_vendors": ["Snyk", "HackerOne"],
            "allow_unlisted_vendors": False,
            "auto_approval_enabled": True,
        },
    }
    res = client.post("/api/v1/agents", json=payload)
    assert res.status_code == 201
    created = res.json()
    assert created["id"].startswith("agent-")
    assert created["name"] == "Security Audit Bot"
    assert created["wallet_balance"] == 500.0

    # Verify retrieval
    res_get = client.get(f"/api/v1/agents/{created['id']}")
    assert res_get.status_code == 200
    assert res_get.json()["name"] == "Security Audit Bot"


def test_patch_agent_wallet():
    # Update balance of agent-research
    original = policy_engine.get_agent("agent-research").wallet_balance
    res = client.patch(
        "/api/v1/agents/agent-research",
        json={"wallet_balance": original + 100.0, "name": "Updated Research Agent"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["wallet_balance"] == original + 100.0
    assert data["name"] == "Updated Research Agent"


def test_submit_payment_intent_autonomous_success():
    payload = {
        "agent_id": "agent-devops",
        "amount": 12.50,
        "currency": "USD",
        "recipient": "AWS",
        "category": "CLOUD_COMPUTE",
        "reasoning": "Deploying ephemeral worker instance for pipeline build",
    }
    res = client.post("/api/v1/payments/intent", json=payload)
    assert res.status_code == 200
    tx = res.json()
    assert tx["status"] == "APPROVED_AUTONOMOUS"
    assert tx["amount"] == 12.50
    assert tx["verification_status"] == "VERIFIED_SANDBOX"
    assert tx["paypal_order_id"] is not None
    assert tx["paypal_capture_id"] is not None
    assert "PP-DBG-" in tx["paypal_debug_id"]


def test_submit_payment_intent_hitl_limit_exceeded():
    payload = {
        "agent_id": "agent-devops",
        "amount": 95.00,  # Single tx limit is 40.0
        "currency": "USD",
        "recipient": "AWS",
        "category": "CLOUD_COMPUTE",
        "reasoning": "Reserving on-demand GPU cluster for deep training",
    }
    res = client.post("/api/v1/payments/intent", json=payload)
    assert res.status_code == 200
    tx = res.json()
    assert tx["status"] == "PENDING_APPROVAL"
    assert tx["amount"] == 95.00
    assert "exceeds single transaction limit" in tx["policy_evaluation_reason"]


def test_submit_payment_intent_freelancer_payout():
    payload = {
        "agent_id": "agent-payout",
        "amount": 35.00,
        "currency": "USD",
        "recipient": "contributor.alex@paypal.com",
        "category": "FREELANCE_PAYOUT",
        "reasoning": "Micro-bounty milestone disbursement for bug triage",
    }
    res = client.post("/api/v1/payments/intent", json=payload)
    assert res.status_code == 200
    tx = res.json()
    assert tx["status"] == "APPROVED_AUTONOMOUS"
    assert tx["transaction_type"] == "PAYPAL_PAYOUT"
    assert tx["paypal_payout_batch_id"] is not None
    assert tx["verification_status"] == "VERIFIED_SANDBOX"


def test_submit_payment_intent_invalid_agent():
    payload = {
        "agent_id": "unknown-ghost-agent",
        "amount": 10.00,
        "currency": "USD",
        "recipient": "AWS",
        "category": "CLOUD_COMPUTE",
        "reasoning": "Should fail with 400",
    }
    res = client.post("/api/v1/payments/intent", json=payload)
    assert res.status_code == 400
    assert "not found" in res.json()["detail"].lower()


def test_resolve_transaction_hitl_approve_and_reject():
    # 1. Create a pending transaction
    intent_payload = {
        "agent_id": "agent-devops",
        "amount": 80.00,
        "currency": "USD",
        "recipient": "Cloudflare",
        "category": "CLOUD_COMPUTE",
        "reasoning": "Enterprise DDoS rule tier upgrade",
    }
    res = client.post("/api/v1/payments/intent", json=intent_payload)
    tx = res.json()
    assert tx["status"] == "PENDING_APPROVAL"
    tx_id = tx["id"]

    # 2. Approve via HITL resolution
    approve_payload = {
        "decision": "APPROVE",
        "reviewer_notes": "Authorized by CFO Elena - high-priority mitigation",
    }
    res_resolve = client.post(f"/api/v1/payments/{tx_id}/resolve", json=approve_payload)
    assert res_resolve.status_code == 200
    resolved_tx = res_resolve.json()
    assert resolved_tx["status"] == "APPROVED_BY_HUMAN"
    assert resolved_tx["paypal_order_id"] is not None
    assert resolved_tx["verification_status"] == "VERIFIED_SANDBOX"

    # 3. Create another pending transaction and reject it
    intent_payload2 = {
        "agent_id": "agent-devops",
        "amount": 85.00,
        "currency": "USD",
        "recipient": "Cloudflare",
        "category": "CLOUD_COMPUTE",
        "reasoning": "Unnecessary auxiliary add-on",
    }
    res2 = client.post("/api/v1/payments/intent", json=intent_payload2)
    tx2 = res2.json()
    assert tx2["status"] == "PENDING_APPROVAL"

    reject_payload = {
        "decision": "REJECT",
        "reviewer_notes": "Rejected: Cost exceeds current operational necessity",
    }
    res_reject = client.post(f"/api/v1/payments/{tx2['id']}/resolve", json=reject_payload)
    assert res_reject.status_code == 200
    assert res_reject.json()["status"] == "REJECTED_BY_HUMAN"
    assert res_reject.json()["reviewer_notes"] == "Rejected: Cost exceeds current operational necessity"


def test_get_transaction_by_id_and_404():
    # 404 test
    res = client.get("/api/v1/payments/TX-NONEXISTENT")
    assert res.status_code == 404
    assert res.json()["detail"] == "Transaction not found"


def test_vault_endpoints():
    # List subscriptions
    res = client.get("/api/v1/vault/subscriptions")
    assert res.status_code == 200
    subs = res.json()
    assert len(subs) >= 3

    # Scan inactivity
    res_scan = client.post("/api/v1/vault/scan")
    assert res_scan.status_code == 200
    scan_data = res_scan.json()
    assert "total_subscriptions" in scan_data
    assert "potential_monthly_savings" in scan_data

    # Cancel a subscription
    res_cancel = client.post(
        "/api/v1/vault/cancel",
        json={"subscription_id": "sub_notion_01", "reason": "Idle seat audit"},
    )
    assert res_cancel.status_code == 200
    assert res_cancel.json()["status"] == "CANCELED"
    assert res_cancel.json()["savings_on_cancel"] == 49.00


def test_telegram_endpoints():
    res = client.get("/api/v1/telegram/settings")
    assert res.status_code == 200
    assert "connected_account" in res.json()

    res_test = client.post(
        "/api/v1/telegram/test-alert",
        json={"message": "Automated pytest verification ping"},
    )
    assert res_test.status_code == 200
    alert = res_test.json()
    assert alert["event_type"] == "HITL_PENDING"
    assert alert["delivered"] is True
