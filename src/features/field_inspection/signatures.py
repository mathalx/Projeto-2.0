"""Assinaturas digitais em canvas/touch do responsável técnico e avaliador."""

from __future__ import annotations

import streamlit as st

from src.components import signature_pad
from src.ui_components import render_section_title, set_flash

from .services import save_signatures, scoped_key


def render_signatures(inspection_id: str, inspection: dict) -> tuple[str, str]:
    render_section_title(
        "Assinaturas digitais",
        "Assine com o dedo, stylus ou mouse. As assinaturas são inseridas no "
        "rodapé do laudo PDF.",
        "✍️",
    )
    signatures = inspection.get("signatures") or {}

    col_technical, col_evaluator = st.columns(2)
    with col_technical:
        technical = signature_pad(
            "Responsável Técnico",
            key=scoped_key(inspection_id, "signature_technical"),
            initial_value=signatures.get("ass_responsavel_tecnico", ""),
        )
    with col_evaluator:
        evaluator = signature_pad(
            "Avaliador de Campo",
            key=scoped_key(inspection_id, "signature_evaluator"),
            initial_value=signatures.get("ass_avaliador", ""),
        )

    if st.button(
        "💾 Salvar assinaturas",
        key=scoped_key(inspection_id, "signature_save"),
        width="stretch",
    ):
        if not technical or not evaluator:
            st.error("As duas assinaturas são obrigatórias para homologar o laudo.")
        else:
            success, message = save_signatures(inspection_id, technical, evaluator)
            if success:
                set_flash(message)
                st.rerun()
            else:
                st.error(message)

    return technical or "", evaluator or ""
