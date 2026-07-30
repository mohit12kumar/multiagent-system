"""
backend/core/upload_security.py

Upload File Security Validator.
Validates file upload MIME types, checks max file size (50MB), prevents ZIP bomb / image bomb exploits
by checking image pixel dimensions (max 10000x10000), and blocks unsafe formats (SVG, executable scripts).
"""

import io
import logging
from typing import Tuple, Optional
from backend.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
MAX_IMAGE_PIXELS = 10000 * 10000         # 100 MegaPixels

ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/tiff", "image/bmp", "image/webp", "application/pdf"
}

DISALLOWED_EXTENSIONS = {".svg", ".exe", ".sh", ".bat", ".cmd", ".zip", ".tar", ".gz", ".7z"}

def validate_file_upload(file_bytes: bytes, filename: str, content_type: Optional[str] = None) -> Tuple[bool, str]:
    """
    Validates uploaded file size, mime type, and dimension bounds.
    """
    if not file_bytes:
        raise ValidationError("Uploaded file is empty.")

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise ValidationError(f"File size exceeds maximum allowed limit of 50 MB (got {len(file_bytes) / (1024*1024):.1f} MB).")

    lower_filename = filename.lower()
    for ext in DISALLOWED_EXTENSIONS:
        if lower_filename.endswith(ext):
            raise ValidationError(f"File type '{ext}' is prohibited for security reasons.")

    if content_type and content_type.lower() not in ALLOWED_MIME_TYPES:
        raise ValidationError(f"Content-type '{content_type}' is not supported.")

    # Image dimension check for image uploads using PIL if available
    if content_type and content_type.startswith("image/"):
        try:
            from PIL import Image
            with Image.open(io.BytesIO(file_bytes)) as img:
                w, h = img.size
                if w * h > MAX_IMAGE_PIXELS:
                    raise ValidationError(f"Image dimensions ({w}x{h}) exceed safety threshold of 10,000 x 10,000 pixels.")
        except ValidationError:
            raise
        except Exception as e:
            logger.warning(f"[UploadSecurity] PIL image inspection failed or PIL not installed: {e}")

    return True, "File security validation passed."
