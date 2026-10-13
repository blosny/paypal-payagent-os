import pytest
from backend.app.models.agent import Agent, AgentPolicy, AgentPersonality
from backend.app.models.transaction import TransactionIntent, TransactionStatus
from backend.app.services.policy_engine import PolicyEngine


@pytest.fixture
def fresh_engine():
    return PolicyEngine()


def test_inactive_agent_cannot_transact(fresh_engine):
    agent = fresh_engine.get_agent("agent-devops")
    agent.is_active = False

    intent = TransactionIntent(
        agent_id="agent-devops",
        amount=10.0,
        currency="USD",
        recipient="AWS",
        category="CLOUD_COMPUTE",
        reasoning="Routine ping",
    )
    can_execute, reason = fresh_engine.evaluate_policy(agent, intent)
    assert can_execute is False
    assert "disabled" in reason.lower()


def test_insufficient_wallet_balance(fresh_engine):
    agent = fresh_engine.get_agent("agent-devops")
    agent.wallet_balance = 5.0  # Very low balance

    intent = TransactionIntent(
        agent_id="agent-devops",
        amount=20.0,
        currency="USD",
        recipient="AWS",
        category="CLOUD_COMPUTE",
        reasoning="Exceeds wallet balance",
    )
    can_execute, reason = fresh_engine.evaluate_policy(agent, intent)
    assert can_execute is False
    assert "insufficient wallet balance" in reason.lower()


def test_disabled_auto_approval_forces_hitl(fresh_engine):
    agent = fresh_engine.get_agent("agent-devops")
    agent.policy.auto_approval_enabled = False

    intent = TransactionIntent(
        agent_id="agent-devops",
        amount=10.0,  # Well under limit
        currency="USD",
        recipient="AWS",
        category="CLOUD_COMPUTE",
        reasoning="Routine task but auto approval turned off",
    )
    can_execute, reason = fresh_engine.evaluate_policy(agent, intent)
    assert can_execute is False
    assert "auto-approval is disabled" in reason.lower()


def test_exact_single_transaction_limit_boundary(fresh_engine):
    agent = fresh_engine.get_agent("agent-devops")
    max_limit = agent.policy.max_per_transaction  # 40.0

    # Exactly at the limit: should pass
    intent_at_limit = TransactionIntent(
        agent_id="agent-devops",
        amount=max_limit,
        currency="USD",
        recipient="AWS",
        category="CLOUD_COMPUTE",
        reasoning="Exact max limit test",
    )
    can_exec, reason = fresh_engine.evaluate_policy(agent, intent_at_limit)
    assert can_exec is True

    # 1 cent over the limit: should fail
    intent_over_limit = TransactionIntent(
        agent_id="agent-devops",
        amount=max_limit + 0.01,
        currency="USD",
        recipient="AWS",
        category="CLOUD_COMPUTE",
        reasoning="1 cent over limit test",
    )
    can_exec_over, reason_over = fresh_engine.evaluate_policy(agent, intent_over_limit)
    assert can_exec_over is False
    assert "exceeds single transaction limit" in reason_over.lower()


@pytest.mark.asyncio
async def test_daily_cumulative_budget_overflow(fresh_engine):
    agent = fresh_engine.get_agent("agent-devops")
    # Daily budget is 200.0, max per tx is 40.0
    agent.spent_today = 180.0  # Only $20 headroom left today

    intent = TransactionIntent(
        agent_id="agent-devops",
        amount=30.0,  # Under 40.0 single limit, but 180 + 30 = 210 > 200 daily budget
        currency="USD",
        recipient="AWS",
        category="CLOUD_COMPUTE",
        reasoning="Causes daily budget overflow",
    )
    can_exec, reason = fresh_engine.evaluate_policy(agent, intent)
    assert can_exec is False
    assert "exceed daily budget" in reason.lower()


def test_reset_daily_budgets(fresh_engine):
    agent = fresh_engine.get_agent("agent-devops")
    agent.spent_today = 150.0

    res = fresh_engine.reset_daily_budgets()
    assert res["agents_reset_count"] >= 3
    assert agent.spent_today == 0.0


@pytest.mark.asyncio
async def test_invalid_resolve_decision_raises_error(fresh_engine):
    intent = TransactionIntent(
        agent_id="agent-devops",
        amount=90.0,
        currency="USD",
        recipient="AWS",
        category="CLOUD_COMPUTE",
        reasoning="Needs supervisor review",
    )
    record = await fresh_engine.submit_intent(intent)
    assert record.status == TransactionStatus.PENDING_APPROVAL

    with pytest.raises(ValueError, match="Decision must be either 'APPROVE' or 'REJECT'"):
        await fresh_engine.resolve_pending_transaction(record.id, decision="MAYBE")


def test_unlisted_vendor_allowed_when_flag_true(fresh_engine):
    agent = fresh_engine.get_agent("agent-payout")
    assert agent.policy.allow_unlisted_vendors is True

    intent = TransactionIntent(
        agent_id="agent-payout",
        amount=25.0,
        currency="USD",
        recipient="UnlistedNewVendorStore",
        category="MISC",
        reasoning="Vendor is unlisted but agent allows unlisted vendors",
    )
    can_exec, reason = fresh_engine.evaluate_policy(agent, intent)
    assert can_exec is True
