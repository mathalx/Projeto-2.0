"""Extens?es de exporta??o (CHANGE 08).

Reaproveita ``src.export_manager`` (n?o duplica gerenciador de exporta??o).
"""

from __future__ import annotations

import os

from src.export_manager import (
    export_clients_to_excel,
    export_visits_to_excel,
    generate_pdf_report,
)


def generate_visit_pdf_bytes(visit_id: str) -> bytes | None:
    """Gera PDF da visita e retorna o conte?do em bytes (quando dispon?vel)."""
    path = generate_pdf_report(visit_id)
    if not path or not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return f.read()


def generate_visit_excel_bytes(visit_id: str = None) -> bytes | None:
    """Gera planilha Excel consolidada de visitas e retorna bytes.

    ``visit_id`` ? aceito para compatibilidade da API modular; a exporta??o
    consolidada atual reutiliza o gerador existente do projeto.
    """
    _ = visit_id
    path = export_visits_to_excel()
    if not path or not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return f.read()


__all__ = [
    "generate_visit_pdf_bytes",
    "generate_visit_excel_bytes",
    "export_visits_to_excel",
    "export_clients_to_excel",
    "generate_pdf_report",
]
