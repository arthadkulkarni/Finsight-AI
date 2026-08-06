import pytest

from app.services import vectorstore


@pytest.fixture(autouse=True)
def isolated_qdrant(tmp_path, monkeypatch):
    """Point every test at a fresh, temporary Qdrant (local embedded mode)
    instead of the real backend/data/qdrant/ directory, so tests never share
    state with each other or with a real ingestion run.
    """
    monkeypatch.setattr(vectorstore.settings, "qdrant_path", tmp_path / "qdrant")
    monkeypatch.setattr(vectorstore.settings, "qdrant_collection", "test_filings")
    vectorstore._client = None
    yield
    vectorstore._client = None
