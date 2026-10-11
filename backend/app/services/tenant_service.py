import uuid
from typing import List, Optional, Dict
from datetime import datetime, timezone
from ..models.tenant import (
    Department,
    DepartmentTransferRequest,
    DepartmentTransferResult,
    TenantSummary,
)


class TenantService:
    """Manages multi-tenant departmental agent hierarchy and cross-departmental budget governance."""

    def __init__(self):
        self._departments: Dict[str, Department] = {}
        self._transfers: List[DepartmentTransferResult] = []
        self._init_mock_departments()

    def _init_mock_departments(self):
        now = datetime.now(timezone.utc).isoformat()
        depts = [
            Department(
                id="dept-eng",
                name="Engineering & Cloud Infrastructure",
                code="ENG",
                allocated_budget=1800.00,
                spent_today=78.50,
                currency="USD",
                lead_name="Elena Rostova (CFO / VP Eng)",
                lead_email="elena.rostova@payagent.io",
                assigned_agent_ids=["agent-devops", "agent-secops"],
                created_at="2026-01-01T00:00:00Z",
            ),
            Department(
                id="dept-research",
                name="Research & AI Model Lab",
                code="RES",
                allocated_budget=1000.00,
                spent_today=50.00,
                currency="USD",
                lead_name="Dr. Aris Vance (Head of AI)",
                lead_email="aris.vance@payagent.io",
                assigned_agent_ids=["agent-research"],
                created_at="2026-01-01T00:00:00Z",
            ),
            Department(
                id="dept-growth",
                name="Growth & Marketing Operations",
                code="MKT",
                allocated_budget=400.00,
                spent_today=0.00,
                currency="USD",
                lead_name="Sarah Koenig (CMO)",
                lead_email="sarah.koenig@payagent.io",
                assigned_agent_ids=["agent-contractor"],
                created_at="2026-01-01T00:00:00Z",
            ),
        ]
        for d in depts:
            self._departments[d.id] = d

    def list_departments(self) -> List[Department]:
        return list(self._departments.values())

    def get_department(self, dept_id: str) -> Optional[Department]:
        return self._departments.get(dept_id)

    def get_department_for_agent(self, agent_id: str) -> Optional[Department]:
        for d in self._departments.values():
            if agent_id in d.assigned_agent_ids:
                return d
        return None

    def transfer_budget(self, request: DepartmentTransferRequest) -> DepartmentTransferResult:
        from_dept = self._departments.get(request.from_dept_id)
        to_dept = self._departments.get(request.to_dept_id)

        if not from_dept:
            raise ValueError(f"Source department '{request.from_dept_id}' not found")
        if not to_dept:
            raise ValueError(f"Destination department '{request.to_dept_id}' not found")
        if from_dept.id == to_dept.id:
            raise ValueError("Source and destination departments cannot be the same")

        available = from_dept.allocated_budget - from_dept.spent_today
        if request.amount > available:
            raise ValueError(
                f"Insufficient departmental funds in '{from_dept.name}'. Available: ${available:.2f}, Requested: ${request.amount:.2f}"
            )

        # Atomic budget shift
        from_dept.allocated_budget = round(from_dept.allocated_budget - request.amount, 2)
        to_dept.allocated_budget = round(to_dept.allocated_budget + request.amount, 2)

        result = DepartmentTransferResult(
            transfer_id=f"tx_dept_{uuid.uuid4().hex[:8]}",
            from_dept_id=from_dept.id,
            to_dept_id=to_dept.id,
            from_dept_name=from_dept.name,
            to_dept_name=to_dept.name,
            amount=request.amount,
            reason=request.reason,
            authorized_by=request.authorized_by,
            timestamp=datetime.now(timezone.utc).isoformat(),
            status="COMPLETED",
        )
        self._transfers.insert(0, result)
        return result

    def validate_department_spend(self, agent_id: str, amount: float) -> bool:
        dept = self.get_department_for_agent(agent_id)
        if not dept:
            # If agent not assigned to department, default to allowed
            return True
        remaining = dept.allocated_budget - dept.spent_today
        return amount <= remaining

    def record_department_spend(self, agent_id: str, amount: float) -> Optional[Department]:
        dept = self.get_department_for_agent(agent_id)
        if dept:
            dept.spent_today = round(dept.spent_today + amount, 2)
            return dept
        return None

    def get_summary(self) -> TenantSummary:
        depts = list(self._departments.values())
        return TenantSummary(
            total_departments=len(depts),
            total_allocated=sum(d.allocated_budget for d in depts),
            total_spent=sum(d.spent_today for d in depts),
            departments=depts,
            recent_transfers=self._transfers[:10],
        )


tenant_service = TenantService()
