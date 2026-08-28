"""
Budget enforcement service.

Hard rules:
- Every spend must be checked BEFORE the API call.
- If remaining budget < estimated_cost → raise BudgetExceededError and set PAUSED_BUDGET.
- Monthly reset is automatic on first access of a new calendar month.
- Only PAUSED_BUDGET is auto-unpaused on month reset (PAUSED_MANUAL stays paused).
- Company-level budget is also enforced.
- record_spend / check_budget do NOT commit — caller owns the transaction.
"""

from datetime import date
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.models import Agent, Company, SpendLog, AgentStatus


class BudgetExceededError(Exception):
    def __init__(self, message: str, agent_id: int, remaining: float, required: float):
        self.message = message
        self.agent_id = agent_id
        self.remaining = remaining
        self.required = required
        super().__init__(self.message)


def _current_budget_month() -> date:
    return date.today().replace(day=1)


def _reset_if_new_month(agent: Agent, db: Session) -> None:
    """Reset spend counters if we crossed into a new calendar month.
    Only auto-unpause agents that were paused purely for budget reasons.
    """
    current = _current_budget_month()
    if agent.budget_month < current:
        agent.current_month_spend = 0.0
        agent.budget_month = current
        if agent.status == AgentStatus.PAUSED_BUDGET:
            agent.status = AgentStatus.ACTIVE
        db.add(agent)


def _reset_company_if_new_month(company: Company, db: Session) -> None:
    current = _current_budget_month()
    if company.budget_month < current:
        company.current_month_spend = 0.0
        company.budget_month = current
        db.add(company)


def get_agent_remaining_budget(agent: Agent, db: Session) -> float:
    _reset_if_new_month(agent, db)
    return max(0.0, agent.monthly_budget - agent.current_month_spend)


def get_company_remaining_budget(company: Company, db: Session) -> float:
    _reset_company_if_new_month(company, db)
    return max(0.0, company.monthly_budget - company.current_month_spend)


def check_budget(
    agent: Agent,
    estimated_cost: float,
    db: Session,
    enforce_company: bool = True,
) -> Tuple[bool, float]:
    """
    Pre-flight check.
    Returns (allowed: bool, remaining_after: float)
    Raises BudgetExceededError if not allowed.
    Does NOT commit — caller must commit if desired.
    """
    if agent.status == AgentStatus.DISABLED:
        raise BudgetExceededError(
            f"Agent {agent.id} ({agent.name}) is disabled",
            agent_id=agent.id,
            remaining=0.0,
            required=estimated_cost,
        )

    if agent.status == AgentStatus.PAUSED_MANUAL:
        raise BudgetExceededError(
            f"Agent {agent.id} ({agent.name}) is manually paused by Board",
            agent_id=agent.id,
            remaining=get_agent_remaining_budget(agent, db),
            required=estimated_cost,
        )

    remaining = get_agent_remaining_budget(agent, db)

    if estimated_cost > remaining:
        agent.status = AgentStatus.PAUSED_BUDGET
        db.add(agent)
        raise BudgetExceededError(
            f"Agent '{agent.name}' monthly budget exceeded. "
            f"Remaining: ${remaining:.4f}, required: ${estimated_cost:.4f}. Agent paused (budget).",
            agent_id=agent.id,
            remaining=remaining,
            required=estimated_cost,
        )

    if enforce_company:
        company = agent.company
        company_remaining = get_company_remaining_budget(company, db)
        if estimated_cost > company_remaining:
            raise BudgetExceededError(
                f"Company monthly budget would be exceeded. "
                f"Company remaining: ${company_remaining:.4f}, required: ${estimated_cost:.4f}.",
                agent_id=agent.id,
                remaining=company_remaining,
                required=estimated_cost,
            )

    return True, remaining - estimated_cost


def record_spend(
    agent: Agent,
    cost_usd: float,
    tokens_input: int,
    tokens_output: int,
    provider: str,
    model: str,
    db: Session,
    task_id: Optional[int] = None,
    request_id: Optional[str] = None,
    meta: Optional[dict] = None,
) -> SpendLog:
    """
    Record an actual spend after a successful API call.
    Does NOT commit — caller owns the transaction.
    """
    _reset_if_new_month(agent, db)
    _reset_company_if_new_month(agent.company, db)

    agent.current_month_spend += cost_usd
    agent.company.current_month_spend += cost_usd

    if agent.current_month_spend >= agent.monthly_budget:
        agent.status = AgentStatus.PAUSED_BUDGET

    log = SpendLog(
        agent_id=agent.id,
        task_id=task_id,
        provider=provider,
        model=model,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        cost_usd=cost_usd,
        request_id=request_id,
        meta=meta or {},
    )
    db.add(log)
    db.add(agent)
    db.add(agent.company)
    return log


def estimate_cost(
    provider: str,
    model: str,
    tokens_input: int,
    tokens_output: int = 0,
) -> float:
    """Rough cost estimator (USD) for pre-flight checks."""
    pricing = {
        "claude-3-5-sonnet-20241022": (3.00, 15.00),
        "claude-3-5-sonnet-latest": (3.00, 15.00),
        "claude-3-opus-20240229": (15.00, 75.00),
        "claude-3-haiku-20240307": (0.25, 1.25),
        "claude-sonnet-4-20250514": (3.00, 15.00),
        "gpt-4o": (2.50, 10.00),
        "gpt-4o-mini": (0.15, 0.60),
        "gpt-4.1": (2.00, 8.00),
        "o3": (10.00, 40.00),
        "default": (3.00, 15.00),
    }

    input_price, output_price = pricing.get(model, pricing["default"])
    cost = (tokens_input / 1_000_000) * input_price + (tokens_output / 1_000_000) * output_price
    return round(cost * 1.05, 6)


def set_agent_budget(agent: Agent, new_budget: float, db: Session) -> Agent:
    if new_budget < 0:
        raise ValueError("Budget cannot be negative")
    agent.monthly_budget = new_budget
    if agent.status == AgentStatus.PAUSED_BUDGET and get_agent_remaining_budget(agent, db) > 0:
        agent.status = AgentStatus.ACTIVE
    db.add(agent)
    return agent


def get_budget_summary(agent: Agent, db: Session) -> dict:
    remaining = get_agent_remaining_budget(agent, db)
    return {
        "agent_id": agent.id,
        "name": agent.name,
        "monthly_budget": agent.monthly_budget,
        "current_month_spend": agent.current_month_spend,
        "remaining": remaining,
        "budget_month": agent.budget_month.isoformat(),
        "status": agent.status.value,
        "utilization_pct": round(
            (agent.current_month_spend / agent.monthly_budget) * 100, 2
        ) if agent.monthly_budget > 0 else 0,
    }
