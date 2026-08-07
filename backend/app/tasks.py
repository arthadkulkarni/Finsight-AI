from app.celery_app import celery_app
from app.services.ingest import ingest_pdf


@celery_app.task(name="ingest_pdf_task")
def ingest_pdf_task(file_path: str, document_name: str) -> dict[str, object]:
    result = ingest_pdf(file_path, document_name)
    return {
        "document_name": result.document_name,
        "num_text_chunks": result.num_text_chunks,
        "num_tables": result.num_tables,
        "num_charts": result.num_charts,
    }
