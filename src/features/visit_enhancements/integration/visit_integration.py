"""Integra??o das extens?es de visita ?s telas existentes.

Conecta componentes/servi?os reutiliz?veis sem recriar auth, clientes,
armazenamento, Xano, exporta??o ou navega??o independente.
"""

from __future__ import annotations

import streamlit as st

from src.storage_manager import load_visits, missing_equipment, missing_signatures

from ..equipment.equipment_selector import render_equipment_block
from ..photographs.photo_manager import render_photographs_block
from ..reports.report_extensions import generate_visit_excel_bytes, generate_visit_pdf_bytes
from ..signatures.signature_service import render_signatures_block
from ..temperature.temperature_service import render_temperature_block
from ..visit_form.visit_form_flow import render_visit_flow_blocks, render_visit_summary_panel


def get_available_enhancement_blocks() -> list[str]:
    return [
        "temperature",
        "signatures",
        "equipment",
        "visit_form_flow",
        "photographs",
        "reports",
        "integration",
    ]


def finalize_visit_guard(visit: dict) -> tuple[bool, list[str]]:
    """Valida requisitos adicionais para conclus?o (equipamentos e assinaturas)."""
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
    """Painel integr?vel em telas existentes (?rea central ou lateral)."""
    visits = load_visits()
    visit = visits.get(str(visit_id), {})
    if not visit:
        st.warning("Visita n?o encontrada para exibir extens?es.")
        return {"visit_id": visit_id, "found": False}

    target = st.sidebar if in_sidebar else st
    result = {"visit_id": visit_id, "found": True}

    if show_summary:
        with target:
            render_visit_summary_panel(visit)

    if show_blocks and not in_sidebar:
        # Em ?rea central, usar layout responsivo: blocos principais + resumo lateral quando houver espa?o.
        main_col, side_col = st.columns([3, 1], gap="medium")
        with main_col:
            result["blocks"] = render_visit_flow_blocks(visit_id, visit, read_only=read_only)
        with side_col:
            render_visit_summary_panel(visit, title="Status")
    elif show_blocks and in_sidebar:
        with target:
            st.caption("Use a ?rea central para formul?rios extensos e assinaturas.")

    return result
