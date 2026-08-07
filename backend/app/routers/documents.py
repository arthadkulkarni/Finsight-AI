import uuid

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, UploadFile

from app.celery_app import celery_app
from app.config import settings
from app.tasks import ingest_pdf_task

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", status_code=202)
async def upload_document(file: UploadFile) -> dict[str, str]:
    filename = file.filename or "upload.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")

    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    destination = settings.upload_dir / f"{uuid.uuid4()}_{filename}"
    destination.write_bytes(await file.read())

    # Hands off to a Celery worker and returns immediately — parsing +
    # embedding a real filing can take minutes, too long to hold the request.
    # Poll GET /documents/status/{task_id} for progress.
    task = ingest_pdf_task.delay(str(destination), filename)

    return {"task_id": task.id, "status": "queued", "document_name": filename}


@router.get("/status/{task_id}")
def get_upload_status(task_id: str) -> dict[str, object]:
    result = AsyncResult(task_id, app=celery_app)
    response: dict[str, object] = {"task_id": task_id, "status": result.status}
    if result.successful():
        response["result"] = result.result
    elif result.failed():
        response["error"] = str(result.result)
    return response
