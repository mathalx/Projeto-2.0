"""Identificação do trabalhador avaliado e foto obrigatória do rosto."""

from __future__ import annotations

import os

import streamlit as st

from src.ui_components import render_section_title, set_flash

from .constants import WORKER_PHOTO_EXTENSIONS
from .services import reload_inspection, save_worker, scoped_key


def _initial_value(inspection_id: str, name: str, current: str) -> str:
    key = scoped_key(inspection_id, name)
    if key not in st.session_state:
        st.session_state[key] = current
    return key


def render_worker(inspection_id: str, inspection: dict) -> dict:
    render_section_title(
        "Identificação do trabalhador avaliado",
        "O nome e a foto do rosto são obrigatórios para a emissão do laudo.",
        "🧑",
    )
    worker = inspection.get("worker") or {}

    col_text, col_photo = st.columns([1.55, 1])
    with col_text:
        name_key = _initial_value(
            inspection_id, "worker_nome", worker.get("funcionario_nome", "")
        )
        name = st.text_input(
            "Nome do funcionário *",
            key=name_key,
            placeholder="Nome completo",
        )

        role_key = _initial_value(
            inspection_id, "worker_funcao", worker.get("funcao", "")
        )
        role = st.text_input(
            "Função", key=role_key, placeholder="Ex.: Operador de produção"
        )

        sector_key = _initial_value(
            inspection_id, "worker_setor", worker.get("setor", "")
        )
        sector = st.text_input(
            "Setor", key=sector_key, placeholder="Ex.: Setor B — prensas"
        )

        st.caption(
            "A foto será exibida ao lado do nome no laudo corporativo em PDF."
        )

    with col_photo:
        st.markdown("**📸 Foto do rosto (perfil)**")
        tab_camera, tab_upload = st.tabs(["Câmera", "Enviar imagem"])
        camera = None
        upload = None
        with tab_camera:
            camera = st.camera_input(
                "Tirar foto do rosto",
                key=scoped_key(inspection_id, "worker_camera"),
                help="Posicione o rosto centralizado e com boa iluminação.",
            )
        with tab_upload:
            upload = st.file_uploader(
                "Selecionar imagem",
                type=WORKER_PHOTO_EXTENSIONS,
                key=scoped_key(inspection_id, "worker_upload"),
            )

        photo_bytes = camera.getvalue() if camera is not None else None
        photo_name = "foto_funcionario.jpg"
        if upload is not None:
            photo_bytes = upload.getvalue()
            photo_name = upload.name

        if photo_bytes:
            st.image(
                photo_bytes,
                caption="Pré-visualização da foto do rosto",
                width="stretch",
            )
        elif worker.get("funcionario_foto_url") and os.path.exists(
            worker["funcionario_foto_url"]
        ):
            st.image(
                worker["funcionario_foto_url"],
                caption="Foto já salva",
                width="stretch",
            )
        else:
            st.info(
                "Foto obrigatória: tire uma selfie ou envie uma imagem do rosto."
            )

    if st.button(
        "💾 Salvar identificação do funcionário",
        key=scoped_key(inspection_id, "worker_save"),
        type="primary",
        width="stretch",
    ):
        if not name.strip():
            st.error("Informe o nome do funcionário.")
        elif not photo_bytes and not worker.get("funcionario_foto_url"):
            st.error("Tire ou envie a foto do rosto do funcionário.")
        else:
            with st.spinner("Salvando identificação..."):
                success, message, _photo_url = save_worker(
                    inspection_id,
                    name,
                    role,
                    sector,
                    photo_bytes=photo_bytes,
                    photo_filename=photo_name,
                )
            if success:
                set_flash(message)
                st.rerun()
            else:
                st.error(message)

    return reload_inspection(inspection_id)
