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
| — | Docker Compose stack | ✅ `docker compose up --build` |
| 4 | Async worker / background execution | Pending |

## Quick Start — Docker (recommended)

```bash
cp .env.example .env   # optional: GROQ_API_KEY=...
docker compose up --build
```

| Service | URL |
|---------|-----|
| **UI** | http://localhost:8080 |
| **API docs** | http://localhost:8000/docs |
| Postgres | `localhost:5432` (user/pass/db: `orchestrator`) |

Stop: `docker compose down` · Wipe DB: `docker compose down -v`

## Quick Start — local (no Docker)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # or set GROQ_API_KEY
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
cd frontend && npm install && npm run dev
# → http://localhost:5173 (proxies /api → :8000)
```

Open http://localhost:8000/docs for interactive API docs.

### Requirements split
- `requirements-base.txt` — Phase 1 (FastAPI, SQLAlchemy, Alembic, auth helpers)
- `requirements-phase2.txt` — Phase 2 (provider SDKs: anthropic, openai, tiktoken, tenacity)
- `requirements.txt` — convenience full install

## Key Design Decisions (Board-approved)

1. **HITL is declarative** – Board decides per workflow/stage whether approval is required. Fully automatic pipelines are first-class.
2. **Sequential always enforced** – Tasks respect `depends_on_id`. No jumping stages.
3. **Budget is hard** – Every provider call is checked before execution. Exceed → agent auto-paused.
4. **Provider-agnostic** – Clean adapter interface (Claude, OpenAI, Groq, OpenClaw, local, custom).
5. **Mobile-first UI** (Phase 3) – Dashboard usable from phone.

## Manual test

Board checklist (UI + curl): **[MANUAL_TEST.md](./MANUAL_TEST.md)**.

1. Company → hire agents (roles = workflow stages) → **Flows** → Start
2. **Tasks** → Advance / Run → Approve HITL if needed

Optional free LLM: `GROQ_API_KEY` in `.env`.

## Notion Project Hub

Review & feedback: [AI Company Orchestrator – Project Hub](https://app.notion.com/p/3c83ee6346408131bd7ae8ccb57dbb84)
