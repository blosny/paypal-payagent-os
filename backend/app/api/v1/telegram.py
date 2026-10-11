from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter
from ...models.telegram import TelegramSettings, TelegramAlertNotification
from ...services.telegram_service import telegram_service

router = APIRouter(prefix="/telegram", tags=["Telegram Supervisor Alerts"])


class TestAlertRequest(BaseModel):
    message: Optional[str] = "🔔 Test ping from PayAgent OS Finance Command Center."


@router.get("/settings", response_model=TelegramSettings)
async def get_settings():
    return telegram_service.get_settings()


@router.post("/settings", response_model=TelegramSettings)
async def update_settings(settings: TelegramSettings):
    return telegram_service.update_settings(settings)


@router.get("/alerts", response_model=List[TelegramAlertNotification])
async def list_alerts(limit: int = 20):
    return telegram_service.list_history(limit=limit)


@router.post("/test-alert", response_model=Optional[TelegramAlertNotification])
async def send_test_alert(req: TestAlertRequest):
    return telegram_service.send_alert(
        event_type="HITL_PENDING",
        title="🔔 Supervisor Test Ping",
        message=req.message or "Test alert",
    )
