from enum import Enum

from pydantic import BaseModel


class ElementType(str, Enum):
    TEXT = "text"
    TABLE = "table"
    CHART = "chart"


class ParsedElement(BaseModel):
    """One retrievable unit produced by the ingestion pipeline.

    `embedding_text` is what actually gets embedded — the chunk itself for
    text, but a generated summary/description for tables and charts, since
    embedding raw HTML or a base64 image is not useful for semantic search.
    The original content fields are kept so citations can point back to the
    real source.
    """

    element_id: str
    element_type: ElementType
    document_name: str
    page_number: int | None
    section_heading: str | None

    text: str | None = None
    table_html: str | None = None
    image_path: str | None = None

    embedding_text: str | None = None
    embedding: list[float] | None = None
