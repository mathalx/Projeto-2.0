"""Ações finais: salvar, finalizar, emitir documentos e ir para a galeria."""

from __future__ import annotations

import os
from datetime import date

import streamlit as st

from src.form_template import visit_completion
from src.ui_components import (
    PAGE_PHOTOS,
    PHOTOS_TAB_TODAY,
    navigate_to,
    record_sync,
    render_section_title,
    set_flash,
)

from .constants import GALLERY_FAB_KEY
from .documents import generate_inspection_excel, generate_inspection_pdf
from .services import (
    finalize_inspection,
    persist_all_answers,
    reload_inspection,
    save_signatures,
    validate_for_finalize,
)


def _read_file(path: str) -> bytes:
    with open(path, "rb") as file:
        return file.read()


def _download_document(kind: str, generator, inspection_id: str) -> None:
    with st.spinner("Preparando documento..."):
        try:
            path = generator(inspection_id)
        except Exception:
            st.error("Não foi possível gerar o documento agora. Tente novamente.")
            return

    if not path or not os.path.exists(path):
        st.error("Não foi possível gerar o documento agora. Tente novamente.")
        return

    st.session_state[f"fi_document_{kind}_{inspection_id}"] = {
        "data": _read_file(path),
        "name": os.path.basename(path),
    }
    st.toast("Documento gerado com sucesso!")


def _render_documents(inspection_id: str) -> None:
    render_section_title(
        "Emissão do laudo corporativo",
        "Gere o PDF com foto do trabalhador, tabela técnica e assinaturas, ou "
        "a planilha consolidada da inspeção.",
        "📄",
    )
    col_pdf, col_excel = st.columns(2)
    with col_pdf:
        if st.button(
            "📄 Gerar laudo PDF",
            key=f"fi_generate_pdf_{inspection_id}",
            width="stretch",
        ):
            _download_document("pdf", generate_inspection_pdf, inspection_id)
        pdf = st.session_state.get(f"fi_document_pdf_{inspection_id}")
        if pdf:
            st.download_button(
                "📥 Baixar laudo PDF",
                data=pdf["data"],
                file_name=pdf["name"],
                mime="application/pdf",
                width="stretch",
                key=f"fi_download_pdf_{inspection_id}",
            )
    with col_excel:
        if st.button(
            "📊 Gerar planilha Excel",
            key=f"fi_generate_excel_{inspection_id}",
            width="stretch",
        ):
            _download_document("excel", generate_inspection_excel, inspection_id)
        excel = st.session_state.get(f"fi_document_excel_{inspection_id}")
        if excel:
            st.download_button(
                "📥 Baixar planilha Excel",
                data=excel["data"],
                file_name=excel["name"],
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                width="stretch",
                key=f"fi_download_excel_{inspection_id}",
            )


def render_actions(
    inspection_id: str,
    inspection: dict,
    technical_signature: str,
    evaluator_signature: str,
) -> None:
    st.markdown("---")
    st.caption(
        "Finalize somente após preencher a empresa, o funcionário com foto, "
        "os equipamentos, o checklist e as duas assinaturas."
    )

    col_save, col_finish = st.columns(2)
    with col_save:
        if st.button(
            "💾 Salvar tudo",
            key=f"fi_save_all_{inspection_id}",
            width="stretch",
        ):
            forms = persist_all_answers(inspection_id)
            save_signatures(
                inspection_id, technical_signature, evaluator_signature
            )
            answered, total = visit_completion(forms)
            set_flash(
                f"Formulário salvo. Checklist: {answered}/{total} campos obrigatórios."
            )
            st.rerun()

    with col_finish:
        if st.button(
            "✅ Finalizar avaliação",
            key=f"fi_finalize_{inspection_id}",
            type="primary",
            width="stretch",
        ):
            forms = persist_all_answers(inspection_id)
            pending = finalize_inspection(
                inspection_id,
                forms,
                technical_signature,
                evaluator_signature,
            )
            if pending:
                st.error(
                    "Pendências antes de finalizar: " + "; ".join(pending) + "."
                )
            else:
                set_flash(
                    "Avaliação finalizada. O laudo PDF e a planilha já podem ser gerados."
                )
                st.rerun()

    fresh = reload_inspection(inspection_id)
    if fresh.get("status") == "Finalizada":
        st.success("Avaliação finalizada e pronta para emissão do laudo.")
    else:
        pending = validate_for_finalize(
            fresh,
            fresh.get("forms") or {},
            technical_signature,
            evaluator_signature,
        )
        if pending:
            st.info("Pendências atuais: " + "; ".join(pending) + ".")

    _render_documents(inspection_id)

    st.markdown("---")
    gallery_day = (
        inspection.get("data_avaliacao")
        or inspection.get("date")
        or date.today().isoformat()
    )
    if st.button(
        "➡️ Ir para Galeria do Dia",
        key=GALLERY_FAB_KEY,
        type="primary",
        width="stretch",
        help="Abre todas as fotografias capturadas na visita.",
    ):
        record_sync()
        navigate_to(
            PAGE_PHOTOS,
            photos_tab=PHOTOS_TAB_TODAY,
            photo_day=gallery_day,
        )
