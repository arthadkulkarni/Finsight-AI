# FinSight AI

Multi-modal financial RAG system for querying SEC 10-K filings — text, tables,
and charts, with cited answers.

**Status: scaffolding phase.** This repo currently contains a minimal backend
(FastAPI) and frontend (React + TypeScript) skeleton with a working CI
pipeline. The ingestion pipeline, retrieval, chat UI, and deployment configs
are being built out incrementally.

## Structure

- `backend/` — FastAPI app (`app/main.py`), tests in `backend/tests/`
- `frontend/` — Vite + React + TypeScript app
- `.github/workflows/ci.yml` — lint, test, typecheck, and Docker build on
  every push/PR to `main`

## Local development

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload   # http://localhost:8000/health

# Frontend
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

A full architecture diagram, one-command `docker-compose up`, Kubernetes
manifests, Terraform (AWS), and an evaluation framework will be added in
later phases of this build.
