from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone

from app.database import get_db
from app.models import Task, Agent, Company, TaskStatus
from app.schemas import TaskCreate, TaskUpdate, TaskOut, TaskApprove

router = APIRouter()


@router.post("/", response_model=TaskOut, status_code=201)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == payload.company_id, Company.is_active == True).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if payload.agent_id:
        agent = db.query(Agent).filter(Agent.id == payload.agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

    if payload.depends_on_id:
        dep = db.query(Task).filter(Task.id == payload.depends_on_id).first()
        if not dep:
            raise HTTPException(status_code=404, detail="Dependency task not found")

    task = Task(
        company_id=payload.company_id,
        agent_id=payload.agent_id,
        title=payload.title,
        description=payload.description,
        depends_on_id=payload.depends_on_id,
        requires_human_approval=payload.requires_human_approval,
        workflow_template_id=payload.workflow_template_id,
        stage_index=payload.stage_index,
        status=TaskStatus.PENDING,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/", response_model=List[TaskOut])
def list_tasks(
    company_id: int | None = None,
    agent_id: int | None = None,
    status: TaskStatus | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Task).filter(Task.is_active == True)
    if company_id:
        q = q.filter(Task.company_id == company_id)
    if agent_id:
        q = q.filter(Task.agent_id == agent_id)
    if status:
        q = q.filter(Task.status == status)
    return q.order_by(Task.created_at.desc()).all()


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id, Task.is_active == True).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id, Task.is_active == True).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)
    return task


@router.post("/{task_id}/approve", response_model=TaskOut)
def approve_task(task_id: int, payload: TaskApprove, db: Session = Depends(get_db)):
    """Human-in-the-Loop approval endpoint. Only works if task is WAITING_APPROVAL."""
    task = db.query(Task).filter(Task.id == task_id, Task.is_active == True).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != TaskStatus.WAITING_APPROVAL:
        raise HTTPException(
            status_code=400,
            detail=f"Task is not waiting for approval (current status: {task.status.value})",
        )

    task.approved_by = payload.approved_by
    task.approved_at = datetime.now(timezone.utc)
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(task)
    return task


@router.post("/{task_id}/cancel", response_model=TaskOut)
def cancel_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id, Task.is_active == True).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
        raise HTTPException(status_code=400, detail="Task already finished")
    task.status = TaskStatus.CANCELLED
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
def soft_delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.is_active = False
    db.commit()
    return None
