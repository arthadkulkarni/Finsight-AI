from fastapi import FastAPI

from app.routers import chat, documents

app = FastAPI(title="FinSight AI API")
app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
