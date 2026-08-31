"""Phase 2 – execution endpoints (run task, start workflow, advance, recover)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models import Task, WorkflowTemplate
from app.schemas import TaskOut
from app.services.workflow_engine import (
    run_task,
    start_workflow,
    advance_ready_tasks,
    can_run_task,
    recover_stuck_running,
    TaskNotRunnable,
    WorkflowEngineError,
)
from app.services.budget import BudgetExceededError

router = APIRouter()


class StartWorkflowRequest(BaseModel):
    company_id: int
    title_prefix: Optional[str] = None


class RunTaskResponse(BaseModel):
    task: TaskOut
    message: str


@router.post("/tasks/{task_id}/run", response_model=RunTaskResponse)
def api_run_task(task_id: int, db: Session = Depends(get_db)):
    """Execute a single task (provider call + budget + state transition)."""
    try:
        task = run_task(task_id, db)
    except TaskNotRunnable as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BudgetExceededError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except WorkflowEngineError as e:
        raise HTTPException(status_code=502, detail=str(e))

    msg = (
        "Completed – waiting for human approval"
        if task.status.value == "waiting_approval"
        else f"Task finished with status={task.status.value}"
    )
    return RunTaskResponse(task=task, message=msg)


@router.get("/tasks/{task_id}/can-run")
def api_can_run(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id, Task.is_active == True).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    ok, reason = can_run_task(task, db)
    return {"task_id": task_id, "can_run": ok, "reason": reason, "status": task.status.value}


@router.post("/workflows/{workflow_id}/start", response_model=List[TaskOut])
def api_start_workflow(
    workflow_id: int,
    payload: StartWorkflowRequest,
    db: Session = Depends(get_db),
):
    """
    Materialize workflow template into sequential tasks.
    Does not auto-execute; call /tasks/{id}/run or /companies/{id}/advance.
    """
    try:
        tasks = start_workflow(
            workflow_id,
            payload.company_id,
            db,
            title_prefix=payload.title_prefix,
        )
    except WorkflowEngineError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return tasks


@router.post("/companies/{company_id}/advance", response_model=List[TaskOut])
def api_advance(company_id: int, db: Session = Depends(get_db)):
    """
    Run the next READY task for this company (one step).
    Respects sequential depends_on and HITL gates.
    """
    try:
        executed = advance_ready_tasks(company_id, db)
    except BudgetExceededError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except WorkflowEngineError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return executed


@router.post("/recover-stuck", response_model=List[TaskOut])
def api_recover_stuck(
    company_id: int | None = None,
    older_than_minutes: int | None = None,
    db: Session = Depends(get_db),
):
    """
    Mark tasks stuck in RUNNING past the threshold as FAILED.
    Default threshold: settings.STUCK_RUNNING_MINUTES (30).
    """
    recovered = recover_stuck_running(
        db,
        older_than_minutes=older_than_minutes,
        company_id=company_id,
    )
    return recovered
