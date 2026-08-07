from types import SimpleNamespace

from app.services import retrieval


def test_hybrid_search_fuses_dense_and_bm25_rankings(monkeypatch):
    dense_hits = [
        SimpleNamespace(id="a", payload={"embedding_text": "a text"}, score=0.9),
        SimpleNamespace(id="b", payload={"embedding_text": "b text"}, score=0.8),
    ]
    bm25_hits = [("b", 5.0), ("c", 3.0)]

    monkeypatch.setattr(retrieval.openai_client, "embed_texts", lambda texts: [[0.1] * 3])
    monkeypatch.setattr(retrieval.vectorstore, "search", lambda vector, limit: dense_hits)
    monkeypatch.setattr(retrieval.bm25, "search", lambda query, limit: bm25_hits)
    monkeypatch.setattr(
        retrieval.vectorstore,
        "get_client",
        lambda: SimpleNamespace(
            retrieve=lambda collection_name, ids: [
                SimpleNamespace(id="c", payload={"embedding_text": "c text"})
            ]
        ),
    )

    results = retrieval.hybrid_search("query", limit=10)

    # "b" appears in both the dense and BM25 lists, so RRF should rank it first.
    assert results[0].point_id == "b"
    assert {r.point_id for r in results} == {"a", "b", "c"}


def test_hybrid_search_returns_empty_when_nothing_found(monkeypatch):
    monkeypatch.setattr(retrieval.openai_client, "embed_texts", lambda texts: [[0.1] * 3])
    monkeypatch.setattr(retrieval.vectorstore, "search", lambda vector, limit: [])
    monkeypatch.setattr(retrieval.bm25, "search", lambda query, limit: [])

    assert retrieval.hybrid_search("query") == []
