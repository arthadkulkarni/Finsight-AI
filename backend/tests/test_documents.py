from types import SimpleNamespace

from fastapi.testclient import TestClient

import app.routers.documents as documents_module
from app.config import settings
from app.main import app

client = TestClient(app)


def test_upload_queues_a_task(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "upload_dir", tmp_path / "uploads")
    monkeypatch.setattr(
        documents_module.ingest_pdf_task,
        "delay",
        lambda file_path, document_name: SimpleNamespace(id="fake-task-id"),
    )

    response = client.post(
        "/documents/upload",
        files={"file": ("sample.pdf", b"%PDF-1.4 fake pdf content", "application/pdf")},
    )

    assert response.status_code == 202
    assert response.json() == {
        "task_id": "fake-task-id",
        "status": "queued",
        "document_name": "sample.pdf",
    }


def test_upload_rejects_non_pdf_files():
    response = client.post(
        "/documents/upload",
        files={"file": ("sample.txt", b"not a pdf", "text/plain")},
    )
    assert response.status_code == 400


def test_status_reports_success(monkeypatch):
    fake_result = SimpleNamespace(
        status="SUCCESS",
        result={
            "document_name": "sample.pdf",
            "num_text_chunks": 3,
            "num_tables": 1,
            "num_charts": 0,
        },
        successful=lambda: True,
        failed=lambda: False,
    )
    monkeypatch.setattr(documents_module, "AsyncResult", lambda task_id, app: fake_result)

    response = client.get("/documents/status/fake-task-id")

    assert response.status_code == 200
    assert response.json() == {
        "task_id": "fake-task-id",
        "status": "SUCCESS",
        "result": {
            "document_name": "sample.pdf",
            "num_text_chunks": 3,
            "num_tables": 1,
            "num_charts": 0,
        },
    }


def test_status_reports_failure(monkeypatch):
    fake_result = SimpleNamespace(
        status="FAILURE",
        result=RuntimeError("boom"),
        successful=lambda: False,
        failed=lambda: True,
    )
    monkeypatch.setattr(documents_module, "AsyncResult", lambda task_id, app: fake_result)

    response = client.get("/documents/status/fake-task-id")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "FAILURE"
    assert "boom" in body["error"]
