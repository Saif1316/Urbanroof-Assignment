"""
FastAPI application entrypoint.

Run with:
    uvicorn app.main:app --reload --port 8000

This serves:
  - /api/generate-ddr, /api/download-pdf/{id}, /api/health  (see app/api/routes.py)
  - /static/*  - extracted inspection/thermal images, so the frontend (and
    the PDF renderer) can load them by URL
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import settings

app = FastAPI(
    title="Urbanroof DDR Generation API",
    description="Generates Detailed Diagnostic Reports from inspection and thermal survey PDFs.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Serve extracted images so they're reachable by URL (used by the frontend
# report view and embedded in the generated PDF).
app.mount("/static/extracted_images", StaticFiles(directory=settings.extracted_images_dir), name="extracted_images")
