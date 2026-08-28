from datetime import datetime, date
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class AgentStatusEnum(str, Enum):
    ACTIVE = "active"
    PAUSED_BUDGET = "paused_budget"
    PAUSED_MANUAL = "paused_manual"
    DISABLED = "disabled"


class TaskStatusEnum(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProviderTypeEnum(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OPENCLAW = "openclaw"
    LOCAL = "local"
    CUSTOM = "custom"


# ---------- Company ----------
class CompanyBase(BaseModel):
    name: str
    mission: Optional[str] = None
    monthly_budget: float = 500.0


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    mission: Optional[str] = None
    monthly_budget: Optional[float] = None


class CompanyOut(CompanyBase):
    id: int
    current_month_spend: float
    budget_month: date
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- Agent ----------
class AgentBase(BaseModel):
    name: str
    role: str
    system_prompt: Optional[str] = None
    description: Optional[str] = None
    provider: ProviderTypeEnum = ProviderTypeEnum.ANTHROPIC
    model: str = "claude-3-5-sonnet-20241022"
    monthly_budget: float = 50.0
    parent_id: Optional[int] = None


class AgentCreate(AgentBase):
    company_id: int


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    system_prompt: Optional[str] = None
    description: Optional[str] = None
    provider: Optional[ProviderTypeEnum] = None
    model: Optional[str] = None
    monthly_budget: Optional[float] = None
    parent_id: Optional[int] = None
    status: Optional[AgentStatusEnum] = None


class AgentOut(AgentBase):
    id: int
    company_id: int
    current_month_spend: float
    budget_month: date
    status: AgentStatusEnum
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BudgetSummary(BaseModel):
    agent_id: int
    name: str
    monthly_budget: float
    current_month_spend: float
    remaining: float
    budget_month: str
    status: str
    utilization_pct: float


# ---------- Workflow ----------
class WorkflowStage(BaseModel):
    name: str
    role: str
    requires_human_approval: bool = False
    description: Optional[str] = None


class WorkflowTemplateCreate(BaseModel):
    company_id: int
    name: str
    description: Optional[str] = None
    stages: List[WorkflowStage]


class WorkflowTemplateOut(BaseModel):
    id: int
    company_id: int
    name: str
    description: Optional[str]
    stages: List[Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- Task ----------
class TaskCreate(BaseModel):
    company_id: int
    agent_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    depends_on_id: Optional[int] = None
    requires_human_approval: bool = False
    workflow_template_id: Optional[int] = None
    stage_index: Optional[int] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatusEnum] = None
    agent_id: Optional[int] = None
    result: Optional[str] = None


class TaskApprove(BaseModel):
    approved_by: str = "board"


class TaskOut(BaseModel):
    id: int
    company_id: int
    agent_id: Optional[int]
    title: str
    description: Optional[str]
    status: TaskStatusEnum
    depends_on_id: Optional[int]
    requires_human_approval: bool
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    result: Optional[str]
    error_message: Optional[str]
    estimated_cost: Optional[float]
    actual_cost: Optional[float]
    tokens_input: Optional[int]
    tokens_output: Optional[int]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# ---------- Spend ----------
class SpendLogOut(BaseModel):
    id: int
    agent_id: int
    task_id: Optional[int]
    provider: str
    model: str
    tokens_input: int
    tokens_output: int
    cost_usd: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
