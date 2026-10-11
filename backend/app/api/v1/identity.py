from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from ...models.did import (
    SpendAuthorityCredential,
    IssueCredentialRequest,
    VerifyCredentialRequest,
    VerificationResult,
)
from ...services.did_service import did_service

router = APIRouter(prefix="/identity", tags=["W3C DID & Decentralized Agent Identity"])


class RevokeRequest(BaseModel):
    reason: Optional[str] = "Manual killswitch triggered by Supervisor"


@router.get("/credentials", response_model=List[SpendAuthorityCredential])
async def list_credentials():
    return did_service.list_credentials()


@router.get("/credentials/{credential_id}", response_model=SpendAuthorityCredential)
async def get_credential(credential_id: str):
    cred = did_service.get_credential(credential_id)
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    return cred


@router.post("/issue", response_model=SpendAuthorityCredential)
async def issue_credential(request: IssueCredentialRequest):
    return did_service.issue_credential(request)


@router.post("/verify", response_model=VerificationResult)
async def verify_credential(request: VerifyCredentialRequest):
    return did_service.verify_credential(request.credential_id)


@router.post("/revoke/{credential_id}", response_model=SpendAuthorityCredential)
async def revoke_credential(credential_id: str, request: Optional[RevokeRequest] = None):
    reason = request.reason if request else "Killswitch triggered"
    cred = did_service.revoke_credential(credential_id, reason=reason)
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    return cred
