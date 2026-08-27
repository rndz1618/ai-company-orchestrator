from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Agent, Company, AgentStatus
from app.schemas import AgentCreate, AgentUpdate, AgentOut, BudgetSummary
from app.services.budget import get_budget_summary, set_agent_budget

router = APIRouter()


@router.post("/", response_model=AgentOut, status_code=201)
def create_agent(payload: AgentCreate, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == payload.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if payload.parent_id:
        parent = db.query(Agent).filter(Agent.id == payload.parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent agent not found")

    agent = Agent(
        company_id=payload.company_id,
        name=payload.name,
        role=payload.role,
        system_prompt=payload.system_prompt,
        description=payload.description,
        provider=payload.provider,
        model=payload.model,
        monthly_budget=payload.monthly_budget,
        parent_id=payload.parent_id,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


@router.get("/", response_model=List[AgentOut])
def list_agents(company_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(Agent)
    if company_id:
        q = q.filter(Agent.company_id == company_id)
    return q.all()


@router.get("/{agent_id}", response_model=AgentOut)
def get_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.patch("/{agent_id}", response_model=AgentOut)
def update_agent(agent_id: int, payload: AgentUpdate, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    data = payload.model_dump(exclude_unset=True)
    if "monthly_budget" in data:
        agent = set_agent_budget(agent, data.pop("monthly_budget"), db)

    for key, value in data.items():
        setattr(agent, key, value)

    db.commit()
    db.refresh(agent)
    return agent


@router.get("/{agent_id}/budget", response_model=BudgetSummary)
def agent_budget(agent_id: int, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return get_budget_summary(agent, db)


@router.post("/{agent_id}/pause", response_model=AgentOut)
def pause_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.status = AgentStatus.PAUSED
    db.commit()
    db.refresh(agent)
    return agent


@router.post("/{agent_id}/resume", response_model=AgentOut)
def resume_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    from app.services.budget import get_agent_remaining_budget
    remaining = get_agent_remaining_budget(agent, db)
    if remaining <= 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot resume: remaining budget is ${remaining:.4f}. Increase budget first.",
        )
    agent.status = AgentStatus.ACTIVE
    db.commit()
    db.refresh(agent)
    return agent
