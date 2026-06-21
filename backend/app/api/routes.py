"""
API routes for the DDR generation system.

Endpoints (matching what the frontend's api/client.js already expects):
  POST /api/generate-ddr        - upload inspection_report + thermal_report PDFs,
                                   returns the structured DDRReport JSON
  GET  /api/download-pdf/{id}   - downloads the previously generated PDF for a report

In-memory report cache: generated reports are kept in a simple dict keyed
by report_id, so the PDF can be re-rendered or re-fetched after the
initial /generate-ddr call without re-running the whole pipeline. This is
sufficient for a single-process demo/assignment deployment; a real
production system would persist reports to a database instead.
"""

from __future__ import annotations

import os
import shutil
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response

from app.config import settings
from app.core.ddr_builder import build_ddr_report
from app.core.nlp_extractor import parse_inspection_areas, parse_thermal_readings
from app.core.pdf_extractor import extract_all
from app.core.pdf_generator import render_report_pdf
from app.models.schemas import DDRReport

router = APIRouter()

# Simple in-memory cache: report_id -> DDRReport. See module docstring.
_report_cache: dict[str, DDRReport] = {}


def _save_upload(upload: UploadFile, destination_dir: str) -> str:
    """Saves an uploaded file to disk and returns its path."""
    os.makedirs(destination_dir, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex[:8]}_{upload.filename}"
    file_path = os.path.join(destination_dir, safe_name)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(upload.file, f)
    return file_path


@router.post("/api/generate-ddr")
async def generate_ddr(
    inspection_report: UploadFile = File(...),
    thermal_report: UploadFile = File(...),
):
    """
    Accepts the two source PDFs, runs the full extraction -> parsing ->
    merging -> LLM-reasoning -> report-building pipeline, and returns the
    structured DDRReport as JSON.
    """
    if inspection_report.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="inspection_report must be a PDF file.")
    if thermal_report.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="thermal_report must be a PDF file.")

    try:
        inspection_path = _save_upload(inspection_report, settings.upload_dir)
        thermal_path = _save_upload(thermal_report, settings.upload_dir)

        inspection_blocks, inspection_images = extract_all(
            inspection_path, "inspection_report", settings.extracted_images_dir
        )
        thermal_blocks, thermal_images = extract_all(
            thermal_path, "thermal_report", settings.extracted_images_dir
        )

        findings = parse_inspection_areas(inspection_blocks)
        readings = parse_thermal_readings(thermal_blocks)

        report = build_ddr_report(
            inspection_findings=findings,
            inspection_images=inspection_images,
            thermal_readings=readings,
            thermal_images=thermal_images,
            use_llm_enhancement=True,
        )

        _report_cache[report.report_id] = report

        return report.model_dump()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/api/download-pdf/{report_id}")
async def download_pdf(report_id: str):
    """Renders and returns the PDF for a previously generated report."""
    report = _report_cache.get(report_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found. It may have expired or the server was restarted.",
        )

    try:
        pdf_bytes = render_report_pdf(report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF rendering failed: {str(e)}")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="DDR-Report-{report_id}.pdf"'},
    )


@router.get("/api/health")
async def health_check():
    """Simple health check, useful for confirming the backend is reachable."""
    return {"status": "ok"}
