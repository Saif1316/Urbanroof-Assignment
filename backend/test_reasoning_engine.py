"""
Tests the reasoning_engine module against real extracted inspection data.

Run this from the backend/ folder, with your venv activated and your
.env file in place (containing GROQ_API_KEY).

Usage:
    python test_reasoning_engine.py
"""

from app.core.pdf_extractor import extract_all
from app.core.nlp_extractor import parse_inspection_areas
from app.core.merger import build_area_observations
from app.core.reasoning_engine import enhance_all_area_observations, generate_property_issue_summary

print("Step 1: Extracting text and images from Sample_Report.pdf...")
inspection_blocks, inspection_images = extract_all(
    "storage/uploads/Sample_Report.pdf",  # adjust path if your file is elsewhere
    "inspection_report",
    "storage/extracted_images/inspection",
)
print(f"  -> {len(inspection_blocks)} text blocks, {len(inspection_images)} images")

print("\nStep 2: Parsing inspection findings...")
findings = parse_inspection_areas(inspection_blocks)
print(f"  -> {len(findings)} findings parsed")

print("\nStep 3: Building rule-based area observations (before LLM enhancement)...")
areas = build_area_observations(findings, inspection_images)
print(f"  -> {len(areas)} areas built")
print("\n--- BEFORE LLM enhancement (rule-based) ---")
for a in areas[:2]:  # just show first 2 for brevity
    print(f"\n[{a.area_name}]")
    print(f"  observation: {a.observation}")
    print(f"  root_cause: {a.probable_root_cause}")
    print(f"  severity_reasoning: {a.severity_reasoning}")

print("\n\nStep 4: Calling Groq (llama-3.3-70b-versatile) to enhance reasoning...")
print("(this may take 10-30 seconds for all areas)")
enhanced_areas = enhance_all_area_observations(areas)

print("\n--- AFTER LLM enhancement ---")
for a in enhanced_areas[:2]:
    print(f"\n[{a.area_name}]")
    print(f"  observation: {a.observation}")
    print(f"  root_cause: {a.probable_root_cause}")
    print(f"  severity_reasoning: {a.severity_reasoning}")
    print(f"  recommended_action: {a.recommended_action}")

print("\n\nStep 5: Generating property issue summary...")
summary = generate_property_issue_summary(enhanced_areas)
print(f"\nSummary:\n{summary}")

print("\n\nDone. If the 'AFTER' text reads more naturally than 'BEFORE' and")
print("doesn't mention any rooms/facts not in the original report, it's working correctly.")
