from typing import List
from fastapi import APIRouter, HTTPException
from ...models.dispute import (
    InvoiceDisputeRecord,
    DisputeInitiateRequest,
)
from ...services.dispute_service import dispute_service

router = APIRouter(prefix="/disputes", tags=["Autonomous Invoice Dispute & Negotiation"])


@router.get("/history", response_model=List[InvoiceDisputeRecord])
async def list_dispute_history():
    return dispute_service.list_disputes()


@router.get("/{dispute_id}", response_model=InvoiceDisputeRecord)
async def get_dispute(dispute_id: str):
    record = dispute_service.get_dispute(dispute_id)
    if not record:
        raise HTTPException(status_code=404, detail="Dispute record not found")
    return record


@router.post("/negotiate", response_model=InvoiceDisputeRecord)
async def initiate_negotiation(request: DisputeInitiateRequest):
    return dispute_service.initiate_negotiation(request)
