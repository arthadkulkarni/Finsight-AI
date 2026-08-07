from collections.abc import Iterator
from pathlib import Path
from typing import Any

from app.clients import anthropic_client, cohere_client
from app.config import settings
from app.services.retrieval import RetrievedChunk, hybrid_search

_SYSTEM_PROMPT = (
    "You are a financial analyst assistant answering questions about SEC 10-K "
    "filings. Answer using ONLY the numbered sources provided below — do not "
    "use outside knowledge. Cite every claim with the matching bracket "
    "number(s), e.g. [1] or [1][2], placed right after the claim it supports. "
    "If the sources don't contain enough information to answer, say so plainly."
)

_NOTHING_FOUND = "I couldn't find anything relevant to that in the ingested filings."


def answer_question_stream(question: str) -> Iterator[dict[str, Any]]:
    """Retrieve -> rerank -> generate a cited answer.

    Yields SSE-ready event dicts: any number of {"type": "delta", "text": ...}
    followed by exactly one {"type": "sources", "sources": [...]}.
    """
    candidates = hybrid_search(question)
    documents = [str(c.payload.get("embedding_text", "")) for c in candidates]
    reranked = cohere_client.rerank(question, documents)

    if not reranked:
        yield {"type": "delta", "text": _NOTHING_FOUND}
        yield {"type": "sources", "sources": []}
        return

    sources = [
        _build_source(rank, candidates[index], score)
        for rank, (index, score) in enumerate(reranked, start=1)
    ]

    user_prompt = _build_prompt(question, sources)
    for chunk in anthropic_client.stream_answer(_SYSTEM_PROMPT, user_prompt):
        yield {"type": "delta", "text": chunk}

    yield {"type": "sources", "sources": sources}


def _build_source(rank: int, chunk: RetrievedChunk, score: float) -> dict[str, Any]:
    payload = chunk.payload
    element_type = payload.get("element_type")
    content = (
        payload.get("table_html")
        if element_type == "table"
        else payload.get("text") or payload.get("embedding_text")
    )

    return {
        "id": rank,
        "element_type": element_type,
        "document_name": payload.get("document_name"),
        "page_number": payload.get("page_number"),
        "section_heading": payload.get("section_heading"),
        "content": content,
        "image_url": _image_url(payload.get("image_path")),
        "relevance_score": score,
    }


def _image_url(image_path: str | None) -> str | None:
    """A source's image_path is an absolute filesystem path inside the
    container — meaningless to a browser. Convert it to the relative URL
    the /images static mount actually serves.
    """
    if not image_path:
        return None
    try:
        relative = Path(image_path).relative_to(settings.extracted_image_dir)
    except ValueError:
        return None
    return f"/images/{relative.as_posix()}"


def _build_prompt(question: str, sources: list[dict[str, Any]]) -> str:
    numbered = "\n\n".join(
        f"[{s['id']}] ({s['element_type']} — {s['section_heading'] or 'unknown section'}, "
        f"page {s['page_number']})\n{s['content']}"
        for s in sources
    )
    return f"Sources:\n\n{numbered}\n\nQuestion: {question}"
