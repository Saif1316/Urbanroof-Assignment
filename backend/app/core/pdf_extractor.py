"""
Extracts text and images from a source PDF (inspection report or thermal
report) using PyMuPDF.

Design choice: we extract text per-page and images per-page, and keep a
"caption_guess" for each image by grabbing the nearest text block on the
same page. This caption_guess is later used by the merger to associate an
image with the right area-wise observation.
"""

from __future__ import annotations

import os
import uuid

import fitz  # PyMuPDF

from app.models.schemas import ExtractedTextBlock, ExtractedImage


def extract_text_blocks(pdf_path: str, source_document: str) -> list[ExtractedTextBlock]:
    """Extract per-page text from a PDF. One block per page (kept simple and
    robust; downstream NLP step handles splitting into observations)."""
    blocks: list[ExtractedTextBlock] = []
    doc = fitz.open(pdf_path)
    try:
        for page_index, page in enumerate(doc):
            text = page.get_text("text").strip()
            if text:
                blocks.append(
                    ExtractedTextBlock(
                        source_document=source_document,
                        page_number=page_index + 1,
                        text=text,
                    )
                )
    finally:
        doc.close()
    return blocks


def extract_images(
    pdf_path: str,
    source_document: str,
    output_dir: str,
    min_dimension_px: int = 300,
) -> list[ExtractedImage]:
    """
    Extract embedded images from a PDF, save them to output_dir, and guess
    a caption for each from the page's text (first ~120 chars of page text,
    as a simple proximity heuristic since PyMuPDF doesn't give per-image
    text anchoring directly without deeper layout analysis).

    Two filters are applied, both necessary (discovered via testing against
    real assignment PDFs, not assumed):

    1. Minimum dimension filter (min_dimension_px): excludes small embedded
       assets (icons, bullet glyphs, legend swatches, repeated UI chrome).
       Real inspection/thermal photos are typically >= 600px on a side;
       icons and template graphics are usually <= 150px.

    2. Placement filter (get_image_rects): `page.get_images()` returns every
       image xref technically referenceable from a page's resource
       dictionary, which can include images that are embedded in the PDF's
       shared resource pool but not actually drawn on that specific page
       (common in PDFs exported from form-builder/report tools that reuse
       a shared resource scope across pages). We confirm an image is
       genuinely placed on the page by checking it has at least one
       drawn rectangle via page.get_image_rects(xref) - without this check,
       a 30-page report with 2 real photos per page can spuriously yield
       dozens of "images" per page.
    """
    os.makedirs(output_dir, exist_ok=True)
    images: list[ExtractedImage] = []

    doc = fitz.open(pdf_path)
    try:
        for page_index, page in enumerate(doc):
            page_text = page.get_text("text").strip()
            caption_guess = page_text[:120] if page_text else None

            image_list = page.get_images(full=True)
            # Track which (rounded rect) positions we've already kept an
            # image for on this page, so that if a PDF has multiple images
            # stacked at the same position (e.g. a duplicated/overlapping
            # embed - seen in some source PDFs with repeated pages), we
            # keep only the last one drawn, which is the visible/topmost
            # one PDF readers actually render.
            seen_rects_this_page: dict[tuple, int] = {}
            candidates: list[tuple] = []  # (xref, rect_key, width, height)

            for img in image_list:
                xref = img[0]
                img_width = img[2]
                img_height = img[3]

                if img_width < min_dimension_px or img_height < min_dimension_px:
                    continue

                placement_rects = page.get_image_rects(xref)
                if not placement_rects:
                    continue

                rect = placement_rects[0]
                rect_key = (round(rect.x0), round(rect.y0), round(rect.x1), round(rect.y1))
                candidates.append((xref, rect_key, img_width, img_height))

            # Keep only the last xref seen for each rect position (last in
            # PDF draw order = topmost/visible).
            for xref, rect_key, img_width, img_height in candidates:
                seen_rects_this_page[rect_key] = xref

            for rect_key, xref in seen_rects_this_page.items():
                try:
                    base_image = doc.extract_image(xref)
                except Exception:
                    continue  # skip unreadable/corrupt embedded image refs

                image_bytes = base_image["image"]
                ext = base_image.get("ext", "png")

                filename = f"{source_document}_p{page_index + 1}_{uuid.uuid4().hex[:8]}.{ext}"
                file_path = os.path.join(output_dir, filename)

                with open(file_path, "wb") as f:
                    f.write(image_bytes)

                images.append(
                    ExtractedImage(
                        source_document=source_document,
                        page_number=page_index + 1,
                        file_path=file_path,
                        caption_guess=caption_guess,
                    )
                )
    finally:
        doc.close()

    return images


def extract_all(pdf_path: str, source_document: str, images_output_dir: str):
    """Convenience wrapper: returns (text_blocks, images) for one PDF."""
    text_blocks = extract_text_blocks(pdf_path, source_document)
    images = extract_images(pdf_path, source_document, images_output_dir)
    return text_blocks, images
