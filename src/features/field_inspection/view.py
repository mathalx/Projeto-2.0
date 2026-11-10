"""Tela principal do novo fluxo de inspeção de campo (v2).

A página abre diretamente no formulário, sem autenticação. O fluxo foi
separado em seções para combinar usabilidade de campo com as regras de
persistência já existentes.
"""

from __future__ import annotations

import html

import streamlit as st

from src.form_template import visit_completion
from src.storage_manager import load_visits
from src.ui_components import (
    render_acnnorte_logo,
    render_empty_state,
    status_badge,
)

from .actions import render_actions
from .checklist import render_checklist, render_notes
from .epi import render_epi_scanner
from .equipment import render_equipment
from .header import render_header
from .services import (
    ACTIVE_INSPECTION_KEY,
    create_inspection_draft,
    inspection_period,
    reload_inspection,
    select_inspection,
)
from .signatures import render_signatures
from .worker import render_worker


def _render_visit_selector(visits: dict) -> str:
    col_select, col_new = st.columns([3.4, 1])
    with col_select:
        inspection_id = select_inspection(visits)
    with col_new:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button(
            "➕ Nova inspeção",
            key="fi_top_new_inspection",
            width="stretch",
        ):
            new_id = create_inspection_draft()
            if new_id:
                st.rerun()
            st.error("Não foi possível iniciar uma nova inspeção.")
    return inspection_id


def _render_context(inspection: dict) -> None:
    answered, total = visit_completion(inspection.get("forms") or {})
    progress = (answered / total) if total else 0
    company = (
        inspection.get("empresa_nome")
        or inspection.get("client_name")
        or "Empresa ainda não informada"
    )
    evaluator = inspection.get("technician") or st.session_state.get("username", "—")

    with st.container(border=True):
        col_company, col_period, col_status, col_progress = st.columns(
            [1.8, 1.1, 1, 1.3]
        )
        with col_company:
            st.markdown(f"### 🏢 {html.escape(str(company))}")
            st.caption(f"Avaliador: {html.escape(str(evaluator))}")
        with col_period:
            st.markdown("**Período**")
            st.markdown(inspection_period(inspection))
        with col_status:
            st.markdown("**Situação**")
            st.markdown(
                status_badge(inspection.get("status", "Rascunho")),
                unsafe_allow_html=True,
            )
        with col_progress:
            st.markdown("**Checklist**")
            st.progress(progress)
            st.caption(f"{answered}/{total} obrigatórios")


def render_field_inspection_view() -> None:
    """Renderiza o formulário completo de inspeção de campo."""
    render_acnnorte_logo(
        size="medium",
        subtitle="Inspeções de Campo — Avaliação de Segurança do Trabalho",
    )

    visits = load_visits()
    if not visits:
        inspection_id = create_inspection_draft()
        if not inspection_id:
            render_empty_state(
                "📝",
                "Não foi possível iniciar a avaliação",
                "Tente novamente em alguns instantes.",
            )
            return
        st.rerun()

    inspection_id = _render_visit_selector(visits)
    if not inspection_id:
        render_empty_state(
            "📝",
            "Nenhuma avaliação disponível",
            "Crie uma nova inspeção para começar.",
        )
        return

    if inspection_id not in visits:
        st.session_state[ACTIVE_INSPECTION_KEY] = inspection_id
        st.rerun()

    inspection = reload_inspection(inspection_id)
    if not inspection:
        st.error("Não foi possível carregar a avaliação selecionada.")
        return

    _render_context(inspection)
    st.caption(
        "Rascunho salvo automaticamente neste dispositivo. "
        f"Identificador da avaliação: {inspection_id}."
    )

    st.markdown("---")
    inspection = render_header(inspection_id, inspection)

    st.markdown("---")
    inspection = render_worker(inspection_id, inspection)

    st.markdown("---")
    inspection = render_equipment(inspection_id, inspection)

    st.markdown("---")
    inspection = render_epi_scanner(inspection_id, inspection)
    render_checklist(inspection_id, inspection)

    st.markdown("---")
    render_notes(inspection_id, inspection)

    st.markdown("---")
    technical_signature, evaluator_signature = render_signatures(
        inspection_id, inspection
    )

    inspection = reload_inspection(inspection_id)
    render_actions(
        inspection_id,
        inspection,
        technical_signature,
        evaluator_signature,
    )
