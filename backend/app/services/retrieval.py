from dataclasses import dataclass

from app.clients import openai_client
from app.config import settings
from app.services import bm25, vectorstore

# Standard smoothing constant for Reciprocal Rank Fusion — large enough that
# rank 1 vs. rank 2 isn't a huge swing, small enough that being unranked
# (absent from a list) still matters.
_RRF_K = 60


@dataclass
class RetrievedChunk:
    point_id: str
    payload: dict[str, object]
    score: float


def hybrid_search(query: str, limit: int | None = None) -> list[RetrievedChunk]:
    """Dense (Qdrant) + BM25 keyword search, combined via Reciprocal Rank
    Fusion: each retriever ranks candidates independently, and a point's
    fused score is the sum of 1/(k + rank) across whichever lists it appears
    in. A point found by both retrievers naturally outranks one found by
    only one — without needing to normalize two very different score scales
    (cosine similarity vs. BM25) against each other.
    """
    query_vector = openai_client.embed_texts([query])[0]
    dense_hits = vectorstore.search(query_vector, limit=settings.dense_search_k)
    bm25_hits = bm25.search(query, limit=settings.bm25_search_k)

    fused_scores: dict[str, float] = {}
    payloads: dict[str, dict[str, object]] = {}

    for rank, point in enumerate(dense_hits):
        point_id = str(point.id)
        fused_scores[point_id] = fused_scores.get(point_id, 0.0) + 1.0 / (_RRF_K + rank + 1)
        payloads[point_id] = point.payload or {}

    for rank, (point_id, _score) in enumerate(bm25_hits):
        fused_scores[point_id] = fused_scores.get(point_id, 0.0) + 1.0 / (_RRF_K + rank + 1)

    # BM25 hits don't carry a payload (bm25.search only returns id + score) —
    # fetch payloads for any point dense search didn't already give us one for.
    missing_ids = [pid for pid in fused_scores if pid not in payloads]
    if missing_ids:
        records = vectorstore.get_client().retrieve(
            collection_name=settings.qdrant_collection, ids=missing_ids
        )
        for record in records:
            payloads[str(record.id)] = record.payload or {}

    ranked_ids = sorted(fused_scores, key=lambda pid: fused_scores[pid], reverse=True)
    result_limit = limit or settings.fused_k
    return [
        RetrievedChunk(point_id=pid, payload=payloads[pid], score=fused_scores[pid])
        for pid in ranked_ids[:result_limit]
        if pid in payloads
    ]
