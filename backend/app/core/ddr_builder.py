"""
Assembles the final DDRReport object from the outputs of pdf_extractor,
nlp_extractor, merger, and reasoning_engine.

This is the one place where the report's 7 required sections are stitched
together, including the explicit "Missing or Unclear Information" entries
that document real limitations in the source data (e.g. the thermal
report's lack of area labels - see merger.py for the full rationale).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.merger import build_area_observations, build_thermal_findings_summary
from app.core.nlp_extractor import (
    InspectionAreaFinding,
    ThermalReading,
    get_cross_reference_findings,
)
from app.core.reasoning_engine import enhance_all_area_observations, generate_property_issue_summary
from app.models.schemas import AreaObservation, DDRReport, ExtractedImage, NOT_AVAILABLE


def _compute_overall_severity(areas: list[AreaObservation]) -> tuple[str, str]:
    """
    Overall severity is the highest severity found across all areas
    (High > Medium > Low > Not Available), with reasoning naming which
    areas drove that classification.
    """
    severity_rank = {"High": 3, "Medium": 2, "Low": 1, "Not Available": 0}

    areas_with_severity = [a for a in areas if a.severity in severity_rank]
    if not areas_with_severity:
        return NOT_AVAILABLE, NOT_AVAILABLE

    highest_rank = max(severity_rank[a.severity] for a in areas_with_severity)
    if highest_rank == 0:
        return NOT_AVAILABLE, NOT_AVAILABLE

    top_severity = [s for s, r in severity_rank.items() if r == highest_rank][0]
    driving_areas = [a.area_name for a in areas_with_severity if a.severity == top_severity]

    reasoning = (
        f"Overall severity is rated {top_severity} based on findings in: "
        f"{', '.join(driving_areas)}."
    )
    return top_severity, reasoning


def _collect_recommended_actions(areas: list[AreaObservation]) -> list[str]:
    """Deduplicates recommended actions across areas into a single list,
    prefixed with the area name for clarity."""
    actions = []
    seen_action_texts = set()

    for area in areas:
        if area.recommended_action and area.recommended_action != NOT_AVAILABLE:
            if area.recommended_action not in seen_action_texts:
                actions.append(f"{area.area_name}: {area.recommended_action}")
                seen_action_texts.add(area.recommended_action)

    return actions if actions else []


def _build_missing_info_notes(
    cross_reference_findings: list[InspectionAreaFinding],
    thermal_readings: list[ThermalReading],
    areas: list[AreaObservation],
) -> list[str]:
    """
    Builds the explicit "Missing or Unclear Information" list. This is
    where the thermal/area-mapping limitation (agreed design decision) is
    documented, along with any other genuine gaps found during parsing.
    """
    notes = []

    if thermal_readings:
        notes.append(
            f"The thermal report contains {len(thermal_readings)} temperature reading(s) "
            f"with associated images, but does not label which room or area each reading "
            f"corresponds to. These readings are included in the 'Thermal Survey Findings' "
            f"section below as supporting data, but could not be confidently matched to a "
            f"specific area without that information being present in the source document."
        )

    areas_missing_images = [a.area_name for a in areas if a.image_url is None]
    if areas_missing_images:
        notes.append(
            f"No matching photo was found for the following area(s): "
            f"{', '.join(areas_missing_images)}. Marked as 'Image Not Available'."
        )

    areas_missing_severity = [a.area_name for a in areas if a.severity == NOT_AVAILABLE]
    if areas_missing_severity:
        notes.append(
            f"Severity could not be determined from the available text for: "
            f"{', '.join(areas_missing_severity)}. The source description did not contain "
            f"enough detail to classify urgency."
        )

    if cross_reference_findings:
        descriptions = [f.description for f in cross_reference_findings]
        notes.append(
            f"The inspection report referenced findings in a different unit "
            f"({'; '.join(descriptions)}), which appears to be a comparison point rather "
            f"than part of the subject property. This was excluded from the area-wise "
            f"observations above to avoid misattributing it to the inspected property."
        )

    return notes


def build_ddr_report(
    inspection_findings: list[InspectionAreaFinding],
    inspection_images: list[ExtractedImage],
    thermal_readings: list[ThermalReading],
    thermal_images: list[ExtractedImage],
    use_llm_enhancement: bool = True,
) -> DDRReport:
    """
    Main entry point: builds the complete DDRReport from parsed inspection
    and thermal data.
    """
    areas = build_area_observations(inspection_findings, inspection_images)

    if use_llm_enhancement:
        areas = enhance_all_area_observations(areas)

    overall_severity, overall_severity_reasoning = _compute_overall_severity(areas)
    recommended_actions = _collect_recommended_actions(areas)

    thermal_summary = build_thermal_findings_summary(thermal_readings, thermal_images)
    cross_reference_findings = get_cross_reference_findings(inspection_findings)
    missing_info_notes = _build_missing_info_notes(cross_reference_findings, thermal_readings, areas)

    if use_llm_enhancement:
        property_issue_summary = generate_property_issue_summary(areas)
    else:
        property_issue_summary = (
            f"The inspection identified {len(areas)} affected area(s) in the property. "
            f"See area-wise observations below for details."
        )

    additional_notes_parts = []
    if thermal_summary["readings_count"] > 0:
        additional_notes_parts.append(
            f"Thermal Survey Findings (Area Not Specified in Source Data): "
            f"{thermal_summary['readings_count']} reading(s) were taken, with an average "
            f"hotspot temperature of {thermal_summary['average_hotspot_c']}°C."
        )
        if thermal_summary["outlier_notes"]:
            additional_notes_parts.append(
                "Notable readings above the survey average: "
                + " ".join(thermal_summary["outlier_notes"])
            )
    additional_notes = " ".join(additional_notes_parts) if additional_notes_parts else NOT_AVAILABLE

    report_id = f"ddr_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    return DDRReport(
        report_id=report_id,
        property_issue_summary=property_issue_summary,
        area_observations=areas,
        overall_severity=overall_severity,
        overall_severity_reasoning=overall_severity_reasoning,
        recommended_actions=recommended_actions,
        additional_notes=additional_notes,
        missing_or_unclear_information=missing_info_notes,
    )
