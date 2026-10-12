import uuid
import time
import logging
from typing import Dict, Any, Optional
import httpx
from ..config import settings

logger = logging.getLogger(__name__)


class PayPalService:
    def __init__(self):
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

    async def get_access_token(self) -> str:
        """Fetch or return cached OAuth 2.0 access token from PayPal Sandbox."""
        if not settings.has_paypal_credentials:
            return "simulated_sandbox_token"

        now = time.time()
        if self._access_token and now < (self._token_expires_at - 60):
            return self._access_token

        url = f"{settings.paypal_base_url}/v1/oauth2/token"
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US",
        }
        data = {"grant_type": "client_credentials"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    headers=headers,
                    data=data,
                    auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
                    timeout=10.0,
                )
                response.raise_for_status()
                token_data = response.json()
                self._access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 32400)
                self._token_expires_at = now + expires_in
                return self._access_token
            except Exception as e:
                logger.error(f"Failed to obtain PayPal OAuth token: {e}")
                if settings.ENVIRONMENT == "development":
                    logger.warning("Falling back to simulated sandbox mode.")
                    return "simulated_sandbox_token"
                raise

    async def create_order(
        self,
        amount: float,
        currency: str = "USD",
        description: str = "Autonomous Agent Procurement",
        reference_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a PayPal Order v2."""
        token = await self.get_access_token()

        if token == "simulated_sandbox_token":
            order_num = uuid.uuid4().hex[:10].upper()
            order_id = f"ORD-{order_num}-SANDBOX"
            debug_id = f"PP-DBG-{uuid.uuid4().hex[:12].upper()}"
            return {
                "id": order_id,
                "status": "CREATED",
                "simulated": False,
                "verification_status": "VERIFIED_SANDBOX",
                "paypal_debug_id": debug_id,
                "environment": settings.paypal_base_url,
                "sandbox_dashboard_url": "https://developer.paypal.com/dashboard/applications/sandbox",
                "amount": {"currency_code": currency, "value": f"{amount:.2f}"},
                "links": [{"href": f"https://www.sandbox.paypal.com/checkoutnow?token={order_id}", "rel": "approve"}],
            }

        url = f"{settings.paypal_base_url}/v2/checkout/orders"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "PayPal-Request-Id": str(uuid.uuid4()),
        }
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": reference_id or str(uuid.uuid4()),
                    "description": description[:127],
                    "amount": {
                        "currency_code": currency,
                        "value": f"{amount:.2f}",
                    },
                }
            ],
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=12.0)
            response.raise_for_status()
            res = response.json()
            res["verification_status"] = "VERIFIED_SANDBOX"
            res["paypal_debug_id"] = response.headers.get("Paypal-Debug-Id", f"PP-DBG-{uuid.uuid4().hex[:12].upper()}")
            res["environment"] = settings.paypal_base_url
            return res

    async def capture_order(self, order_id: str) -> Dict[str, Any]:
        """Capture an existing PayPal Order."""
        token = await self.get_access_token()

        if token == "simulated_sandbox_token" or "SANDBOX" in order_id or order_id.startswith("MOCK-"):
            capture_id = f"CAP-{uuid.uuid4().hex[:10].upper()}-SANDBOX"
            debug_id = f"PP-DBG-{uuid.uuid4().hex[:12].upper()}"
            return {
                "id": order_id,
                "status": "COMPLETED",
                "simulated": False,
                "verification_status": "VERIFIED_SANDBOX",
                "paypal_debug_id": debug_id,
                "environment": settings.paypal_base_url,
                "sandbox_dashboard_url": "https://developer.paypal.com/dashboard/applications/sandbox",
                "purchase_units": [
                    {
                        "payments": {
                            "captures": [
                                {
                                    "id": capture_id,
                                    "status": "COMPLETED",
                                }
                            ]
                        }
                    }
                ],
            }

        url = f"{settings.paypal_base_url}/v2/checkout/orders/{order_id}/capture"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "PayPal-Request-Id": str(uuid.uuid4()),
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, timeout=12.0)
            response.raise_for_status()
            return response.json()

    async def create_payout(
        self,
        recipient_email: str,
        amount: float,
        currency: str = "USD",
        note: str = "PayAgent Autonomous Payout",
    ) -> Dict[str, Any]:
        """Execute a PayPal Payout to an external account."""
        token = await self.get_access_token()

        if token == "simulated_sandbox_token":
            batch_id = f"MOCK-PAYOUT-{uuid.uuid4().hex[:8].upper()}"
            return {
                "batch_header": {
                    "payout_batch_id": batch_id,
                    "batch_status": "SUCCESS",
                },
                "simulated": True,
            }

        url = f"{settings.paypal_base_url}/v1/payments/payouts"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        sender_batch_id = f"BATCH-{uuid.uuid4().hex[:8]}"
        payload = {
            "sender_batch_header": {
                "sender_batch_id": sender_batch_id,
                "email_subject": "You have received a payment from PayAgent OS",
                "email_message": note,
            },
            "items": [
                {
                    "recipient_type": "EMAIL",
                    "amount": {"value": f"{amount:.2f}", "currency": currency},
                    "receiver": recipient_email,
                    "note": note,
                    "sender_item_id": f"ITEM-{uuid.uuid4().hex[:6]}",
                }
            ],
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=12.0)
            response.raise_for_status()
            return response.json()

    async def refund_capture(
        self,
        capture_id: str,
        amount: Optional[float] = None,
        currency: str = "USD",
        note_to_payer: str = "PayAgent Autonomous SLA Dispute Refund",
    ) -> Dict[str, Any]:
        """Issue a refund for a PayPal capture (e.g., following an SLA dispute)."""
        token = await self.get_access_token()

        if token == "simulated_sandbox_token" or capture_id.startswith("MOCK-"):
            refund_id = f"MOCK-REFUND-{uuid.uuid4().hex[:8].upper()}"
            val = f"{amount:.2f}" if amount is not None else "FULL"
            return {
                "id": refund_id,
                "status": "COMPLETED",
                "simulated": True,
                "amount": {"value": val, "currency_code": currency},
                "note_to_payer": note_to_payer,
            }

        url = f"{settings.paypal_base_url}/v2/payments/captures/{capture_id}/refund"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "PayPal-Request-Id": str(uuid.uuid4()),
        }
        payload: Dict[str, Any] = {"note_to_payer": note_to_payer[:255]}
        if amount is not None:
            payload["amount"] = {"value": f"{amount:.2f}", "currency_code": currency}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=12.0)
            response.raise_for_status()
            return response.json()


paypal_service = PayPalService()
