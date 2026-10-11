import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.services.tenant_service import tenant_service


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_list_and_get_departments():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # List all departments
        res = await ac.get("/api/v1/tenants/departments")
        assert res.status_code == 200
        depts = res.json()
        assert len(depts) == 3

        eng = next(d for d in depts if d["code"] == "ENG")
        assert eng["name"] == "Engineering & Cloud Infrastructure"
        assert eng["allocated_budget"] == 1800.00
        assert "agent-devops" in eng["assigned_agent_ids"]

        # Get single department by ID
        single_res = await ac.get(f"/api/v1/tenants/departments/{eng['id']}")
        assert single_res.status_code == 200
        assert single_res.json()["code"] == "ENG"


@pytest.mark.asyncio
async def test_department_budget_transfer_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Transfer $150 from Engineering to Research for emergency GPU training
        payload = {
            "from_dept_id": "dept-eng",
            "to_dept_id": "dept-research",
            "amount": 150.00,
            "reason": "Emergency GPU quota rebalancing for LLM fine-tuning",
            "authorized_by": "Elena Rostova (CFO)",
        }
        res = await ac.post("/api/v1/tenants/transfer", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["amount"] == 150.00
        assert data["from_dept_name"] == "Engineering & Cloud Infrastructure"
        assert data["to_dept_name"] == "Research & AI Model Lab"
        assert data["status"] == "COMPLETED"

        # Verify summary reflects changes
        sum_res = await ac.get("/api/v1/tenants/summary")
        assert sum_res.status_code == 200
        sum_data = sum_res.json()
        assert len(sum_data["recent_transfers"]) >= 1


@pytest.mark.asyncio
async def test_department_budget_transfer_insufficient_funds():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Attempt to transfer more than available budget
        payload = {
            "from_dept_id": "dept-growth",
            "to_dept_id": "dept-eng",
            "amount": 99999.00,
            "reason": "Excessive transfer attempt",
            "authorized_by": "Test Supervisor",
        }
        res = await ac.post("/api/v1/tenants/transfer", json=payload)
        assert res.status_code == 400
        assert "Insufficient departmental funds" in res.json()["detail"]


@pytest.mark.asyncio
async def test_tenant_service_spend_validation():
    # Directly test departmental spend check
    # agent-devops belongs to dept-eng
    valid = tenant_service.validate_department_spend("agent-devops", 50.0)
    assert valid is True

    # High amount exceeding remaining
    invalid = tenant_service.validate_department_spend("agent-devops", 99999.0)
    assert invalid is False

    # Recording spend
    updated = tenant_service.record_department_spend("agent-devops", 25.0)
    assert updated is not None
    assert updated.spent_today >= 25.0


@pytest.mark.asyncio
async def test_transfer_same_department_fails():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "from_dept_id": "dept-eng",
            "to_dept_id": "dept-eng",
            "amount": 50.00,
            "reason": "Invalid self-transfer",
            "authorized_by": "Test Supervisor",
        }
        res = await ac.post("/api/v1/tenants/transfer", json=payload)
        assert res.status_code == 400
        assert "cannot be the same" in res.json()["detail"]


@pytest.mark.asyncio
async def test_get_unknown_department_returns_404():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/tenants/departments/dept-nonexistent-99")
        assert res.status_code == 404

