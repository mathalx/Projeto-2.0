"""Fluxo modular do formulário de visita (CHANGE 06).

Organiza blocos da área central e painel auxiliar lateral reutilizando
componentes/serviços existentes (sem recriar navegação, auth ou armazenamento).
"""

from __future__ import annotations

import streamlit as st

from src.equipment_catalog import equipment_label
from src.storage_manager import get_visit_equipment, load_clients, missing_signatures
from src.ui_components import status_badge

from ..equipment.equipment_selector import render_equipment_block, validate_equipment_for_completion
from ..signatures.signature_service import render_signatures_block, validate_signatures_for_completion
from ..temperature.temperature_service import render_temperature_block
from ..photographs.photo_manager import build_photo_identification, render_photographs_block

VISIT_FLOW_STEPS = [
    "Empresa",
    "Datas",
    "Equipamentos e arquivos",
    "Formulário técnico",
]


def _visit_date_label(visit: dict) -> str:
    start = str(visit.get("date_start") or visit.get("date") or "").strip()
    end = str(visit.get("date_end") or "").strip()
    if start and end and end != start:
        return f"{start} a {end}"
    return start or "—"


def render_visit_summary_panel(visit: dict, *, title: str = "Resumo da visita") -> None:
    """Painel lateral auxiliar com resumo e status (área lateral)."""
    with st.container(border=True):
        st.markdown(f"**{title}**")
        clients = load_clients()
        client = clients.get(str(visit.get("client_id") or ""), {})
        company = visit.get("client_name") or client.get("name") or "—"
        worker = visit.get("worker") if isinstance(visit.get("worker"), dict) else {}
        worker_name = worker.get("name") or visit.get("worker_name") or "—"
        equipment = get_visit_equipment(visit)
        weather = visit.get("weather") if isinstance(visit.get("weather"), dict) else {}
        photos = visit.get("photos", []) if isinstance(visit.get("photos"), list) else []
        pending_eq = validate_equipment_for_completion(visit)
        pending_sig = validate_signatures_for_completion(visit)

        st.markdown(f"**Empresa:** {company}")
        st.markdown(f"**Data:** {_visit_date_label(visit)}")
        st.markdown(f"**Funcionário:** {worker_name}")
        st.markdown(f"**Equipamentos:** {len(equipment)} selecionado(s)")
        if equipment:
            for item in equipment[:5]:
                st.caption(f"• {equipment_label(item)}")
            if len(equipment) > 5:
                st.caption(f"• +{len(equipment) - 5} outro(s)")
        temp = weather.get("temperature_c")
        st.markdown(f"**Temperatura externa:** {temp if temp is not None else '—'}")
        st.markdown(f"**Origem:** {weather.get('source') or '—'}")
        st.markdown(f"**Fotografias:** {len(photos)}")
        status = visit.get("status", "Rascunho")
        st.markdown(f"**Situação:** {status_badge(status)}", unsafe_allow_html=True)

        st.markdown("**Etapas/pendências**")
        st.caption(("✅" if not pending_eq else "⚠️") + " Equipamentos" + ("" if not pending_eq else " (pendente)"))
        st.caption(("✅" if not pending_sig else "⚠️") + " Assinaturas" + ("" if not pending_sig else f" ({', '.join(pending_sig)})"))
        st.caption(("✅" if photos else "⚠️") + f" Fotografias ({len(photos)})")


def render_visit_flow_blocks(
    visit_id: str,
    visit: dict,
    *,
    show_temperature: bool = True,
    show_equipment: bool = True,
    show_signatures: bool = True,
    show_photos: bool = True,
    read_only: bool = False,
    layout: str = "central",
) -> dict:
    """Renderiza blocos modulares (área central)."""
    result = {"visit_id": visit_id}
    if show_temperature:
        with st.container(border=True):
            st.markdown("### Condições ambientais")
            result["temperature"] = render_temperature_block(visit_id, visit, read_only=read_only)
    if show_equipment:
        with st.container(border=True):
            st.markdown("### Equipamentos e medições")
            result["equipment"] = render_equipment_block(visit_id, visit, read_only=read_only)
    if show_signatures:
        with st.container(border=True):
            st.markdown("### Assinaturas")
            result["signatures"] = render_signatures_block(visit_id, visit, read_only=read_only)
    if show_photos:
        with st.container(border=True):
            st.markdown("### Fotografias")
            result["photographs"] = render_photographs_block(visit_id, visit)
    return result
