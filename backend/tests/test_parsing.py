from pathlib import Path

import pytest

from app.models.elements import ElementType
from app.services.parsing import parse_pdf

FIXTURE = Path(__file__).parent / "fixtures" / "sample_10k.pdf"


@pytest.mark.skipif(
    not FIXTURE.exists(),
    reason="run `python backend/scripts/fetch_sample_filing.py` to generate the fixture",
)
def test_parse_pdf_extracts_text_and_tables():
    """Real parse of a real (truncated) SEC 10-K — no API key needed since
    parsing is pure local inference. Takes roughly a minute or two: hi_res
    parsing runs a layout-detection model over every page.
    """
    elements = parse_pdf(FIXTURE, document_name="sample_10k.pdf")

    assert elements, "expected at least one parsed element"

    text_elements = [e for e in elements if e.element_type == ElementType.TEXT]
    table_elements = [e for e in elements if e.element_type == ElementType.TABLE]

    assert text_elements, "expected at least one text chunk"
    assert table_elements, "expected at least one table (this filing has financial statements)"

    assert all(e.text for e in text_elements)
    assert all(e.document_name == "sample_10k.pdf" for e in elements)
    # Past the cover page, chunks should carry a section heading derived
    # from the nearest preceding Title element.
    assert any(e.section_heading for e in text_elements)
