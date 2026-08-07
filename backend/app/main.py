from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import chat, documents

app = FastAPI(title="FinSight AI API")
app.include_router(documents.router)
app.include_router(chat.router)

# Chart images extracted during ingestion live on disk — this is what turns
# a source's image_url into something the browser can actually load. Must
# exist before mounting: StaticFiles refuses to start against a missing dir,
# and on a fresh checkout nothing has created it yet.
settings.extracted_image_dir.mkdir(parents=True, exist_ok=True)
app.mount("/images", StaticFiles(directory=settings.extracted_image_dir), name="images")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
