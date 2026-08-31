"""
Workflow execution engine.

Rules (Board-approved):
- Sequential always: a task may only run when depends_on is COMPLETED (or None).
- HITL: if requires_human_approval → move to WAITING_APPROVAL after agent finishes.
- Budget: pre-flight check before every provider call; record_spend after success.
- Soft-deleted / paused agents cannot run.
- Soft-deleted dependency blocks the chain with a clear error.
- Every stage must have a role that matches an active agent (fail-fast).
"""

from __future__ import annotations

import logging
from typing import Optional, List

from sqlalchemy.orm import Session

from app.models import (
    Task, Agent, Company, WorkflowTemplate,
    TaskStatus, AgentStatus, utcnow,
)
from app.providers import adapter_for_agent, ProviderNotSupported
from app.services.budget import (
    check_budget, record_spend, estimate_cost, BudgetExceededError,
)

logger = logging.getLogger(__name__)


class WorkflowEngineError(Exception):
    pass


class TaskNotRunnable(WorkflowEngineError):
    pass


def _dependency_satisfied(task: Task, db: Session) -> bool:
    if task.depends_on_id is None:
        return True
    dep = db.query(Task).filter(Task.id == task.depends_on_id).first()
    if not dep:
        return False
    if not dep.is_active:
        return False
    return dep.status == TaskStatus.COMPLETED


def can_run_task(task: Task, db: Session) -> tuple[bool, str]:
    """Return (ok, reason)."""
    if not task.is_active:
        return False, "Task is soft-deleted"
    if task.status in (TaskStatus.RUNNING, TaskStatus.COMPLETED, TaskStatus.CANCELLED):
        return False, f"Task status is {task.status.value}"
    if task.status == TaskStatus.WAITING_APPROVAL:
        return False, "Task is waiting for human approval"
    if task.status == TaskStatus.FAILED:
        pass
    if not _dependency_satisfied(task, db):
        dep = db.query(Task).filter(Task.id == task.depends_on_id).first()
        if dep and not dep.is_active:
            return False, f"Dependency task {task.depends_on_id} was soft-deleted"
        return False, f"Dependency task {task.depends_on_id} not completed"
    if not task.agent_id:
        return False, "No agent assigned"
    agent = db.query(Agent).filter(Agent.id == task.agent_id, Agent.is_active == True).first()
    if not agent:
        return False, "Agent not found or soft-deleted"
    if agent.status == AgentStatus.DISABLED:
        return False, "Agent is disabled"
    if agent.status == AgentStatus.PAUSED_MANUAL:
        return False, "Agent is manually paused by Board"
    if agent.status == AgentStatus.PAUSED_BUDGET:
        return False, "Agent is paused (budget exhausted)"
    return True, "ok"


def build_prompt(task: Task, agent: Agent) -> tuple[str, str]:
    """Return (system, user) messages for the provider."""
    system = agent.system_prompt or f"You are {agent.name}, role: {agent.role}."
    user_parts = [f"# Task: {task.title}"]
    if task.description:
        user_parts.append(task.description)
    if task.depends_on_id and task.depends_on and task.depends_on.result:
        user_parts.append("\n## Previous stage output\n")
        user_parts.append(task.depends_on.result)
    user_parts.append(
        "\nRespond with a thorough, well-structured answer. "
        "Cite data when available. Do not invent facts."
    )
    return system, "\n".join(user_parts)


