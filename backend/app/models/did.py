from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class CredentialStatus(str, Enum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class AgentDIDDocument(BaseModel):
    did: str
    controller: str
    public_key_hex: str
    created_at: str


class SpendAuthorityCredential(BaseModel):
    credential_id: str
    issuer_did: str = "did:payagent:cfo-elena"
    issuer_name: str = "Elena Rostova (CFO)"
    subject_did: str
    agent_id: str
    agent_name: str
    max_single_spend: float
    daily_spend_cap: float
    allowed_categories: List[str] = Field(default_factory=list)
    valid_from: str
    valid_until: str
    proof_type: str = "Ed25519Signature2020"
    proof_signature: str
    status: CredentialStatus = CredentialStatus.ACTIVE
    revoked_reason: Optional[str] = None


class IssueCredentialRequest(BaseModel):
    agent_id: str
    max_single_spend: float = 150.00
    daily_spend_cap: float = 500.00
    allowed_categories: List[str] = Field(default_factory=lambda: ["CLOUD_COMPUTE", "API_QUOTA"])
    valid_days: int = 90


class VerifyCredentialRequest(BaseModel):
    credential_id: str


class VerificationResult(BaseModel):
    is_valid: bool
    status: CredentialStatus
    subject_did: str
    agent_id: str
    proof_verified: bool
    reason: str
    verified_at: str
    credential: Optional[SpendAuthorityCredential] = None
