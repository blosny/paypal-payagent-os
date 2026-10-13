import pytest
from backend.app.services.paypal_service import PayPalService
from backend.app.config import settings


@pytest.fixture
def service():
    return PayPalService()


@pytest.mark.asyncio
async def test_paypal_access_token_simulated(service):
    token = await service.get_access_token()
    assert token is not None
    assert isinstance(token, str)


@pytest.mark.asyncio
async def test_paypal_create_order_structure(service):
    res = await service.create_order(
        amount=25.50,
        currency="USD",
        description="Autonomous GPU compute slice",
        reference_id="TX-REF-TEST-001",
    )
    assert "id" in res
    assert res["status"] == "CREATED"
    assert res["verification_status"] == "VERIFIED_SANDBOX"
    assert "paypal_debug_id" in res
    assert res["paypal_debug_id"].startswith("PP-DBG-")
    assert "environment" in res
    assert "sandbox_dashboard_url" in res
    assert res["amount"]["value"] == "25.50"
    assert res["amount"]["currency_code"] == "USD"
    assert len(res["links"]) > 0


@pytest.mark.asyncio
async def test_paypal_capture_order_structure(service):
    # First create an order
    order = await service.create_order(amount=18.00, currency="USD")
    order_id = order["id"]

    # Capture it
    capture = await service.capture_order(order_id)
    assert capture["id"] == order_id
    assert capture["status"] == "COMPLETED"
    assert capture["verification_status"] == "VERIFIED_SANDBOX"
    assert "paypal_debug_id" in capture
    assert len(capture["purchase_units"]) > 0
    captures_list = capture["purchase_units"][0]["payments"]["captures"]
    assert len(captures_list) > 0
    assert captures_list[0]["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_paypal_create_payout_structure(service):
    payout = await service.create_payout(
        recipient_email="freelance.dev@paypal.com",
        amount=50.00,
        currency="USD",
        note="Smart contract audit reward",
    )
    assert "batch_header" in payout
    assert payout["batch_header"]["batch_status"] == "SUCCESS"
    assert payout["batch_header"]["payout_batch_id"].startswith("MOCK-PAYOUT-") or "BATCH" in payout["batch_header"]["payout_batch_id"]


@pytest.mark.asyncio
async def test_paypal_order_custom_currency(service):
    res = await service.create_order(
        amount=100.00,
        currency="EUR",
        description="European Cloud Provider Node",
    )
    assert res["amount"]["currency_code"] == "EUR"
    assert res["amount"]["value"] == "100.00"
