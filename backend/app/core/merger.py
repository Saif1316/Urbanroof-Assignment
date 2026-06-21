"""
Merges parsed inspection findings and thermal readings into the DDR's
area-wise observation structure.

Key design decision (documented per the "do not invent facts" rule):
the sample thermal report contains NO room/area labels - only sequential
thermal camera readings. There is no reliable way to map a specific
thermal reading to a specific inspection area without inventing that
correspondence. Rather than guessing (by sequence order or by asking an
LLM to visually infer a room from an abstract heatmap), this merger:

  1. Builds area-wise observations entirely from the Inspection Report,
     since that document explicitly names rooms/areas.
  2. Reports thermal findings as a separate, clearly labeled block
     ("Thermal Survey Findings - Area Not Specified in Source Data"),
     attached to the report but not falsely pinned to a specific room.
  3. Surfaces this exact limitation in "Missing or Unclear Information".
  4. Still extracts real signal from thermal data: flags any thermal
     reading whose hotspot is a statistical outlier relative to the rest
     of the survey (using the configured severity thresholds), without
     claiming a room location for it.
"""

from __future__ import annotations

from app.config import settings
from app.core.nlp_extractor import InspectionAreaFinding, ThermalReading, group_areas_by_room
from app.models.schemas import AreaObservation, ExtractedImage


def _find_best_image_for_area(
    room_key: str,
    inspection_images: list[ExtractedImage],
    used_image_paths: set[str],
) -> ExtractedImage | None:
    """
    Best-effort match: picks the first not-yet-used inspection image whose
    caption_guess (nearby page text) mentions the room name. Returns None
    if no match is found - callers must then mark "Image Not Available"
    rather than substituting an unrelated image.
    """
    room_key_lower = room_key.lower()
    for img in inspection_images:
        if img.file_path in used_image_paths:
            continue
        caption = (img.caption_guess or "").lower()
        if room_key_lower in caption:
            return img
    return None


def build_area_observations(
    inspection_findings: list[InspectionAreaFinding],
    inspection_images: list[ExtractedImage],
) -> list[AreaObservation]:
    """Builds one AreaObservation per room, combining negative/positive
    side findings for that room."""
    grouped = group_areas_by_room(inspection_findings)
    observations: list[AreaObservation] = []
    used_image_paths: set[str] = set()

    for room_key, findings in grouped.items():
        negative_descriptions = [f.description for f in findings if f.side == "negative"]
        positive_descriptions = [f.description for f in findings if f.side == "positive"]

        observation_parts = []
        if negative_descriptions:
            observation_parts.append("Issue observed: " + "; ".join(negative_descriptions))
        if positive_descriptions:
            observation_parts.append("Related finding: " + "; ".join(positive_descriptions))

        observation_text = " | ".join(observation_parts) if observation_parts else "Not Available"

        # Severity heuristic based on keyword presence in the observation
        # text. This is intentionally conservative and explainable: it
        # does not invent a cause, only classifies urgency based on terms
        # actually present in the source text.
        severity, severity_reasoning = _classify_severity_from_text(observation_text)

        matched_image = _find_best_image_for_area(room_key, inspection_images, used_image_paths)
        if matched_image:
            used_image_paths.add(matched_image.file_path)

        observations.append(
            AreaObservation(
                area_name=room_key,
                observation=observation_text,
                probable_root_cause=_infer_root_cause_from_keywords(observation_text),
                severity=severity,
                severity_reasoning=severity_reasoning,
                recommended_action=_recommend_action_from_keywords(observation_text),
                image_url=matched_image.file_path if matched_image else None,
                image_caption=f"{room_key} - inspection photo" if matched_image else None,
                source_documents=["inspection_report"],
                has_conflict=False,
                conflict_note=None,
            )
        )

    return observations


