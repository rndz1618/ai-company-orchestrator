from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import WorkflowTemplate, Company
from app.schemas import WorkflowTemplateCreate, WorkflowTemplateOut

router = APIRouter()


@router.post("/", response_model=WorkflowTemplateOut, status_code=201)
def create_workflow(payload: WorkflowTemplateCreate, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == payload.company_id, Company.is_active == True).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    stages_data = [s.model_dump() if hasattr(s, "model_dump") else s for s in payload.stages]
    wf = WorkflowTemplate(
        company_id=payload.company_id,
        name=payload.name,
        description=payload.description,
        stages=stages_data,
    )
    db.add(wf)
    db.commit()
    db.refresh(wf)
    return wf


@router.get("/", response_model=List[WorkflowTemplateOut])
def list_workflows(company_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(WorkflowTemplate).filter(WorkflowTemplate.is_active == True)
    if company_id:
        q = q.filter(WorkflowTemplate.company_id == company_id)
    return q.all()


@router.get("/{workflow_id}", response_model=WorkflowTemplateOut)
def get_workflow(workflow_id: int, db: Session = Depends(get_db)):
    wf = db.query(WorkflowTemplate).filter(
        WorkflowTemplate.id == workflow_id, WorkflowTemplate.is_active == True
    ).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf


@router.delete("/{workflow_id}", status_code=204)
def soft_delete_workflow(workflow_id: int, db: Session = Depends(get_db)):
    wf = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    wf.is_active = False
    db.commit()
    return None
