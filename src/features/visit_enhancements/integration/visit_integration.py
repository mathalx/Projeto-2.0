"""Integração das extensões de visita às telas existentes.

Conecta componentes/serviços reutilizáveis sem recriar auth, clientes,
armazenamento, Xano, exportação ou navegação independente.
"""

from __future__ import annotations

import streamlit as st

from src.features import available_features
from src.storage_manager import load_visits, missing_equipment, missing_signatures

from ..equipment.equipment_selector import render_equipment_block
from ..photographs.photo_manager import render_photographs_block
from ..reports.report_extensions import generate_visit_excel_bytes, generate_visit_pdf_bytes
from ..signatures.signature_service import render_signatures_block
from ..temperature.temperature_service import render_temperature_block
from ..visit_form.visit_form_flow import render_visit_flow_blocks, render_visit_summary_panel


def get_available_enhancement_blocks() -> list[str]:
    """Lista os blocos registrados no ponto central de inicialização."""
    return list(available_features())


def finalize_visit_guard(visit: dict) -> tuple[bool, list[str]]:
    """Valida requisitos adicionais para conclusão (equipamentos e assinaturas)."""
    problems: list[str] = []
    pending_eq = missing_equipment(visit)
    pending_sig = missing_signatures(visit)
    if pending_eq:
        problems.append("Equipamentos pendentes: " + ", ".join(pending_eq))
    if pending_sig:
        problems.append("Assinaturas pendentes: " + ", ".join(pending_sig))
    return (len(problems) == 0, problems)


def render_visit_enhancements_panel(
    visit_id: str,
    *,
    show_summary: bool = True,
    show_blocks: bool = True,
    read_only: bool = False,
    in_sidebar: bool = False,
) -> dict:
    """Painel integrável em telas existentes (área central ou lateral)."""
    visits = load_visits()
    visit = visits.get(str(visit_id), {})
    if not visit:
        st.warning("Visita não encontrada para exibir extensões.")
        return {"visit_id": visit_id, "found": False}

    # ``st`` (o módulo) não é um context manager; use um container explícito
    # para a área central. A sidebar já é um context manager nativo.
    central_summary = show_summary and not (show_blocks and not in_sidebar)
    target = st.sidebar if in_sidebar else (st.container() if central_summary else None)
    result = {"visit_id": visit_id, "found": True}

    if central_summary:
        with target:
            render_visit_summary_panel(visit)

    if show_blocks and not in_sidebar:
        # Em área central, usar layout responsivo: blocos principais + resumo lateral quando houver espaço.
        main_col, side_col = st.columns([3, 1], gap="medium")
        with main_col:
            result["blocks"] = render_visit_flow_blocks(visit_id, visit, read_only=read_only)
        if show_summary:
            with side_col:
                render_visit_summary_panel(visit, title="Status")
    elif show_blocks and in_sidebar:
        with st.sidebar:
            st.caption("Use a área central para formulários extensos e assinaturas.")

    return result
