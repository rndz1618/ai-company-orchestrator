# AI Company Orchestrator

Central dashboard and control plane for managing a team of AI agents as a virtual company.

**You are the Board of Directors.** You define the mission, hire agents into roles, set monthly budgets, design workflows (fully automatic or with Human-in-the-Loop gates), assign sequential tasks, and monitor progress + spend in real time.

**Repo:** https://github.com/rndz1618/ai-company-orchestrator  

**Notion hub:** [Project Hub](https://app.notion.com/p/3c83ee6346408131bd7ae8ccb57dbb84)

## Phase status

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Requirements & architecture | ✅ Approved |
| 1 | Skeleton, models, hard budget, CRUD | ✅ Done |
| 1.5 | Alembic-only, pause types, soft-delete, workflow router | ✅ Done |
| 2 | Workflow engine, sequential + HITL, Claude adapter | ✅ Done |
| 2.1–2.2 | API key auth, rate limit, OpenAI, stuck recovery | ✅ Done |
| 3 | React dashboard: CRUD, HITL, Org, Workflows UI (score 9.5) | ✅ Done |
| — | Groq free-tier provider | ✅ Done |
| — | Manual test runbook | ✅ [MANUAL_TEST.md](./MANUAL_TEST.md) |
| — | Docker Compose (Postgres + API + UI) | ✅ Done |
| 4 | Async worker / background execution | Pending |

## Quick start — Docker (recommended)

```bash
cp .env.example .env
# optional: GROQ_API_KEY=gsk_...

docker compose up --build
```

| Service | URL |
|---------|-----|
| **UI** | http://localhost:8080 |
| **API docs** | http://localhost:8000/docs |
| Postgres | `localhost:5432` (user/pass/db: `orchestrator`) |

```bash
docker compose down       # stop
docker compose down -v    # stop + wipe DB volume
```

## Quick start — local (no Docker)

**API**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # or set GROQ_API_KEY
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**UI**

```bash
cd frontend
npm install && npm run dev
# → http://localhost:5173 (Vite proxies /api → :8000)
```

## What you can do in the UI

1. **Companies** — create company + monthly budget  
2. **Agents** — hire roles; provider `groq` / `anthropic` / `openai`  
3. **Org** — set reporting lines (`parent_id`)  
4. **Flows** — define sequential stages (role + optional HITL) → **Start**  
5. **Tasks** — Advance / Run → open detail → **Approve** when `waiting_approval`  
6. **Budgets** — spend vs caps (Groq cost tracked as $0)

Stage `role` must **exactly match** `agent.role`.

## Manual test checklist

Full Board checklist (UI + curl + negative cases): **[MANUAL_TEST.md](./MANUAL_TEST.md)**.

## Design decisions (Board-approved)

1. **HITL declarative** — per stage; fully automatic pipelines allowed  
2. **Sequential always** — `depends_on_id`; no stage jumping  
3. **Hard budget** — pre-flight check; exceed → `paused_budget`  
4. **Provider-agnostic** — Claude, OpenAI, **Groq**, OpenClaw/local (stubs)  
5. **Mobile-first UI** — sidebar desktop, 5-tab bottom nav mobile  

## Stack

| Layer | Tech |
|-------|------|
| API | FastAPI, SQLAlchemy, Alembic |
| DB | SQLite (local) / Postgres 16 (Docker) |
| Providers | Anthropic, OpenAI, Groq (OpenAI-compatible) |
| UI | React 19, Vite, Tailwind v4, React Router 7 |
| Auth | Optional `X-API-Key` (`ORCHESTRATOR_API_KEY`) |

## Requirements

- `backend/requirements-base.txt` — Phase 1 core  
- `backend/requirements-phase2.txt` — providers + tenacity/tiktoken  
- `backend/requirements.txt` — full install  

## Next (Phase 4)

Async / background worker so multi-stage runs do not block HTTP requests.

---

*Last updated: 2026-08-31 — Phase 3 closed, Docker Compose + MANUAL_TEST shipped.*