def run_task(task_id: int, db: Session, *, force: bool = False) -> Task:
    """
    Execute a single task via its assigned agent.
    Pre-flight budget → provider call → record_spend → COMPLETED or WAITING_APPROVAL.
    """
    task = db.query(Task).filter(Task.id == task_id, Task.is_active == True).first()
    if not task:
        raise TaskNotRunnable(f"Task {task_id} not found")

    ok, reason = can_run_task(task, db)
    if not ok and not force:
        raise TaskNotRunnable(reason)

    agent = db.query(Agent).filter(Agent.id == task.agent_id).first()
    if not agent:
        raise TaskNotRunnable("Agent missing")

    system, user = build_prompt(task, agent)

    try:
        adapter = adapter_for_agent(agent)
    except (ProviderNotSupported, ValueError) as e:
        task.status = TaskStatus.FAILED
        task.error_message = str(e)
        db.commit()
        raise WorkflowEngineError(str(e)) from e

    est_in = adapter.estimate_tokens(system + user)
    est_out = 1024
    estimated = estimate_cost(agent.provider.value, agent.model, est_in, est_out)
    task.estimated_cost = estimated

    try:
        check_budget(agent, estimated, db, enforce_company=True)
    except BudgetExceededError:
        task.status = TaskStatus.FAILED
        task.error_message = "Budget exceeded before execution"
        db.add(task)
        db.commit()
        raise

    task.status = TaskStatus.RUNNING
    task.started_at = utcnow()
    task.error_message = None
    db.add(task)
    db.commit()

    try:
        response = adapter.complete(
            system=system,
            user=user,
            model=agent.model,
        )
    except Exception as e:
        logger.exception("Provider call failed for task %s", task_id)
        task.status = TaskStatus.FAILED
        task.error_message = str(e)[:2000]
        db.add(task)
        db.commit()
        raise WorkflowEngineError(f"Provider error: {e}") from e

    record_spend(
        agent=agent,
        cost_usd=response.cost_usd,
        tokens_input=response.tokens_input,
        tokens_output=response.tokens_output,
        provider=response.provider,
        model=response.model,
        db=db,
        task_id=task.id,
        request_id=response.request_id,
    )

    task.result = response.content
    task.actual_cost = response.cost_usd
    task.tokens_input = response.tokens_input
    task.tokens_output = response.tokens_output

    if task.requires_human_approval:
        task.status = TaskStatus.WAITING_APPROVAL
    else:
        task.status = TaskStatus.COMPLETED
        task.completed_at = utcnow()

    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def start_workflow(
    workflow_id: int,
    company_id: int,
    db: Session,
    *,
    title_prefix: Optional[str] = None,
) -> List[Task]:
    """
    Materialize WorkflowTemplate into sequential Tasks.
    Every stage must have a non-empty role matching an active agent — fail-fast otherwise.
    """
    wf = (
        db.query(WorkflowTemplate)
        .filter(
            WorkflowTemplate.id == workflow_id,
            WorkflowTemplate.company_id == company_id,
            WorkflowTemplate.is_active == True,
        )
        .first()
    )
    if not wf:
        raise WorkflowEngineError("Workflow template not found")

    company = db.query(Company).filter(Company.id == company_id, Company.is_active == True).first()
    if not company:
        raise WorkflowEngineError("Company not found")

    stages = wf.stages or []
    if not stages:
        raise WorkflowEngineError("Workflow has no stages")

    created: List[Task] = []
    prev_task_id: Optional[int] = None

    for idx, stage in enumerate(stages):
        if isinstance(stage, dict):
            name = stage.get("name") or f"Stage {idx + 1}"
            role = stage.get("role") or ""
            requires_approval = bool(stage.get("requires_human_approval", False))
            description = stage.get("description") or ""
        else:
            name = getattr(stage, "name", f"Stage {idx + 1}")
            role = getattr(stage, "role", "") or ""
            requires_approval = bool(getattr(stage, "requires_human_approval", False))
            description = getattr(stage, "description", "") or ""

        if not role:
            raise WorkflowEngineError(
                f"Stage {idx} ('{name}'): role is required. "
                f"Every stage must specify a role that matches an active agent."
            )
        agent = (
            db.query(Agent)
            .filter(
                Agent.company_id == company_id,
                Agent.role == role,
                Agent.is_active == True,
            )
            .first()
        )
        if not agent:
            raise WorkflowEngineError(
                f"Stage {idx} ('{name}'): no active agent with role='{role}' "
                f"in company {company_id}. Hire/create agent first."
            )

        title = f"{title_prefix + ' — ' if title_prefix else ''}{name}"
        task = Task(
            company_id=company_id,
            agent_id=agent.id,
            title=title,
            description=description or f"Stage: {name} (role={role})",
            status=TaskStatus.PENDING if prev_task_id else TaskStatus.READY,
            depends_on_id=prev_task_id,
            requires_human_approval=requires_approval,
            workflow_template_id=wf.id,
            stage_index=idx,
        )
        db.add(task)
        db.flush()
        created.append(task)
        prev_task_id = task.id

    db.commit()
    for t in created:
        db.refresh(t)
    return created


def advance_ready_tasks(company_id: int, db: Session) -> List[Task]:
    """Run the next READY task for this company (one sequential step)."""
    candidates = (
        db.query(Task)
        .filter(
            Task.company_id == company_id,
            Task.is_active == True,
            Task.status.in_([TaskStatus.READY, TaskStatus.PENDING, TaskStatus.FAILED]),
        )
        .order_by(Task.stage_index.nullsfirst(), Task.id)
        .all()
    )
    executed = []
    for task in candidates:
        ok, _ = can_run_task(task, db)
        if not ok:
            continue
        if task.status == TaskStatus.PENDING:
            task.status = TaskStatus.READY
            db.add(task)
            db.commit()
        try:
            result = run_task(task.id, db)
            executed.append(result)
            break
        except (TaskNotRunnable, WorkflowEngineError, BudgetExceededError) as e:
            logger.warning("advance skipped task %s: %s", task.id, e)
            continue
    return executed
