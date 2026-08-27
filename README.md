# AI Company Orchestrator

Central dashboard and control plane for managing a team of AI agents as a virtual company.

**You are the Board of Directors.** You define the mission, hire agents into roles, set monthly budgets, design workflows (fully automatic or with Human-in-the-Loop gates), assign sequential tasks, and monitor progress + spend in real time.

## Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Requirements & Architecture | ✅ Approved |
| 1 | Project skeleton + DB models + Budget enforcement | ✅ Done |
| 2 | Workflow engine + sequential execution + provider adapters | Pending |
| 3 | React + Tailwind dashboard (mobile-first) | Pending |
| 4 | Auth, org chart UI, real-time updates | Pending |

## Phase 1 Deliverables

- FastAPI backend skeleton
- SQLAlchemy models: Company, Agent, WorkflowTemplate, Task, SpendLog
- Hard budget enforcement service (per-agent + company level)
- Automatic monthly budget reset
- Auto-pause agent when budget exhausted
- Pre-flight cost estimation
- Immutable spend logging
- Basic CRUD routers for companies, agents, tasks, budgets
- Configurable Human-in-the-Loop (per task / stage)
- Alembic migrations (first migration: initial_schema_phase1)
- Requirements split (base / phase2)

## Quick Start (Phase 1)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows

# Phase 1 only
pip install -r requirements-base.txt

# or full (Phase 1 + Phase 2 deps)
pip install -r requirements.txt

# Apply migrations
alembic upgrade head

# Run API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000/docs for interactive API docs.

### Requirements split
- `requirements-base.txt` — Phase 1 (FastAPI, SQLAlchemy, Alembic, auth helpers)
- `requirements-phase2.txt` — Phase 2 (provider SDKs: anthropic, openai, tiktoken, tenacity)
- `requirements.txt` — convenience full install

### Alembic
- Environment: `alembic/`
- First migration: `alembic/versions/8d5da4fc0b82_initial_schema_phase1.py`
- Commands: `alembic revision --autogenerate -m "msg"` / `alembic upgrade head`

## Key Design Decisions (Board-approved)

1. **HITL is declarative** – Board decides per workflow/stage whether approval is required. Fully automatic pipelines are first-class.
2. **Sequential always enforced** – Tasks respect `depends_on_id`. No jumping stages.
3. **Budget is hard** – Every provider call is checked before execution. Exceed → agent auto-paused.
4. **Provider-agnostic** – Clean adapter interface (Claude, OpenAI, OpenClaw, local, custom).
5. **Mobile-first UI** (Phase 3) – Dashboard usable from phone.

## Notion Project Hub

Review & feedback: [AI Company Orchestrator – Project Hub](https://app.notion.com/p/3c83ee6346408131bd7ae8ccb57dbb84)

## Next Phase (Phase 2)

After Board approval of Phase 1:
- Workflow execution engine
- Provider adapters (starting with Anthropic Claude)
- Task state machine that respects dependencies + optional approval gates
- Cost tracking integration with real API responses
