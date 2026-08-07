import re

from rank_bm25 import BM25Okapi

from app.config import settings
from app.services import vectorstore

_TOKEN_RE = re.compile(r"\w+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _fetch_corpus() -> list[tuple[str, str]]:
    """Scroll the whole Qdrant collection, returning (point_id, embedding_text)
    pairs — the same text each element was embedded with, so dense and BM25
    search the same representation.
    """
    client = vectorstore.get_client()
    vectorstore.ensure_collection()

    corpus: list[tuple[str, str]] = []
    offset = None
    while True:
        records, offset = client.scroll(
            collection_name=settings.qdrant_collection,
            limit=256,
            with_payload=["embedding_text"],
            offset=offset,
        )
        for record in records:
            text = (record.payload or {}).get("embedding_text")
            if text:
                corpus.append((str(record.id), text))
        if offset is None:
            break
    return corpus


def search(query: str, limit: int) -> list[tuple[str, float]]:
    """BM25 keyword search over every ingested element's embedding text.

    Returns (point_id, score) pairs, best match first. The index is rebuilt
    in-memory on every call — fine at demo scale (hundreds to low thousands
    of chunks), but a larger deployment would want Qdrant's native
    sparse-vector search instead of rebuilding an index per query.
    """
    corpus = _fetch_corpus()
    if not corpus:
        return []

    point_ids = [point_id for point_id, _ in corpus]
    tokenized_corpus = [_tokenize(text) for _, text in corpus]
    bm25 = BM25Okapi(tokenized_corpus)

    query_tokens = _tokenize(query)
    scores = bm25.get_scores(query_tokens)
    ranked = sorted(
        zip(point_ids, scores, tokenized_corpus, strict=True),
        key=lambda triple: triple[1],
        reverse=True,
    )

    # BM25's IDF can go negative for terms that appear in most/all of a
    # small corpus, so a document can rank low yet still score below zero —
    # filtering on the score's sign would wrongly drop real matches. Whether
    # any query token appears in the document at all is a relevance signal
    # that doesn't depend on corpus size.
    query_token_set = set(query_tokens)
    return [
        (point_id, score)
        for point_id, score, tokens in ranked[:limit]
        if query_token_set & set(tokens)
    ]
