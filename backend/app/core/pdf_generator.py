"""
Renders a DDRReport into HTML (for the in-browser view) or PDF (for
download), using a shared Jinja2 template so both outputs stay visually
consistent.

Uses xhtml2pdf (pure Python, built on ReportLab) instead of WeasyPrint.
This is a deliberate choice: WeasyPrint requires system-level GTK/Pango/
Cairo libraries that are notoriously difficult to install on Windows
(frequent "cannot load library" errors requiring manual MSYS2/GTK setup).
xhtml2pdf installs cleanly via pip alone on every platform, which matters
for a 24-hour build where local environment issues cost real time.
"""

from __future__ import annotations

import os
from io import BytesIO

from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

from app.models.schemas import DDRReport

_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")
_env = Environment(loader=FileSystemLoader(_TEMPLATE_DIR))


def render_report_html(report: DDRReport) -> str:
    """Renders the DDRReport into an HTML string using the shared template."""
    template = _env.get_template("ddr_report.html")
    return template.render(report=report)


def render_report_pdf(report: DDRReport) -> bytes:
    """
    Renders the DDRReport into PDF bytes.

    Image paths in the report (area.image_url) must be absolute
    filesystem paths at render time, since xhtml2pdf resolves <img src="">
    as local file paths when not given a base URL for http(s) resolution.
    """
    html_string = render_report_html(report)

    output_buffer = BytesIO()
    pisa_status = pisa.CreatePDF(
        src=html_string,
        dest=output_buffer,
    )

    if pisa_status.err:
        raise RuntimeError(f"PDF generation failed with {pisa_status.err} error(s).")

    return output_buffer.getvalue()


def save_report_pdf(report: DDRReport, output_dir: str) -> str:
    """Renders and saves the PDF to disk, returning the file path."""
    os.makedirs(output_dir, exist_ok=True)
    pdf_bytes = render_report_pdf(report)
    file_path = os.path.join(output_dir, f"{report.report_id}.pdf")
    with open(file_path, "wb") as f:
        f.write(pdf_bytes)
    return file_path
