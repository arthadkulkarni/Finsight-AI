"""Download a real, public SEC 10-K filing and turn it into a small test PDF.

SEC EDGAR filings are HTML/iXBRL, not PDF, so there's no PDF to just
download directly — this fetches the real primary document, renders it to
PDF with weasyprint (`brew install weasyprint`), and truncates it to the
first N pages to keep hi_res parsing fast for local runs and CI.

Filing chosen: theglobe.com, inc. FY2022 Form 10-K (CIK 0001066684,
accession 0001410578-23-000361) — a real, small filer whose 10-K still has
genuine risk-factor text and full financial statements (balance sheet,
statements of operations) within the first 25 pages.

The output (backend/tests/fixtures/sample_10k.pdf) is small enough to be
committed to git directly, so CI doesn't need network access or weasyprint
installed just to run the parsing tests. Re-run this script only if you want
to regenerate or swap out the fixture.

Usage:
    python backend/scripts/fetch_sample_filing.py
"""

import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

import pypdf

FILING_URL = (
    "https://www.sec.gov/Archives/edgar/data/1066684/000141057823000361/"
    "tglo-20221231x10k.htm"
)
# SEC requires a descriptive User-Agent identifying the requester.
USER_AGENT = "FinSight-AI sample-fixture-fetch (contact: set-your-email-here)"

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"
HTML_PATH = FIXTURES_DIR / "_sample_10k_source.htm"
OUTPUT_PATH = FIXTURES_DIR / "sample_10k.pdf"
MAX_PAGES = 25


def main() -> None:
    if shutil.which("weasyprint") is None:
        print(
            "weasyprint is required to render the filing to PDF.\n"
            "Install it with: brew install weasyprint",
            file=sys.stderr,
        )
        sys.exit(1)

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {FILING_URL}")
    request = urllib.request.Request(FILING_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request) as response:  # noqa: S310 - fixed, trusted URL
        HTML_PATH.write_bytes(response.read())

    full_pdf_path = FIXTURES_DIR / "_sample_10k_full.pdf"
    print("Rendering to PDF with weasyprint...")
    subprocess.run(
        ["weasyprint", str(HTML_PATH), str(full_pdf_path)],
        check=True,
    )

    reader = pypdf.PdfReader(str(full_pdf_path))
    writer = pypdf.PdfWriter()
    for page in reader.pages[:MAX_PAGES]:
        writer.add_page(page)
    with OUTPUT_PATH.open("wb") as f:
        writer.write(f)

    HTML_PATH.unlink()
    full_pdf_path.unlink()

    print(f"Wrote {OUTPUT_PATH} ({len(writer.pages)} pages)")


if __name__ == "__main__":
    main()
