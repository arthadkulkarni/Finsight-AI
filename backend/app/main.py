from fastapi import FastAPI

from app.routers import documents

# This is the entrypoint for the FinSight AI backend. Later phases will add
# routers for chat and job status here (via app.include_router), rather than
# growing this file directly.
app = FastAPI(title="FinSight AI API")
app.include_router(documents.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