def _classify_severity_from_text(text: str) -> tuple[str, str]:
    """Conservative keyword-based severity classification."""
    text_lower = text.lower()

    high_severity_terms = ["leakage", "crack", "structural", "seepage", "corrosion"]
    medium_severity_terms = ["dampness", "hollowness", "efflorescence", "gap"]

    if any(term in text_lower for term in high_severity_terms):
        matched = [t for t in high_severity_terms if t in text_lower]
        return "High", f"Observation text mentions: {', '.join(matched)}, which typically indicate active or structural-adjacent issues."

    if any(term in text_lower for term in medium_severity_terms):
        matched = [t for t in medium_severity_terms if t in text_lower]
        return "Medium", f"Observation text mentions: {', '.join(matched)}, which typically indicate moisture-related but non-structural issues."

    return "Not Available", "Not Available"


def _infer_root_cause_from_keywords(text: str) -> str:
    """
    Conservative, keyword-driven root cause note. Does not assert a cause
    beyond what the keywords in the source text directly suggest, and
    flags uncertainty rather than asserting a definitive diagnosis.
    """
    text_lower = text.lower()
    if "leakage" in text_lower and "plumbing" in text_lower:
        return "Likely related to concealed or damaged plumbing, based on reported leakage and plumbing-related findings. Not confirmed without further investigation."
    if "dampness" in text_lower or "seepage" in text_lower:
        return "Likely moisture ingress (e.g. from plumbing, waterproofing failure, or external seepage). Not confirmed without further investigation."
    if "crack" in text_lower:
        return "Likely related to structural movement or external wall damage. Not confirmed without further investigation."
    return "Not Available"


def _recommend_action_from_keywords(text: str) -> str:
    text_lower = text.lower()
    if "leakage" in text_lower or "plumbing" in text_lower:
        return "Engage a licensed plumber to inspect concealed plumbing lines and repair as needed."
    if "dampness" in text_lower or "seepage" in text_lower:
        return "Conduct a moisture/waterproofing assessment of the affected area."
    if "crack" in text_lower:
        return "Engage a structural engineer to assess crack severity and recommend repair."
    if "hollowness" in text_lower or "gap" in text_lower:
        return "Re-grout or re-lay affected tiles to prevent further water ingress."
    return "Not Available"


def build_thermal_findings_summary(
    thermal_readings: list[ThermalReading],
    thermal_images: list[ExtractedImage],
) -> dict:
    """
    Builds the separate thermal findings block (not pinned to any area).
    Flags statistical outliers using the configured severity thresholds,
    relative to the survey's own average - this is real signal from the
    data, without inventing a room location for it.
    """
    if not thermal_readings:
        return {
            "readings_count": 0,
            "outlier_notes": [],
            "images": [],
        }

    hotspots = [r.hotspot_c for r in thermal_readings if r.hotspot_c is not None]
    avg_hotspot = sum(hotspots) / len(hotspots) if hotspots else None

    outlier_notes = []
    if avg_hotspot is not None:
        for r in thermal_readings:
            if r.hotspot_c is None:
                continue
            delta = r.hotspot_c - avg_hotspot
            if delta >= settings.thermal_high_severity_delta_c:
                outlier_notes.append(
                    f"Reading from page {r.page_number} ({r.source_filename or 'unlabeled'}): "
                    f"{r.hotspot_c}°C, {delta:.1f}°C above the survey average of {avg_hotspot:.1f}°C. "
                    f"Room location not specified in source thermal report."
                )
            elif delta >= settings.thermal_medium_severity_delta_c:
                outlier_notes.append(
                    f"Reading from page {r.page_number} ({r.source_filename or 'unlabeled'}): "
                    f"{r.hotspot_c}°C, moderately above the survey average of {avg_hotspot:.1f}°C. "
                    f"Room location not specified in source thermal report."
                )

    return {
        "readings_count": len(thermal_readings),
        "average_hotspot_c": round(avg_hotspot, 1) if avg_hotspot else None,
        "outlier_notes": outlier_notes,
        "images": [img.file_path for img in thermal_images],
    }
