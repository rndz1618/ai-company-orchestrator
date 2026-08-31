# Manual test runbook — AI Company Orchestrator

Uji end-to-end **tanpa Docker**. Target: Board bisa verifikasi loop UI + API di mesin lokal.

## 0. Prasyarat

- Python 3.11+
- Node.js 20+
- (Opsional) [Groq API key](https://console.groq.com/keys) — gratis, untuk run agent sungguhan

## 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt
# atau: pip install -r requirements-base.txt -r requirements-phase2.txt

cp .env.example .env
# Edit .env minimal:
#   GROQ_API_KEY=gsk_...          # jika mau call LLM
#   ORCHESTRATOR_API_KEY=         # kosong = open (dev)
#   ALLOWED_ORIGINS=http://localhost:5173

alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Cek:

```bash
curl -s http://localhost:8000/health
# → {"status":"ok", ...}
```

Docs: http://localhost:8000/docs

## 2. Frontend

Terminal kedua:

```bash
cd frontend
npm install
npm run dev
```

Buka: http://localhost:5173

Vite proxy mengarahkan `/api` dan `/health` ke `:8000`.

Jika pakai `ORCHESTRATOR_API_KEY`, isi di sidebar **API Key** → Save.

## 3. Checklist UI (happy path)

Kerjakan berurutan. Centang mental / catat ID.

| # | Langkah | Halaman | Hasil yang diharapkan |
|---|---------|---------|------------------------|
| 1 | **New company** | Companies | Muncul di list; budget default |
| 2 | **Hire 2 agents** (role beda, mis. `Researcher` + `Writer`) | Agents | Status `active`; provider **groq** + model `llama-3.3-70b-versatile` (atau anthropic jika ada key) |
| 3 | (Opsional) Set reporting line | Org | Tree berubah; parent tersimpan |
| 4 | **New workflow** 2 stage: role = agent roles; stage 2 centang **HITL** | Flows | Stages tampil berurutan + badge HITL |
| 5 | Isi **Title prefix** (opsional) → **Start** | Flows | Banner hijau: `Started → N task(s)`; link ke Tasks |
| 6 | **Advance** / buka task READY → **Run** | Tasks / detail | Status jalan → `waiting_approval` atau `completed` |
| 7 | Task HITL → **Approve** | Task detail | Status `completed`; Advance bisa lanjut stage berikutnya |
| 8 | Cek spend | Budgets / Agents | Groq ≈ $0 cost; token ter-log jika run LLM |

### Role harus cocok

`workflow.stage.role` **harus sama** dengan `agent.role` (string match).  
Contoh gagal: stage `researcher` vs agent `Researcher`.

## 4. Smoke API (tanpa UI)

Ganti header jika API key di-set: `-H "X-API-Key: ..."`

```bash
# Company
curl -s -X POST http://localhost:8000/api/companies/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Paperclip Lab","mission":"Deep dive ID","monthly_budget":100}'

# Agent (company_id dari response di atas)
curl -s -X POST http://localhost:8000/api/agents/ \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": 1,
    "name": "R1",
    "role": "Researcher",
    "provider": "groq",
    "model": "llama-3.3-70b-versatile",
    "monthly_budget": 20
  }'

# Workflow
curl -s -X POST http://localhost:8000/api/workflows/ \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": 1,
    "name": "Deep dive v1",
    "stages": [
      {"name": "Research", "role": "Researcher", "requires_human_approval": false},
      {"name": "Draft", "role": "Writer", "requires_human_approval": true}
    ]
  }'

# Start → materialize tasks
curl -s -X POST http://localhost:8000/api/execution/workflows/1/start \
  -H "Content-Type: application/json" \
  -d '{"company_id": 1, "title_prefix": "Uji manual"}'

# Advance satu langkah
curl -s -X POST http://localhost:8000/api/execution/companies/1/advance

# Approve HITL (task_id dari list)
curl -s -X POST http://localhost:8000/api/tasks/2/approve \
  -H "Content-Type: application/json" \
  -d '{"approved_by":"board"}'
```

## 5. Kasus negatif (cepat)

| Kasus | Aksi | Harapan |
|-------|------|---------|
| Budget habis | Turunkan `monthly_budget` agent ke 0, coba Run | 409 / agent `paused_budget`; UI Play disabled |
| Resume budget-pause | Klik Play tanpa naikkan budget | Error jelas, bukan silent 400 |
| Stage role tidak ada agent | Start workflow role `NoSuchRole` | Error / task tanpa agent gagal saat run |
| Soft-delete | Delete company/agent/workflow | Hilang dari list; tidak di hard-delete |

## 6. Shutdown

```bash
# Ctrl+C di terminal uvicorn + vite
# Data SQLite default: backend/orchestrator.db
```

Reset DB dev:

```bash
cd backend
rm -f orchestrator.db
alembic upgrade head
```

## 7. Yang belum diuji di sini

- Deploy Vercel/Render (butuh hosting + `VITE_API_URL`)
- Async worker / background queue (Phase 4)
- Multi-user auth (masih API key tunggal)

---

**Pass criteria Phase 3 manual:** langkah 1–7 checklist UI hijau tanpa error blocking; HITL Approve mengubah status; Advance menghormati `depends_on`.
