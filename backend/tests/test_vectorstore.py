from app.models.elements import ElementType, ParsedElement
from app.services import vectorstore


def test_ensure_collection_is_idempotent():
    vectorstore.ensure_collection()
    assert vectorstore.get_client().collection_exists(vectorstore.settings.qdrant_collection)
    vectorstore.ensure_collection()  # must not raise on a second call


def test_upsert_and_search_round_trip():
    dim = vectorstore.settings.embedding_dimensions
    element = ParsedElement(
        element_id="44444444-4444-4444-4444-444444444444",
        element_type=ElementType.TEXT,
        document_name="doc.pdf",
        page_number=1,
        section_heading="Intro",
        text="hello world",
        embedding=[0.5] * dim,
    )

    stored_count = vectorstore.upsert_elements([element])
    assert stored_count == 1

    results = vectorstore.search([0.5] * dim, limit=5)
    assert len(results) == 1
    assert results[0].payload["document_name"] == "doc.pdf"
    assert results[0].payload["section_heading"] == "Intro"
    assert results[0].payload["element_type"] == "text"


def test_upsert_skips_elements_without_an_embedding():
    element = ParsedElement(
        element_id="55555555-5555-5555-5555-555555555555",
        element_type=ElementType.TEXT,
        document_name="doc.pdf",
        page_number=1,
        section_heading=None,
        text="never embedded",
    )

    stored_count = vectorstore.upsert_elements([element])
    assert stored_count == 0
