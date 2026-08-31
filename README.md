# AI Company Orchestrator

Central dashboard and control plane for managing a team of AI agents as a virtual company.

**You are the Board of Directors.** You define the mission, hire agents into roles, set monthly budgets, design workflows (fully automatic or with Human-in-the-Loop gates), assign sequential tasks, and monitor progress + spend in real time.

## Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Requirements & Architecture | ✅ Approved |
| 1 | Project skeleton + DB models + Budget enforcement | ✅ Done |
| 1.5 | Polish (Alembic-only, budget 409, pause types, workflow router, soft-delete) | ✅ Done |
| 2 | Workflow engine + sequential execution + provider adapters | ✅ Done |
| 2.1–2.2 | Auth, rate limit, OpenAI/Groq, stuck recovery | ✅ Done |
| 3 | React dashboard: CRUD, HITL, Org, Workflows UI | ✅ Done (9.5) |
| — | Manual local test | See [MANUAL_TEST.md](./MANUAL_TEST.md) |
| 4 | Async worker / background execution | Pending |

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

## Phase 3 (done)

React + Tailwind mobile-first dashboard:
- Overview, Companies, Agents, Tasks, Budgets, Org, Workflows
- Proxy to FastAPI (`/api`)
- Bottom nav (mobile) + sidebar (desktop)

```bash
cd frontend && npm install && npm run dev
# API: uvicorn on :8000
```

## Manual test (local)

Step-by-step Board checklist (UI + curl smoke): **[MANUAL_TEST.md](./MANUAL_TEST.md)**.

1. Start API (`uvicorn` :8000) + UI (`npm run dev` :5173)
2. Company → hire agents (roles match workflow stages) → **Flows** → Start
3. **Tasks** → Advance / Run → Approve HITL if needed

Optional free LLM: set `GROQ_API_KEY` in `backend/.env`.

## Notion Project Hub

Review & feedback: [AI Company Orchestrator – Project Hub](https://app.notion.com/p/3c83ee6346408131bd7ae8ccb57dbb84)
