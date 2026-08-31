# AI Company Orchestrator — Dashboard (Phase 3)

React + Vite + Tailwind v4 mobile-first Board dashboard.

## Setup

```bash
# Backend first
cd ../backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend
cd ../frontend
npm install
npm run dev
```

Open http://localhost:5173

Optional API key (browser console):
```js
localStorage.setItem('orchestrator_api_key', 'your-key')
```

## Pages

| Route | Purpose |
|-------|--------|
| `/` | Overview stats + recent tasks |
| `/companies` | Company list + budget bars |
| `/agents` | Agent roster + status |
| `/tasks` | Task board + Advance button |
| `/budgets` | Company & agent spend monitors |

Vite proxies `/api` and `/health` to `http://localhost:8000`.
