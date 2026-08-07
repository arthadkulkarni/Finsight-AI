# FinSight AI

Multi-modal financial RAG system for querying SEC 10-K filings — text, tables,
and charts, with cited answers.

**Status: core pipeline works end-to-end.** Upload a 10-K PDF, it's parsed
(text/tables/charts), embedded, and stored in Qdrant asynchronously via
Celery; ask a question and get a Claude-generated answer with inline
citations, built from hybrid (dense + BM25) retrieval and Cohere reranking.
The frontend is still a placeholder — no chat UI yet. A full architecture
diagram, Kubernetes manifests, Terraform (AWS), and an evaluation framework
are still to come.

## Structure

- `backend/` — FastAPI app + Celery worker (`app/main.py`, `app/tasks.py`),
  tests in `backend/tests/`
- `frontend/` — Vite + React + TypeScript app
- `docker-compose.yml` — the whole stack: frontend, API, worker, Qdrant, Redis
- `.github/workflows/ci.yml` — lint, test, typecheck, Docker build, and a
  Compose smoke test on every push/PR to `main`

## Quickstart (Docker Compose)

```bash
cp backend/.env.example backend/.env   # then fill in your API keys
docker compose up --build
```

- Frontend: http://localhost:3000
- API: http://localhost:8000 (also reachable via the frontend at `/api/*`)
- Qdrant dashboard: http://localhost:6333/dashboard

Uploaded PDFs and the vector store persist in named Docker volumes across
restarts. `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` are required for
ingestion; all three (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`,
`COHERE_API_KEY`) are required to get an answer from `/chat`. Without them,
requests fail with a clear "API key not set" error at the exact step that
needed it, rather than doing anything silently wrong.

## Local development (without Docker)

```bash
# Backend — also needs redis-server running locally for Celery
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload                       # http://localhost:8000/health
celery -A app.celery_app worker --loglevel=info --pool=solo  # separate terminal; macOS needs --pool=solo
                                                      # (prefork segfaults when forking a process that
                                                      # already has torch/onnxruntime loaded — a Linux
                                                      # container, e.g. via Compose, doesn't have this issue)

# Frontend
cd frontend
npm install
npm run dev                                          # http://localhost:5173
```

A full architecture diagram, Kubernetes manifests, Terraform (AWS), and an
evaluation framework will be added in later phases of this build.
