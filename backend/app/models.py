from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    String, Text, Float, Integer, Boolean, DateTime, Date, ForeignKey,
    Enum as SQLEnum, JSON, UniqueConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from app.database import Base


class AgentStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"          # budget exhausted or manually paused
    DISABLED = "disabled"


class TaskStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"            # dependencies met, waiting to start
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProviderType(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OPENCLAW = "openclaw"
    LOCAL = "local"
    CUSTOM = "custom"


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    mission: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    monthly_budget: Mapped[float] = mapped_column(Float, default=500.0)
    current_month_spend: Mapped[float] = mapped_column(Float, default=0.0)
    budget_month: Mapped[date] = mapped_column(Date, default=date.today().replace(day=1))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    agents: Mapped[List["Agent"]] = relationship("Agent", back_populates="company", cascade="all, delete-orphan")
    workflows: Mapped[List["WorkflowTemplate"]] = relationship("WorkflowTemplate", back_populates="company", cascade="all, delete-orphan")
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="company", cascade="all, delete-orphan")


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False)  # CEO, CTO, Researcher, etc.
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    provider: Mapped[ProviderType] = mapped_column(SQLEnum(ProviderType), default=ProviderType.ANTHROPIC)
    model: Mapped[str] = mapped_column(String(100), default="claude-3-5-sonnet-20241022")
    api_key_env: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # env var name, never store raw key

    monthly_budget: Mapped[float] = mapped_column(Float, default=50.0)
    current_month_spend: Mapped[float] = mapped_column(Float, default=0.0)
    budget_month: Mapped[date] = mapped_column(Date, default=date.today().replace(day=1))

    status: Mapped[AgentStatus] = mapped_column(SQLEnum(AgentStatus), default=AgentStatus.ACTIVE)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("agents.id"), nullable=True)  # for org chart

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company: Mapped["Company"] = relationship("Company", back_populates="agents")
    parent: Mapped[Optional["Agent"]] = relationship("Agent", remote_side=[id], backref="children")
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="agent")
    spend_logs: Mapped[List["SpendLog"]] = relationship("SpendLog", back_populates="agent", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_agents_company_status", "company_id", "status"),
    )


class WorkflowTemplate(Base):
    __tablename__ = "workflow_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Ordered list of stages: [{"name": "...", "role": "...", "requires_human_approval": false}, ...]
    stages: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company: Mapped["Company"] = relationship("Company", back_populates="workflows")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    agent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("agents.id"), nullable=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)

    # Dependency: this task cannot start until depends_on_id is COMPLETED
    depends_on_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tasks.id"), nullable=True)

    requires_human_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Result / output from the agent
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Cost tracking for this specific task
    estimated_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tokens_input: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tokens_output: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    workflow_template_id: Mapped[Optional[int]] = mapped_column(ForeignKey("workflow_templates.id"), nullable=True)
    stage_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company: Mapped["Company"] = relationship("Company", back_populates="tasks")
    agent: Mapped[Optional["Agent"]] = relationship("Agent", back_populates="tasks")
    depends_on: Mapped[Optional["Task"]] = relationship("Task", remote_side=[id], backref="dependents")

    __table_args__ = (
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_company_status", "company_id", "status"),
    )


class SpendLog(Base):
    __tablename__ = "spend_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), nullable=False)
    task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tasks.id"), nullable=True)

    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)

    tokens_input: Mapped[int] = mapped_column(Integer, default=0)
    tokens_output: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False)

    # Optional metadata
    request_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    agent: Mapped["Agent"] = relationship("Agent", back_populates="spend_logs")

    __table_args__ = (
        Index("ix_spend_logs_agent_created", "agent_id", "created_at"),
    )
