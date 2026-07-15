from fastapi import FastAPI

# This is the entrypoint for the FinSight AI backend. Later phases will add
# routers for document upload, chat, and job status here (via app.include_router),
# rather than growing this file directly.
app = FastAPI(title="FinSight AI API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
