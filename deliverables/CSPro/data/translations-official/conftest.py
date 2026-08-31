"""Shared pytest fixtures/helpers for the Aug-21 translation tooling tests.

`make_pdf()` lives here (and ONLY here) so every test file in this folder builds
its synthetic paper the same way — the extractor and the English-delta gate both
read real PDFs through PyMuPDF, and two drifting copies of the generator would
let one tool's tests pass on text the other tool could never see.

pytest inserts this directory on sys.path (no __init__.py, prepend import mode),
so test files use `from conftest import make_pdf`.
"""
import fitz


def make_pdf(path, lines):
    """Write a PDF at `path`, one line of `lines` per text row.

    A line placed below the page rect is not rendered and never comes back out of
    get_text(), so the helper starts a new page instead: a consent-page fixture is ~50
    wrapped lines and would otherwise lose its tail silently, which reads in a test as an
    extractor that "cannot find" text the extractor was never shown.
    """
    doc = fitz.open()
    page = doc.new_page()
    y = 60
    for ln in lines:
        if y > 780:
            page = doc.new_page()
            y = 60
        page.insert_text((40, y), ln, fontsize=9)
        y += 14
    doc.save(str(path))
    doc.close()
