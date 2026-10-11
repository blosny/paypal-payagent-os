import uuid
import hashlib
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
from ..models.did import (
    CredentialStatus,
    AgentDIDDocument,
    SpendAuthorityCredential,
    IssueCredentialRequest,
    VerificationResult,
)


class DIDIdentityService:
    """Manages W3C Decentralized Identifiers (DIDs) & Verifiable Spend Authority Credentials for AI fleet."""

    MASTER_ISSUER_DID = "did:payagent:cfo-elena"
    MASTER_ISSUER_NAME = "Elena Rostova (CFO)"

    def __init__(self):
        self._did_documents: Dict[str, AgentDIDDocument] = {}
        self._credentials: Dict[str, SpendAuthorityCredential] = {}
        self._init_mock_identities()

    def _generate_signature(self, payload: str) -> str:
        """Simulates a cryptographic Ed25519 / SHA-256 digital signature."""
        secret_salt = "payagent-cfo-authority-ed25519-secret-salt-2026"
        return "ed25519_" + hashlib.sha256(f"{payload}_{secret_salt}".encode("utf-8")).hexdigest()

    def _init_mock_identities(self):
        now = datetime.now(timezone.utc)
        valid_until = (now + timedelta(days=90)).isoformat()
        now_iso = now.isoformat()

        initial_fleet = [
            {
                "id": "agent-devops",
                "name": "DevOps Infrastructure Agent",
                "max_single": 250.00,
                "daily_cap": 800.00,
                "categories": ["CLOUD_COMPUTE", "SERVERLESS", "CI_CD"],
            },
            {
                "id": "agent-research",
                "name": "Research & AI Model Agent",
                "max_single": 150.00,
                "daily_cap": 350.00,
                "categories": ["API_QUOTA", "DATASET_ACCESS"],
            },
            {
                "id": "agent-contractor",
                "name": "Contractor & Freelancer Agent",
                "max_single": 80.00,
                "daily_cap": 180.00,
                "categories": ["FREELANCE_PAYOUT"],
            },
        ]

        for item in initial_fleet:
            agent_id = item["id"]
            agent_did = f"did:payagent:{agent_id}:{uuid.uuid4().hex[:8]}"
            pubkey = hashlib.sha256(f"pubkey_{agent_id}".encode("utf-8")).hexdigest()

            doc = AgentDIDDocument(
                did=agent_did,
                controller=self.MASTER_ISSUER_DID,
                public_key_hex=pubkey,
                created_at=now_iso,
            )
            self._did_documents[agent_id] = doc

            cred_id = f"vc_spend_{uuid.uuid4().hex[:10]}"
            raw_payload = f"{self.MASTER_ISSUER_DID}|{agent_did}|{item['max_single']}|{item['daily_cap']}|{valid_until}"
            sig = self._generate_signature(raw_payload)

            cred = SpendAuthorityCredential(
                credential_id=cred_id,
                issuer_did=self.MASTER_ISSUER_DID,
                issuer_name=self.MASTER_ISSUER_NAME,
                subject_did=agent_did,
                agent_id=agent_id,
                agent_name=item["name"],
                max_single_spend=item["max_single"],
                daily_spend_cap=item["daily_cap"],
                allowed_categories=item["categories"],
                valid_from=now_iso,
                valid_until=valid_until,
                proof_type="Ed25519Signature2020",
                proof_signature=sig,
                status=CredentialStatus.ACTIVE,
            )
            self._credentials[cred_id] = cred

    def list_credentials(self) -> List[SpendAuthorityCredential]:
        return list(self._credentials.values())

    def get_credential(self, credential_id: str) -> Optional[SpendAuthorityCredential]:
        return self._credentials.get(credential_id)

    def get_active_credential_for_agent(self, agent_id: str) -> Optional[SpendAuthorityCredential]:
        for c in self._credentials.values():
            if c.agent_id == agent_id and c.status == CredentialStatus.ACTIVE:
                return c
        return None

    def issue_credential(self, request: IssueCredentialRequest) -> SpendAuthorityCredential:
        agent_id = request.agent_id
        doc = self._did_documents.get(agent_id)
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        if not doc:
            agent_did = f"did:payagent:{agent_id}:{uuid.uuid4().hex[:8]}"
            doc = AgentDIDDocument(
                did=agent_did,
                controller=self.MASTER_ISSUER_DID,
                public_key_hex=hashlib.sha256(f"pubkey_{agent_id}".encode("utf-8")).hexdigest(),
                created_at=now_iso,
            )
            self._did_documents[agent_id] = doc

        # Revoke any older active credential for this agent
        for existing in self._credentials.values():
            if existing.agent_id == agent_id and existing.status == CredentialStatus.ACTIVE:
                existing.status = CredentialStatus.REVOKED
                existing.revoked_reason = "Superseded by new issuance"

        valid_until = (now + timedelta(days=request.valid_days)).isoformat()
        cred_id = f"vc_spend_{uuid.uuid4().hex[:10]}"
        raw_payload = f"{self.MASTER_ISSUER_DID}|{doc.did}|{request.max_single_spend}|{request.daily_spend_cap}|{valid_until}"
        sig = self._generate_signature(raw_payload)

        agent_clean_name = agent_id.replace("agent-", "").capitalize() + " Agent"
        cred = SpendAuthorityCredential(
            credential_id=cred_id,
            issuer_did=self.MASTER_ISSUER_DID,
            issuer_name=self.MASTER_ISSUER_NAME,
            subject_did=doc.did,
            agent_id=agent_id,
            agent_name=agent_clean_name,
            max_single_spend=request.max_single_spend,
            daily_spend_cap=request.daily_spend_cap,
            allowed_categories=request.allowed_categories,
            valid_from=now_iso,
            valid_until=valid_until,
            proof_type="Ed25519Signature2020",
            proof_signature=sig,
            status=CredentialStatus.ACTIVE,
        )
        self._credentials[cred_id] = cred
        return cred

    def verify_credential(self, credential_id: str) -> VerificationResult:
        cred = self._credentials.get(credential_id)
        now_iso = datetime.now(timezone.utc).isoformat()

        if not cred:
            return VerificationResult(
                is_valid=False,
                status=CredentialStatus.EXPIRED,
                subject_did="unknown",
                agent_id="unknown",
                proof_verified=False,
                reason="Credential not found in registry",
                verified_at=now_iso,
            )

        # Check status
        if cred.status == CredentialStatus.REVOKED:
            return VerificationResult(
                is_valid=False,
                status=CredentialStatus.REVOKED,
                subject_did=cred.subject_did,
                agent_id=cred.agent_id,
                proof_verified=True,
                reason=f"Credential was revoked by supervisor: {cred.revoked_reason or 'No reason provided'}",
                verified_at=now_iso,
                credential=cred,
            )

        # Check expiration
        now = datetime.now(timezone.utc)
        exp = datetime.fromisoformat(cred.valid_until.replace("Z", "+00:00"))
        if now > exp:
            cred.status = CredentialStatus.EXPIRED
            return VerificationResult(
                is_valid=False,
                status=CredentialStatus.EXPIRED,
                subject_did=cred.subject_did,
                agent_id=cred.agent_id,
                proof_verified=True,
                reason="Credential expiration TTL elapsed",
                verified_at=now_iso,
                credential=cred,
            )

        # Re-compute cryptographic proof
        raw_payload = f"{cred.issuer_did}|{cred.subject_did}|{cred.max_single_spend}|{cred.daily_spend_cap}|{cred.valid_until}"
        expected_sig = self._generate_signature(raw_payload)

        if expected_sig != cred.proof_signature:
            return VerificationResult(
                is_valid=False,
                status=CredentialStatus.ACTIVE,
                subject_did=cred.subject_did,
                agent_id=cred.agent_id,
                proof_verified=False,
                reason="Cryptographic signature mismatch! Possible credential tampering detected.",
                verified_at=now_iso,
                credential=cred,
            )

        return VerificationResult(
            is_valid=True,
            status=CredentialStatus.ACTIVE,
            subject_did=cred.subject_did,
            agent_id=cred.agent_id,
            proof_verified=True,
            reason="Cryptographic signature verified. Authorized by CFO Elena Rostova.",
            verified_at=now_iso,
            credential=cred,
        )

    def revoke_credential(self, credential_id: str, reason: str = "Killswitch triggered by Supervisor") -> Optional[SpendAuthorityCredential]:
        cred = self._credentials.get(credential_id)
        if not cred:
            return None
        cred.status = CredentialStatus.REVOKED
        cred.revoked_reason = reason
        return cred


did_service = DIDIdentityService()
