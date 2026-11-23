"""Bloco de assinaturas digitais (CHANGE 04)."""
from .signature_service import (
    SIGNATURE_LABELS,
    SIGNATURE_ROLES,
    render_signatures_block,
    validate_signatures_for_completion,
)

__all__ = [
    "SIGNATURE_LABELS",
    "SIGNATURE_ROLES",
    "render_signatures_block",
    "validate_signatures_for_completion",
]
