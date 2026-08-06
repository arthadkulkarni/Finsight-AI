import uuid

from fastapi import APIRouter, HTTPException, UploadFile

from app.config import settings
from app.services.ingest import ingest_pdf

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(file: UploadFile) -> dict[str, object]:
    filename = file.filename or "upload.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")

    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    destination = settings.upload_dir / f"{uuid.uuid4()}_{filename}"
    destination.write_bytes(await file.read())

    # Runs synchronously for now — a later phase moves this behind a Celery
    # task so large filings don't block the request.
    result = ingest_pdf(str(destination), document_name=filename)

    return {
        "document_name": result.document_name,
        "num_text_chunks": result.num_text_chunks,
        "num_tables": result.num_tables,
        "num_charts": result.num_charts,
    }
