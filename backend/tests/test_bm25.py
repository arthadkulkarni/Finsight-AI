from app.models.elements import ElementType, ParsedElement
from app.services import bm25, vectorstore


def _seed(element_id: str, text: str) -> None:
    dim = vectorstore.settings.embedding_dimensions
    element = ParsedElement(
        element_id=element_id,
        element_type=ElementType.TEXT,
        document_name="doc.pdf",
        page_number=1,
        section_heading=None,
        text=text,
        embedding_text=text,
        embedding=[0.0] * dim,
    )
    vectorstore.upsert_elements([element])


def test_bm25_ranks_matching_document_first():
    _seed(
        "11111111-1111-1111-1111-111111111111",
        "Revenue increased due to strong widget sales growth.",
    )
    _seed(
        "22222222-2222-2222-2222-222222222222",
        "The board of directors approved a new stock buyback program.",
    )

    results = bm25.search("widget sales revenue", limit=5)

    # Only one of the two seeded documents shares any vocabulary with the
    # query, so it should be the only (and therefore top) result. Small
    # corpora can legitimately produce zero or negative raw BM25 scores
    # (IDF for a term appearing in most/all documents goes negative) — rank
    # is the signal that matters, not the sign of the score.
    assert [point_id for point_id, _ in results] == ["11111111-1111-1111-1111-111111111111"]


def test_bm25_returns_empty_list_for_empty_collection():
    assert bm25.search("anything", limit=5) == []
