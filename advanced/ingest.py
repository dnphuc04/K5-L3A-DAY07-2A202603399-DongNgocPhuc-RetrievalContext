"""Index every page, including diagram text; retain on-demand original page renders."""
import argparse
from datetime import datetime, timezone
import logging
import re
import subprocess
import threading
import urllib.request
from pypdf import PdfReader
from .common import BASE, LOCAL, PDF, SOURCE_URL, SOURCE_SHA, check_pdf, read, sha, write

RENDER_LOCK = threading.Lock()

def render(page, size=1800):
    check_pdf()
    if type(page) is not int or not 1 <= page <= 297:
        raise ValueError("Physical PDF page must be 1..297")
    output = LOCAL / "pages" / f"p{page:04d}_{size}"
    output.parent.mkdir(parents=True, exist_ok=True)
    png = output.with_suffix(".png")
    with RENDER_LOCK:
        if not png.exists():
            temporary = output.with_name(output.name + "_pending")
            subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-scale-to", str(size),
                            "-singlefile", "-png", str(PDF), str(temporary)],
                           check=True, capture_output=True, timeout=90)
            temporary.with_suffix(".png").replace(png)
    return png

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--download", action="store_true")
    args = p.parse_args()
    if args.download and not PDF.exists():
        LOCAL.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(SOURCE_URL, timeout=90) as r:
            PDF.write_bytes(r.read())
    check_pdf()
    reader = PdfReader(PDF)
    if len(reader.pages) != 297:
        raise ValueError("Unexpected source edition")
    pages, failures, warnings = [], [], []
    class WarningCapture(logging.Handler):
        def emit(self, record):
            message = record.getMessage()
            category = "fontTools missing: some CFF Type1 encodings may be incomplete" if "fontTools" in message else (
                "Rotated text: native extraction may omit labels" if "Rotated text" in message else "Other pypdf extraction warning")
            if {"page": number, "category": category} not in warnings:
                warnings.append({"page": number, "category": category})
    logger = logging.getLogger("pypdf")
    capture = WarningCapture()
    logger.addHandler(capture)
    logger.propagate = False
    for number, page in enumerate(reader.pages, 1):
        try:
            text = page.extract_text(extraction_mode="layout") or ""
            text = re.sub(r"[ \t]+", " ", text)
            error = None
        except Exception as exc:
            text, error = "", type(exc).__name__
            failures.append({"page": number, "error": error})
        # Full-page region is an honest locator; no fabricated figure bounding boxes.
        pages.append({"id": f"NASA-SE:p{number:04d}", "page": number,
            "printed_page": number - 10 if number >= 11 else None,
            "source": SOURCE_URL, "bbox": [0, 0, 1, 1], "text": text,
            "metadata": {"page": number}, "extraction_error": error,
            "render": f"data/local/advanced/pages/p{number:04d}_1800.png"})
    write(LOCAL / "index.json", pages)
    manifest = {"title": "NASA Systems Engineering Handbook",
        "edition": "NASA/SP-2016-6105 Rev 2", "source_url": SOURCE_URL,
        "landing_url": "https://www.nasa.gov/reference/systems-engineering-handbook/",
        "sha256": SOURCE_SHA, "pdf_pages": 297, "printed_page_offset": 10,
        "rights_url": "https://www.nasa.gov/nasa-brand-center/images-and-media/",
        "distribution": "Original PDF and renders local only; download from NASA. Retain third-party credits, including INCOSE on Figure 2.5-1.",
        "method": "pypdf layout text on ALL pages + searchable page-level BM25 + model-selected original page vision via Poppler",
        "image_coverage": "Every page is addressable/renderable, including vector diagrams; no benchmark-page allowlist. Images without searchable captions may require navigation from neighboring text.",
        "limitations": "No OCR for scanned-only pages; native diagram labels may lose relationships. Vision reads original when requested. Extraction is not ground truth.",
        "coverage": {"indexed_pages": len(pages), "text_characters": sum(len(p['text']) for p in pages),
            "warnings": warnings, "warning_impact": "Native text may lose labels/rotation; whole original page remains renderable and is required before cited answers. No OCR correction was silently assumed.",
            "empty_text_pages": [p['page'] for p in pages if not p['text'].strip()], "failures": failures},
        "index_sha256": sha(LOCAL / "index.json"), "created_at": datetime.now(timezone.utc).isoformat()}
    source_manifest=BASE/'source.json'
    if source_manifest.exists():
        existing=read(source_manifest)
        if existing['index_sha256']!=manifest['index_sha256'] or existing['sha256']!=SOURCE_SHA:
            raise ValueError('Rebuilt index differs from recorded source manifest; do not overwrite frozen provenance')
    else:
        write(source_manifest,manifest)
    logger.removeHandler(capture)
    logger.propagate = True
    print("Indexed", len(pages), "pages; failures", len(failures), "; warning pages", len({w['page'] for w in warnings}))

if __name__ == "__main__":
    main()
