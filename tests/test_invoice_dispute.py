import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.models.dispute import DisputeStrategy


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_list_and_get_dispute_history():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/disputes/history")
        assert res.status_code == 200
        history = res.json()
        assert len(history) >= 1

        sample = history[0]
        assert "Datadog" in sample["vendor_name"]
        assert sample["original_amount"] == 240.00
        assert sample["saved_amount"] > 0
        assert sample["status"] == "SETTLED"
        assert len(sample["rounds"]) >= 2

        # Get single dispute
        single_res = await ac.get(f"/api/v1/disputes/{sample['dispute_id']}")
        assert single_res.status_code == 200
        assert single_res.json()["dispute_id"] == sample["dispute_id"]


@pytest.mark.asyncio
async def test_negotiate_volume_commitment():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "vendor_name": "OpenAI API Platform",
            "invoice_ref": "INV-OAI-3301",
            "original_amount": 500.00,
            "strategy": "VOLUME_COMMITMENT",
            "target_discount_percent": 20.0,
        }
        res = await ac.post("/api/v1/disputes/negotiate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["vendor_name"] == "OpenAI API Platform"
        assert data["original_amount"] == 500.00
        assert data["agreed_amount"] < 500.00
        assert data["saved_amount"] > 0
        assert data["status"] == "SETTLED"
        assert len(data["rounds"]) == 3
        assert "PP-SETTLED-" in data["paypal_settlement_id"]


@pytest.mark.asyncio
async def test_negotiate_sla_downtime_credit():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "vendor_name": "AWS CloudWatch & Logs",
            "invoice_ref": "INV-AWS-7741",
            "original_amount": 350.00,
            "strategy": "SLA_DOWNTIME_CREDIT",
            "target_discount_percent": 15.0,
        }
        res = await ac.post("/api/v1/disputes/negotiate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["strategy"] == "SLA_DOWNTIME_CREDIT"
        assert data["agreed_amount"] < 350.00
        assert "99.3% availability" in data["rounds"][0]["message"]
