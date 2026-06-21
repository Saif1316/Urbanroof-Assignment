"""
Pydantic models defining the DDR (Detailed Diagnostic Report) structure.

These schemas enforce the assignment's required 7 sections and the
"Not Available" / conflict-handling rules at the data layer, so a report
can never silently drop a required field.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


NOT_AVAILABLE = "Not Available"


class AreaObservation(BaseModel):
    """A single area-wise observation, combining inspection + thermal data."""

    area_name: str = Field(default=NOT_AVAILABLE)
    observation: str = Field(default=NOT_AVAILABLE)
    probable_root_cause: str = Field(default=NOT_AVAILABLE)
    severity: str = Field(default=NOT_AVAILABLE)  # High | Medium | Low | Not Available
    severity_reasoning: str = Field(default=NOT_AVAILABLE)
    recommended_action: str = Field(default=NOT_AVAILABLE)

    image_url: Optional[str] = Field(default=None)
    image_caption: Optional[str] = Field(default=None)

    source_documents: list[str] = Field(default_factory=list)
    has_conflict: bool = Field(default=False)
    conflict_note: Optional[str] = Field(default=None)


class DDRReport(BaseModel):
    """
    The full Detailed Diagnostic Report:
      1. Property Issue Summary
      2. Area-wise Observations
      3. Probable Root Cause          (per AreaObservation)
      4. Severity Assessment          (per-area + overall)
      5. Recommended Actions
      6. Additional Notes
      7. Missing or Unclear Information
    """

    report_id: str
    property_issue_summary: str = Field(default=NOT_AVAILABLE)
    area_observations: list[AreaObservation] = Field(default_factory=list)

    overall_severity: str = Field(default=NOT_AVAILABLE)
    overall_severity_reasoning: str = Field(default=NOT_AVAILABLE)

    recommended_actions: list[str] = Field(default_factory=list)
    additional_notes: str = Field(default=NOT_AVAILABLE)
    missing_or_unclear_information: list[str] = Field(default_factory=list)


class ExtractedTextBlock(BaseModel):
    """One chunk of text extracted from a source PDF, with page reference."""

    source_document: str  # "inspection_report" | "thermal_report"
    page_number: int
    text: str


class ExtractedImage(BaseModel):
    """One image extracted from a source PDF."""

    source_document: str
    page_number: int
    file_path: str
    caption_guess: Optional[str] = None
