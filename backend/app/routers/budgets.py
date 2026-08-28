from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Agent, Company, SpendLog
from app.schemas import BudgetSummary, SpendLogOut
from app.services.budget import get_budget_summary, get_company_remaining_budget

router = APIRouter()


@router.get("/agents/{agent_id}", response_model=BudgetSummary)
def agent_budget_summary(agent_id: int, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id, Agent.is_active == True).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return get_budget_summary(agent, db)


@router.get("/company/{company_id}")
def company_budget_summary(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id, Company.is_active == True).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    remaining = get_company_remaining_budget(company, db)
    agents = db.query(Agent).filter(Agent.company_id == company_id, Agent.is_active == True).all()
    agent_summaries = [get_budget_summary(a, db) for a in agents]

    return {
        "company_id": company.id,
        "name": company.name,
        "monthly_budget": company.monthly_budget,
        "current_month_spend": company.current_month_spend,
        "remaining": remaining,
        "budget_month": company.budget_month.isoformat(),
        "utilization_pct": round(
            (company.current_month_spend / company.monthly_budget) * 100, 2
        ) if company.monthly_budget > 0 else 0,
        "agents": agent_summaries,
    }


@router.get("/agents/{agent_id}/logs", response_model=List[SpendLogOut])
def agent_spend_logs(agent_id: int, limit: int = 50, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id, Agent.is_active == True).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    logs = (
        db.query(SpendLog)
        .filter(SpendLog.agent_id == agent_id)
        .order_by(SpendLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return logs
