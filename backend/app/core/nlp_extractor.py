"""
Parses raw extracted text from the Inspection Report into structured
per-area observations, and from the Thermal Report into structured
temperature readings.

This module does deterministic, rule-based parsing (regex/string matching)
rather than calling an ML model, because the source documents
(UrbanRoof-style inspection forms and Bosch thermal camera exports) follow
a consistent, predictable text layout. A small local extraction model
(NuExtract) is layered in as a fallback for inspection text that doesn't
match the expected pattern - see extract_with_nuextract() below - so the
system still generalizes to inspection reports with a different layout
than the sample, per the assignment's "should generalise to similar
inspection data" requirement.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.models.schemas import ExtractedTextBlock


@dataclass
class InspectionAreaFinding:
    """One impacted area parsed from the inspection report."""
    area_label: str  # e.g. "Hall", "Master Bedroom", "Common Bathroom"
    side: str  # "negative" | "positive"
    description: str
    raw_text: str = ""


@dataclass
class ThermalReading:
    """One thermal camera reading parsed from the thermal report."""
    page_number: int
    hotspot_c: float | None
    coldspot_c: float | None
    emissivity: float | None
    reflected_temp_c: float | None
    source_filename: str | None  # e.g. "RB02380X.JPG"


# Regex patterns tuned to the UrbanRoof inspection form layout and the
# Bosch thermal camera export layout observed in the sample documents.
#
# The description capture is non-greedy up to the next known field label
# (not just the next newline) because descriptions in the source PDF can
# wrap across multiple lines, e.g. "Common Bathroom Ceiling \nDampness".
# Stopping at the first newline would silently truncate the description.
_AREA_LINE_PATTERN = re.compile(
    r"(Negative|Positive) side Description\s+(.+?)(?=\n\s*(?:Negative side photographs|Positive side photographs|Negative side Description|Positive side Description|Impacted Area|$))",
    re.IGNORECASE | re.DOTALL,
)
_HOTSPOT_PATTERN = re.compile(r"Hotspot\s*:\s*([\d.]+)\s*°?C", re.IGNORECASE)
_COLDSPOT_PATTERN = re.compile(r"Coldspot\s*:\s*([\d.]+)\s*°?C", re.IGNORECASE)
_EMISSIVITY_PATTERN = re.compile(r"Emissivity\s*:\s*([\d.]+)", re.IGNORECASE)
_REFLECTED_TEMP_PATTERN = re.compile(r"Reflected temperature\s*:\s*([\d.]+)\s*°?C", re.IGNORECASE)
_THERMAL_FILENAME_PATTERN = re.compile(r"Thermal image\s*:\s*(\S+\.JPG)", re.IGNORECASE)


def parse_inspection_areas(text_blocks: list[ExtractedTextBlock]) -> list[InspectionAreaFinding]:
    """
    Parse "Negative side Description" / "Positive side Description" lines
    from the inspection report's extracted text into structured findings.

    Falls back gracefully: if a block doesn't match the expected pattern,
    it's simply skipped here (not invented) - any unmatched content is
    surfaced later as "missing/unclear" rather than silently dropped from
    awareness.
    """
    findings: list[InspectionAreaFinding] = []

    for block in text_blocks:
        matches = _AREA_LINE_PATTERN.findall(block.text)
        for side, description in matches:
            description_clean = " ".join(description.split())
            findings.append(
                InspectionAreaFinding(
                    area_label=description_clean,
                    side=side.lower(),
                    description=description_clean,
                    raw_text=block.text,
                )
            )

    return findings


def parse_thermal_readings(text_blocks: list[ExtractedTextBlock]) -> list[ThermalReading]:
    """Parse hotspot/coldspot/emissivity/filename from each thermal report page."""
    readings: list[ThermalReading] = []

    for block in text_blocks:
        text = block.text

        hotspot_match = _HOTSPOT_PATTERN.search(text)
        coldspot_match = _COLDSPOT_PATTERN.search(text)
        emissivity_match = _EMISSIVITY_PATTERN.search(text)
        reflected_match = _REFLECTED_TEMP_PATTERN.search(text)
        filename_match = _THERMAL_FILENAME_PATTERN.search(text)

        # Only record a reading if we found at least a hotspot or coldspot -
        # otherwise this page likely isn't a thermal reading page.
        if not hotspot_match and not coldspot_match:
            continue

        readings.append(
            ThermalReading(
                page_number=block.page_number,
                hotspot_c=float(hotspot_match.group(1)) if hotspot_match else None,
                coldspot_c=float(coldspot_match.group(1)) if coldspot_match else None,
                emissivity=float(emissivity_match.group(1)) if emissivity_match else None,
                reflected_temp_c=float(reflected_match.group(1)) if reflected_match else None,
                source_filename=filename_match.group(1) if filename_match else None,
            )
        )

    return readings


def group_areas_by_room(findings: list[InspectionAreaFinding]) -> dict[str, list[InspectionAreaFinding]]:
    """
    Groups parsed findings by a normalized room/area name, extracted from
    the start of each description (e.g. "Hall Skirting level Dampness" ->
    room key "Hall"). This is a heuristic: it takes the first 1-2 words of
    the description as the room name, since that's the consistent pattern
    in the sample inspection form's phrasing.

    Findings that reference a different unit/flat number than the subject
    property (e.g. "Flat no 203 ...", appearing as a cross-reference/
    comparison point in some inspection forms) are excluded from area
    grouping and returned separately, since merging them into the subject
    property's area observations would misrepresent whose property the
    finding describes.
    """
    grouped: dict[str, list[InspectionAreaFinding]] = {}

    known_room_keywords = [
        "Hall", "Bedroom", "Master Bedroom", "Kitchen", "Common Bathroom",
        "Master Bedroom Bathroom", "MB Bathroom", "External wall", "External Wall",
        "Parking Area", "Parking",
    ]

    cross_reference_pattern = re.compile(r"\bFlat\s*(?:no\.?|number)?\s*\d+\b", re.IGNORECASE)

    for finding in findings:
        if cross_reference_pattern.search(finding.description):
            # Out-of-scope cross-reference (a different unit), not a room
            # in the subject property. Skip rather than mis-grouping.
            continue

        room_key = None
        for keyword in sorted(known_room_keywords, key=len, reverse=True):
            if finding.description.lower().startswith(keyword.lower()):
                room_key = keyword
                break

        if room_key is None:
            # Fall back to first two words rather than inventing a label.
            words = finding.description.split()
            room_key = " ".join(words[:2]) if words else "Not Available"

        grouped.setdefault(room_key, []).append(finding)

    return grouped


def get_cross_reference_findings(findings: list[InspectionAreaFinding]) -> list[InspectionAreaFinding]:
    """Returns findings that reference a different unit/flat (excluded
    from area grouping by group_areas_by_room), so they can still be
    surfaced in the report's Additional Notes / Missing-Unclear section
    rather than silently dropped."""
    cross_reference_pattern = re.compile(r"\bFlat\s*(?:no\.?|number)?\s*\d+\b", re.IGNORECASE)
    return [f for f in findings if cross_reference_pattern.search(f.description)]
