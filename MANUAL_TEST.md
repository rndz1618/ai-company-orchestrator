# Manual test runbook — AI Company Orchestrator

Uji end-to-end di mesin lokal. Dua opsi start: **Docker Compose** atau **manual** (venv + npm).

## 0. Prasyarat

- **Docker path:** Docker Engine + Compose v2
- **Manual path:** Python 3.11+, Node.js 20+
- (Opsional) [Groq API key](https://console.groq.com/keys) — gratis, untuk run agent sungguhan

## 1A. Docker Compose (recommended)

```bash
# dari root repo
cp .env.example .env
# optional: GROQ_API_KEY=gsk_... di .env

docker compose up --build
```

| Service | URL |
|---------|-----|
| UI | http://localhost:8080 |
| API / docs | http://localhost:8000/docs |
| Postgres | localhost:5432 (`orchestrator` / `orchestrator`) |

Stop: `docker compose down` · Hapus data DB: `docker compose down -v`

Lanjut ke **§3 Checklist UI** (pakai port **8080**).

## 1B. Backend manual

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
# GROQ_API_KEY=...  ORCHESTRATOR_API_KEY=  ALLOWED_ORIGINS=http://localhost:5173

alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
curl -s http://localhost:8000/health
```

Docs: http://localhost:8000/docs

## 2. Frontend manual (jika tidak pakai Docker UI)

```bash
cd frontend
npm install
npm run dev
```

Buka: http://localhost:5173

Jika pakai `ORCHESTRATOR_API_KEY`, isi di sidebar **API Key** → Save.

## 3. Checklist UI (happy path)

| # | Langkah | Halaman | Hasil yang diharapkan |
|---|---------|---------|------------------------|
| 1 | **New company** | Companies | Muncul di list; budget default |
| 2 | **Hire 2 agents** (role beda, mis. `Researcher` + `Writer`) | Agents | Status `active`; provider **groq** + model `llama-3.3-70b-versatile` |
| 3 | (Opsional) Set reporting line | Org | Tree berubah; parent tersimpan |
| 4 | **New workflow** 2 stage; stage 2 centang **HITL** | Flows | Stages + badge HITL |
| 5 | **Start** | Flows | Banner hijau + link ke Tasks |
| 6 | **Advance** / **Run** | Tasks / detail | `waiting_approval` atau `completed` |
| 7 | **Approve** HITL | Task detail | `completed`; Advance lanjut |
| 8 | Cek spend | Budgets | Groq ≈ $0; token ter-log |

`workflow.stage.role` harus **sama** dengan `agent.role`.

## 4. Smoke API (curl)

```bash
curl -s -X POST http://localhost:8000/api/companies/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Paperclip Lab","mission":"Deep dive ID","monthly_budget":100}'

curl -s -X POST http://localhost:8000/api/agents/ \
  -H "Content-Type: application/json" \
  -d '{"company_id":1,"name":"R1","role":"Researcher","provider":"groq","model":"llama-3.3-70b-versatile","monthly_budget":20}'

curl -s -X POST http://localhost:8000/api/workflows/ \
  -H "Content-Type: application/json" \
  -d '{"company_id":1,"name":"Deep dive v1","stages":[{"name":"Research","role":"Researcher","requires_human_approval":false},{"name":"Draft","role":"Writer","requires_human_approval":true}]}'

curl -s -X POST http://localhost:8000/api/execution/workflows/1/start \
  -H "Content-Type: application/json" \
  -d '{"company_id":1,"title_prefix":"Uji manual"}'

curl -s -X POST http://localhost:8000/api/execution/companies/1/advance
```

## 5. Kasus negatif

| Kasus | Harapan |
|-------|---------|
| Budget 0 + Run | 409 / `paused_budget` |
| Resume tanpa naikkan budget | Error jelas |
| Role stage tidak match agent | Gagal start/run |
| Soft-delete | Hilang dari list |

## 6. Shutdown / reset

```bash
docker compose down -v   # docker
# atau Ctrl+C + rm backend/orchestrator.db + alembic upgrade head
```

**Pass criteria:** checklist §3 hijau; HITL Approve mengubah status; Advance menghormati `depends_on`.
