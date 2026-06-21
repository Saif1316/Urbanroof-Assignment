"""
Small file-handling utilities.

image_path_to_data_uri() is the key function for free-tier deployment:
it converts a saved image file into a self-contained base64 data URI
(e.g. "data:image/jpeg;base64,/9j/4AAQ..."), so the image can be embedded
directly in the API's JSON response and the rendered HTML/PDF, with no
dependency on the file still existing on disk later. This matters on
ephemeral-filesystem free hosting tiers (e.g. Render's free web services),
where files written at runtime are not guaranteed to persist across
restarts or redeploys.
"""

from __future__ import annotations

import base64
import mimetypes
import os


def image_path_to_data_uri(file_path: str) -> str | None:
    """
    Reads an image file from disk and returns it as a base64 data URI
    string. Returns None if the file doesn't exist or can't be read,
    rather than raising - callers should treat None the same as "no
    image available" (consistent with the rest of the system's
    "Not Available" handling).
    """
    if not file_path or not os.path.exists(file_path):
        return None

    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        mime_type = "image/jpeg"  # reasonable default for extracted PDF images

    try:
        with open(file_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("ascii")
    except OSError:
        return None

    return f"data:{mime_type};base64,{encoded}"
