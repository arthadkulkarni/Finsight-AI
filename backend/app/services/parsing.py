from pathlib import Path

from unstructured.chunking.title import chunk_by_title
from unstructured.documents.elements import Element
from unstructured.partition.pdf import partition_pdf

from app.config import settings
from app.models.elements import ElementType, ParsedElement

# Running headers/footers and page breaks are boilerplate, not retrievable
# content — everything else that isn't a Table or Image is treated as text.
_NON_TEXT_CATEGORIES = {"Header", "Footer", "PageBreak"}


def parse_pdf(file_path: str | Path, document_name: str) -> list[ParsedElement]:
    """Partition a PDF into text/table/chart elements.

    `strategy="hi_res"` is what actually detects table regions and extracts
    embedded chart images — the cheaper `fast` strategy only does raw text
    extraction and would give us neither.
    """
    image_output_dir = settings.extracted_image_dir / document_name
    image_output_dir.mkdir(parents=True, exist_ok=True)

    raw_elements = partition_pdf(
        filename=str(file_path),
        strategy="hi_res",
        infer_table_structure=True,
        extract_image_block_types=["Image"],
        extract_image_block_output_dir=str(image_output_dir),
    )

    parsed: list[ParsedElement] = []
    text_elements: list[Element] = []

    for element in raw_elements:
        if element.category == "Table":
            parsed.append(
                ParsedElement(
                    element_id=element.id,
                    element_type=ElementType.TABLE,
                    document_name=document_name,
                    page_number=element.metadata.page_number,
                    section_heading=None,  # filled in during the text pass below
                    table_html=element.metadata.text_as_html,
                    text=element.text,
                )
            )
        elif element.category == "Image":
            parsed.append(
                ParsedElement(
                    element_id=element.id,
                    element_type=ElementType.CHART,
                    document_name=document_name,
                    page_number=element.metadata.page_number,
                    section_heading=None,
                    image_path=element.metadata.image_path,
                )
            )
        elif element.category not in _NON_TEXT_CATEGORIES:
            text_elements.append(element)

    parsed.extend(_chunk_text_elements(text_elements, document_name))
    _backfill_section_headings(parsed, raw_elements)
    return parsed


def _chunk_text_elements(text_elements: list[Element], document_name: str) -> list[ParsedElement]:
    """Group text elements into section-aware chunks.

    chunk_by_title breaks a new chunk at every Title element, which is
    exactly the section-boundary behavior we want. combine_text_under_n_chars
    folds a short section heading into the chunk that follows it instead of
    emitting a near-empty chunk. include_orig_elements lets us recover which
    Title (if any) started each chunk, for section-heading tracking.
    """
    chunks = chunk_by_title(
        text_elements,
        combine_text_under_n_chars=200,
        max_characters=1500,
        include_orig_elements=True,
    )

    result: list[ParsedElement] = []
    current_section: str | None = None
    for chunk in chunks:
        orig_elements = chunk.metadata.orig_elements or []
        titles_in_chunk = [e.text for e in orig_elements if e.category == "Title"]
        if titles_in_chunk:
            current_section = titles_in_chunk[-1]

        result.append(
            ParsedElement(
                element_id=chunk.id,
                element_type=ElementType.TEXT,
                document_name=document_name,
                page_number=chunk.metadata.page_number,
                section_heading=current_section,
                text=chunk.text,
            )
        )
    return result


def _backfill_section_headings(
    parsed: list[ParsedElement], raw_elements: list[Element]
) -> None:
    """Tables and charts don't go through chunk_by_title, so they never get a
    section_heading from that pass — derive it here from the nearest
    preceding Title in the original, ordered element stream.
    """
    section_by_element_id: dict[str, str] = {}
    current_section: str | None = None
    for element in raw_elements:
        if element.category == "Title":
            current_section = element.text
        elif element.category in ("Table", "Image") and current_section is not None:
            section_by_element_id[element.id] = current_section

    for item in parsed:
        if item.element_type in (ElementType.TABLE, ElementType.CHART):
            item.section_heading = section_by_element_id.get(item.element_id)
