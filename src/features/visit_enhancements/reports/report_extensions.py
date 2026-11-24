"""Extensões de exportação (CHANGE 08).

Reaproveita ``src.export_manager`` (não duplica gerenciador de exportação).
Expõe tanto os bytes dos arquivos quanto os pacotes de download usados pela
tela de relatórios, mantendo uma única fonte de geração.
"""

from __future__ import annotations

import os

from src.export_manager import (
    export_clients_to_excel,
    export_visits_to_excel,
    generate_pdf_report,
)

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PDF_MIME = "application/pdf"


def _read_bytes(path: str | None) -> bytes | None:
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as file:
            return file.read()
    except OSError:
        return None


def _download_payload(path: str | None, mime: str) -> dict | None:
    """Monta o pacote de download a partir do arquivo já gerado."""
    data = _read_bytes(path)
    if data is None:
        return None
    return {"data": data, "name": os.path.basename(path), "mime": mime}


def generate_visit_pdf_bytes(visit_id: str) -> bytes | None:
    """Gera PDF da visita e retorna o conteúdo em bytes (quando disponível)."""
    return _read_bytes(generate_pdf_report(visit_id))


def generate_visit_excel_bytes(visit_id: str = None) -> bytes | None:
    """Gera planilha Excel consolidada de visitas e retorna bytes.

    ``visit_id`` é aceito para compatibilidade da API modular; a exportação
    consolidada atual reutiliza o gerador existente do projeto.
    """
    _ = visit_id
    return _read_bytes(export_visits_to_excel())


def generate_visit_pdf_download(visit_id: str) -> dict | None:
    """Retorna ``data``/``name``/``mime`` do PDF de uma visita."""
    return _download_payload(generate_pdf_report(visit_id), PDF_MIME)


def generate_visits_excel_download() -> dict | None:
    """Retorna o pacote de download da planilha consolidada de visitas."""
    return _download_payload(export_visits_to_excel(), XLSX_MIME)


def generate_clients_excel_download() -> dict | None:
    """Retorna o pacote de download da planilha de clientes."""
    return _download_payload(export_clients_to_excel(), XLSX_MIME)


__all__ = [
    "generate_visit_pdf_bytes",
    "generate_visit_excel_bytes",
    "generate_visit_pdf_download",
    "generate_visits_excel_download",
    "generate_clients_excel_download",
    "export_visits_to_excel",
    "export_clients_to_excel",
    "generate_pdf_report",
]
