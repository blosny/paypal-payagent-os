import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.services.did_service import did_service


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_list_and_get_did_credentials():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/identity/credentials")
        assert res.status_code == 200
        creds = res.json()
        assert len(creds) >= 3

        devops_cred = next(c for c in creds if c["agent_id"] == "agent-devops")
        assert "did:payagent:agent-devops" in devops_cred["subject_did"]
        assert devops_cred["issuer_did"] == "did:payagent:cfo-elena"
        assert devops_cred["proof_type"] == "Ed25519Signature2020"
        assert devops_cred["status"] == "ACTIVE"

        # Get single credential
        single_res = await ac.get(f"/api/v1/identity/credentials/{devops_cred['credential_id']}")
        assert single_res.status_code == 200
        assert single_res.json()["agent_id"] == "agent-devops"


@pytest.mark.asyncio
async def test_verify_active_credential():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        creds_res = await ac.get("/api/v1/identity/credentials")
        first_cred_id = creds_res.json()[0]["credential_id"]

        verify_res = await ac.post("/api/v1/identity/verify", json={"credential_id": first_cred_id})
        assert verify_res.status_code == 200
        data = verify_res.json()
        assert data["is_valid"] is True
        assert data["proof_verified"] is True
        assert data["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_issue_new_credential_and_supersede():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "agent_id": "agent-devops",
            "max_single_spend": 300.00,
            "daily_spend_cap": 950.00,
            "allowed_categories": ["CLOUD_COMPUTE", "GPU_SPOT"],
            "valid_days": 60,
        }
        issue_res = await ac.post("/api/v1/identity/issue", json=payload)
        assert issue_res.status_code == 200
        new_cred = issue_res.json()
        assert new_cred["max_single_spend"] == 300.00
        assert new_cred["daily_spend_cap"] == 950.00
        assert new_cred["status"] == "ACTIVE"

        # Verify new credential is valid
        verify_res = await ac.post("/api/v1/identity/verify", json={"credential_id": new_cred["credential_id"]})
        assert verify_res.status_code == 200
        assert verify_res.json()["is_valid"] is True


@pytest.mark.asyncio
async def test_revoke_credential_killswitch():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Get contractor credential
        creds_res = await ac.get("/api/v1/identity/credentials")
        contractor_cred = next(c for c in creds_res.json() if c["agent_id"] == "agent-contractor" and c["status"] == "ACTIVE")
        cred_id = contractor_cred["credential_id"]

        # Trigger Killswitch
        revoke_res = await ac.post(
            f"/api/v1/identity/revoke/{cred_id}",
            json={"reason": "Suspected prompt anomaly / unauthorized API query"},
        )
        assert revoke_res.status_code == 200
        assert revoke_res.json()["status"] == "REVOKED"

        # Verifying revoked credential must fail
        verify_res = await ac.post("/api/v1/identity/verify", json={"credential_id": cred_id})
        assert verify_res.status_code == 200
        verify_data = verify_res.json()
        assert verify_data["is_valid"] is False
        assert verify_data["status"] == "REVOKED"
        assert "Suspected prompt anomaly" in verify_data["reason"]
