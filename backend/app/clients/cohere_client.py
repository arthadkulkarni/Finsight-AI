import cohere

from app.config import settings

_client: cohere.ClientV2 | None = None


def _get_client() -> cohere.ClientV2:
    global _client
    if _client is None:
        if not settings.cohere_api_key:
            raise RuntimeError(
                "COHERE_API_KEY is not set. Add it to backend/.env to enable reranking."
            )
        _client = cohere.ClientV2(api_key=settings.cohere_api_key)
    return _client


def rerank(query: str, documents: list[str], top_n: int | None = None) -> list[tuple[int, float]]:
    """Rerank `documents` against `query`.

    Returns (original_index, relevance_score) pairs, best match first — the
    original_index lets the caller map back to the source object each string
    came from.
    """
    if not documents:
        return []

    response = _get_client().rerank(
        model=settings.cohere_rerank_model,
        query=query,
        documents=documents,
        top_n=top_n or settings.rerank_top_n,
    )
    return [(result.index, result.relevance_score) for result in response.results]
