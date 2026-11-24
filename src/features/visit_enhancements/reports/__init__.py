"""Extensões de relatórios (CHANGE 08)."""
from .report_extensions import (
    generate_clients_excel_download,
    generate_visit_excel_bytes,
    generate_visit_pdf_bytes,
    generate_visit_pdf_download,
    generate_visits_excel_download,
)

__all__ = [
    "generate_visit_excel_bytes",
    "generate_visit_pdf_bytes",
    "generate_visit_pdf_download",
    "generate_visits_excel_download",
    "generate_clients_excel_download",
]
