from dataclasses import dataclass

from app.clients import anthropic_client, openai_client
from app.models.elements import ElementType, ParsedElement
from app.services import vectorstore
from app.services.parsing import parse_pdf


@dataclass
class IngestResult:
    document_name: str
    num_text_chunks: int
    num_tables: int
    num_charts: int


def ingest_pdf(file_path: str, document_name: str) -> IngestResult:
    """Parse a PDF, route each element to the right embedding strategy, and
    store the results in Qdrant.

    Runs synchronously — the upload endpoint blocks until this returns. A
    later phase wraps this in a Celery task so uploads don't block on
    parsing + embedding; the logic here doesn't change.
    """
    elements = parse_pdf(file_path, document_name)

    text_elements = [e for e in elements if e.element_type == ElementType.TEXT]
    table_elements = [e for e in elements if e.element_type == ElementType.TABLE]
    chart_elements = [e for e in elements if e.element_type == ElementType.CHART]

    # Text embeds directly. Tables and charts are summarized/described into
    # natural language first — embedding raw HTML or an image is not useful
    # for semantic search, but a plain-English description of what's in them is.
    for element in text_elements:
        element.embedding_text = element.text

    for element in table_elements:
        element.embedding_text = anthropic_client.summarize_table(
            element.table_html or element.text or ""
        )

    for element in chart_elements:
        if element.image_path:
            element.embedding_text = anthropic_client.describe_chart(element.image_path)

    _embed_in_place(elements)
    vectorstore.upsert_elements(elements)

    return IngestResult(
        document_name=document_name,
        num_text_chunks=len(text_elements),
        num_tables=len(table_elements),
        num_charts=len(chart_elements),
    )


def _embed_in_place(elements: list[ParsedElement]) -> None:
    embeddable = [e for e in elements if e.embedding_text]
    if not embeddable:
        return
    vectors = openai_client.embed_texts([e.embedding_text for e in embeddable])
    for element, vector in zip(embeddable, vectors, strict=True):
        element.embedding = vector
