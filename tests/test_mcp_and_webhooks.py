import json
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.mcp import MCPJsonRpcRequest
from backend.app.models.webhook import PayPalWebhookEvent
from backend.app.services.mcp_server import mcp_server
from backend.app.services.webhook_service import paypal_webhook_service


@pytest.fixture
def client():
    return TestClient(app)


# 1. MCP Tools & JSON-RPC Tests
def test_mcp_tools_manifest():
    tools = mcp_server.get_tools()
    assert len(tools) >= 5
    names = [t.name for t in tools]
    assert "payagent_request_funds" in names
    assert "payagent_check_budget" in names
    assert "payagent_get_policy" in names
    assert "payagent_list_agents" in names
    assert "payagent_scan_risk" in names


@pytest.mark.asyncio
async def test_mcp_call_check_budget():
    res = await mcp_server.call_tool("payagent_check_budget", {"agent_id": "agent-devops"})
    assert res.isError is False
    assert len(res.content) == 1
    data = json.loads(res.content[0].text)
    assert data["agent_id"] == "agent-devops"
    assert "wallet_balance" in data
    assert "remaining_daily_headroom" in data


@pytest.mark.asyncio
async def test_mcp_call_request_funds_autonomous():
    res = await mcp_server.call_tool(
        "payagent_request_funds",
        {
            "agent_id": "agent-devops",
            "amount": 15.0,
            "currency": "USD",
            "recipient": "AWS",
            "reasoning": "Deploying ephemeral test cluster via MCP",
        },
    )
    assert res.isError is False
    data = json.loads(res.content[0].text)
    assert data["status"] in ["APPROVED_AUTONOMOUS", "SETTLED"]
    assert "transaction_id" in data


@pytest.mark.asyncio
async def test_mcp_call_request_funds_exceeds_limit():
    res = await mcp_server.call_tool(
        "payagent_request_funds",
        {
            "agent_id": "agent-devops",
            "amount": 250.0,
            "currency": "USD",
            "recipient": "RunPod",
            "reasoning": "Massive GPU fine-tuning run",
        },
    )
    assert res.isError is False
    data = json.loads(res.content[0].text)
    assert data["status"] == "PENDING_APPROVAL"


@pytest.mark.asyncio
async def test_mcp_json_rpc_handler():
    req = MCPJsonRpcRequest(
        id=101,
        method="tools/call",
        params={
            "name": "payagent_get_policy",
            "arguments": {"agent_id": "agent-devops"},
        },
    )
    resp = await mcp_server.handle_jsonrpc(req)
    assert resp.id == 101
    assert resp.error is None
    assert resp.result is not None


# 2. PayPal Webhooks & Cryptographic Signature Verification Tests
@pytest.mark.asyncio
async def test_webhook_signature_verification_valid():
    is_valid = paypal_webhook_service.verify_signature(
        transmission_id="WH-TX-12345",
        transmission_time="2026-10-10T12:00:00Z",
        cert_url="https://api.sandbox.paypal.com/v1/notifications/certs/CERT-SANDBOX",
        auth_algo="SHA256withRSA",
        transmission_sig="VALID_SIGNATURE_HASH_XYZ",
        raw_body='{"event_type": "PAYMENT.CAPTURE.COMPLETED"}',
    )
    assert is_valid is True


@pytest.mark.asyncio
async def test_webhook_untrusted_cert_url():
    is_untrusted = paypal_webhook_service.verify_signature(
        transmission_id="WH-TX-FAKE",
        transmission_time="2026-10-10T12:00:00Z",
        cert_url="https://malicious-site.com/fake-cert",
        auth_algo="SHA256withRSA",
        transmission_sig="FAKE_SIG",
        raw_body="{}",
    )
    assert is_untrusted is False


@pytest.mark.asyncio
async def test_webhook_capture_completed_processing():
    event = PayPalWebhookEvent(
        id="WH-EVENT-998877",
        create_time="2026-10-10T12:00:00Z",
        event_type="PAYMENT.CAPTURE.COMPLETED",
        summary="Payment capture completed for order MOCK-ORD-123",
        resource={"id": "MOCK-CAP-123", "status": "COMPLETED"},
    )
    resp = await paypal_webhook_service.process_webhook_event(
        event=event,
        transmission_id="WH-TX-998877",
        is_verified=True,
    )
    assert resp.verification_status == "SUCCESS"
    assert resp.is_verified is True
    assert resp.event_type == "PAYMENT.CAPTURE.COMPLETED"


# 3. REST API Endpoint Tests
def test_api_mcp_and_webhooks_endpoints(client):
    # MCP tools list
    resp = client.get("/api/v1/mcp/tools")
    assert resp.status_code == 200
    assert len(resp.json()) >= 5

    # MCP tool call
    resp_call = client.post(
        "/api/v1/mcp/tools/call",
        json={"name": "payagent_list_agents", "arguments": {}},
    )
    assert resp_call.status_code == 200
    assert resp_call.json()["isError"] is False

    # PayPal Webhook POST
    wh_payload = {
        "id": "WH-TEST-INT-01",
        "create_time": "2026-10-10T12:00:00Z",
        "event_type": "CHECKOUT.ORDER.APPROVED",
        "summary": "Order approved by buyer",
        "resource": {"id": "MOCK-ORD-APPROVED-01"},
    }
    resp_wh = client.post(
        "/api/v1/webhooks/paypal",
        json=wh_payload,
        headers={
            "PAYPAL-TRANSMISSION-ID": "WH-TX-INT-01",
            "PAYPAL-TRANSMISSION-TIME": "2026-10-10T12:00:00Z",
            "PAYPAL-CERT-URL": "https://api.sandbox.paypal.com/v1/notifications/certs/CERT-SANDBOX",
            "PAYPAL-AUTH-ALGO": "SHA256withRSA",
            "PAYPAL-TRANSMISSION-SIG": "TEST-SIG-INT-01",
        },
    )
    assert resp_wh.status_code == 200
    assert resp_wh.json()["verification_status"] == "SUCCESS"
