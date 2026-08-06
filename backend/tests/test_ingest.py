from app.models.elements import ElementType, ParsedElement
from app.services import ingest, vectorstore


def _fake_elements() -> list[ParsedElement]:
    return [
        ParsedElement(
            element_id="11111111-1111-1111-1111-111111111111",
            element_type=ElementType.TEXT,
            document_name="sample.pdf",
            page_number=1,
            section_heading="Item 1. Business",
            text="The company sells widgets.",
        ),
        ParsedElement(
            element_id="22222222-2222-2222-2222-222222222222",
            element_type=ElementType.TABLE,
            document_name="sample.pdf",
            page_number=2,
            section_heading="Item 8. Financial Statements",
            table_html="<table><tr><td>Revenue</td><td>100</td></tr></table>",
        ),
        ParsedElement(
            element_id="33333333-3333-3333-3333-333333333333",
            element_type=ElementType.CHART,
            document_name="sample.pdf",
            page_number=3,
            section_heading="Item 7. MD&A",
            image_path="/tmp/does-not-need-to-exist.png",
        ),
    ]


def test_ingest_routes_each_element_type_and_stores_vectors(monkeypatch):
    dim = vectorstore.settings.embedding_dimensions
    monkeypatch.setattr(ingest, "parse_pdf", lambda path, document_name: _fake_elements())
    monkeypatch.setattr(
        ingest.openai_client, "embed_texts", lambda texts: [[0.1] * dim for _ in texts]
    )
    monkeypatch.setattr(
        ingest.anthropic_client, "summarize_table", lambda html: "Revenue was 100."
    )
    monkeypatch.setattr(
        ingest.anthropic_client, "describe_chart", lambda path: "A bar chart of revenue."
    )

    result = ingest.ingest_pdf("unused/path.pdf", document_name="sample.pdf")

    assert result.document_name == "sample.pdf"
    assert result.num_text_chunks == 1
    assert result.num_tables == 1
    assert result.num_charts == 1

    stored = vectorstore.search([0.1] * dim, limit=10)
    assert len(stored) == 3
    element_types = {point.payload["element_type"] for point in stored}
    assert element_types == {"text", "table", "chart"}


def test_ingest_skips_chart_without_an_image_path(monkeypatch):
    dim = vectorstore.settings.embedding_dimensions
    chart_without_image = ParsedElement(
        element_id="66666666-6666-6666-6666-666666666666",
        element_type=ElementType.CHART,
        document_name="sample.pdf",
        page_number=1,
        section_heading=None,
        image_path=None,
    )
    monkeypatch.setattr(
        ingest, "parse_pdf", lambda path, document_name: [chart_without_image]
    )
    monkeypatch.setattr(
        ingest.openai_client, "embed_texts", lambda texts: [[0.1] * dim] * len(texts)
    )

    called = False

    def _fail_if_called(path: str) -> str:
        nonlocal called
        called = True
        return "should not be reached"

    monkeypatch.setattr(ingest.anthropic_client, "describe_chart", _fail_if_called)

    result = ingest.ingest_pdf("unused/path.pdf", document_name="sample.pdf")

    assert called is False
    assert result.num_charts == 1
    assert vectorstore.search([0.1] * dim, limit=10) == []
