"""Captura de fotografias por upload ou câmera do dispositivo."""

from .photo_capture import (
    MAX_PHOTO_BYTES,
    PhotoValidationError,
    camera_support_from_headers,
    camera_support_status,
    clear_photo_input,
    normalize_photo_bytes,
    photo_bytes_from_data_url,
    photo_input,
)

__all__ = [
    "MAX_PHOTO_BYTES",
    "PhotoValidationError",
    "camera_support_from_headers",
    "camera_support_status",
    "clear_photo_input",
    "normalize_photo_bytes",
    "photo_bytes_from_data_url",
    "photo_input",
]
