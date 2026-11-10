"""Checklist técnico NR-06, NR-24/08, IT/NR-23, NR-12 e PGR/PCMSO/CIPA."""

from __future__ import annotations

import streamlit as st

from src.form_template import (
    UNANSWERED_LABEL,
    section_completion,
    visit_completion,
)
from src.ui_components import render_section_title

from .services import SECTIONS, answer_key, save_answer

STATUS_OPTIONS_HELP = "As respostas são salvas automaticamente a cada alteração."


def render_checklist(inspection_id: str, inspection: dict) -> None:
    forms = inspection.get("forms") or {}
    answered, total = visit_completion(forms)
    progress = (answered / total) if total else 0

    render_section_title(
        "Checklist técnico de segurança",
        "Percorra as cinco normas. O progresso é salvo automaticamente.",
        "✅",
    )
    col_progress, col_hint = st.columns([2, 1.2])
    with col_progress:
        st.progress(progress)
        st.caption(f"Progresso: {answered} de {total} campos obrigatórios.")
    with col_hint:
        st.caption(STATUS_OPTIONS_HELP)
        pending_sections = sum(
            1
            for category, _info in SECTIONS
            if section_completion(category, forms.get(category, {}))[0]
            < section_completion(category, forms.get(category, {}))[1]
        )
        st.caption(f"{pending_sections} seção(ões) com pendências.")

    for index, (category, category_info) in enumerate(SECTIONS):
        answers = forms.get(category) or {}
        section_answered, section_total = section_completion(category, answers)
        suffix = (
            "✅ completo"
            if section_answered >= section_total
            else f"{section_answered}/{section_total}"
        )
        with st.expander(
            f"{category_info['title']} — {suffix}",
            expanded=(index == 0 and section_answered < section_total),
        ):
            for field in category_info["fields"]:
                key = answer_key(inspection_id, category, field["id"])
                value = answers.get(field["id"], "")
                required = field.get("type") == "select"
                label = field["label"] + (" *" if required else "")

                if field["type"] == "select":
                    options = [UNANSWERED_LABEL] + list(field.get("options", []))
                    if key not in st.session_state:
                        st.session_state[key] = (
                            value if value in options else UNANSWERED_LABEL
                        )
                    st.selectbox(
                        label,
                        options,
                        key=key,
                        on_change=save_answer,
                        args=(inspection_id, category, field["id"]),
                    )
                else:
                    if key not in st.session_state:
                        st.session_state[key] = str(value or "")
                    st.text_area(
                        label,
                        key=key,
                        on_change=save_answer,
                        args=(inspection_id, category, field["id"]),
                    )


def render_notes(inspection_id: str, inspection: dict) -> None:
    render_section_title(
        "Observações e conclusão",
        "Registre os pontos relevantes, recomendações e o parecer final.",
        "📝",
    )
    observations_key = f"fi_observations_{inspection_id}"
    if observations_key not in st.session_state:
        st.session_state[observations_key] = inspection.get("observations", "")
    st.text_area(
        "Observações gerais",
        key=observations_key,
        on_change=_save_notes_callback,
        args=(inspection_id, "observations"),
    )

    conclusions_key = f"fi_conclusions_{inspection_id}"
    if conclusions_key not in st.session_state:
        st.session_state[conclusions_key] = inspection.get("conclusions", "")
    st.text_area(
        "Conclusões e recomendações",
        key=conclusions_key,
        on_change=_save_notes_callback,
        args=(inspection_id, "conclusions"),
    )


def _save_notes_callback(inspection_id: str, field: str) -> None:
    from .services import save_notes

    save_notes(inspection_id, field)
