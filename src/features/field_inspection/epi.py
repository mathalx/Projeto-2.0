"""Scanner de EPI (NR-06) com OCR opcional e gravação na galeria."""

from __future__ import annotations

import html
from datetime import datetime

import streamlit as st

from src.epi_scanner import (
    EPI_TAGS,
    analyze_epi_image,
    epi_tag,
    ocr_status,
    suggest_epi_answers,
)
from src.equipment_catalog import build_photo_filename
from src.storage_manager import add_photo_to_visit
from src.ui_components import record_sync, render_section_title, set_flash

from .constants import IMAGE_EXTENSIONS
from .services import apply_epi_answers, reload_inspection, scoped_key


def _first_device(inspection: dict) -> dict | None:
    devices = inspection.get("devices") or []
    return devices[0] if devices else None


def _render_recognition(recognition: dict) -> None:
    st.markdown(
        f'<span class="acn-chip">Resultado: {html.escape(str(recognition.get("status", "—")))}</span>',
        unsafe_allow_html=True,
    )
    if recognition.get("items"):
        chips = "".join(
            f'<span class="acn-chip">{html.escape(item)}</span>'
            for item in recognition["items"]
        )
        st.markdown(f'<div class="acn-chip-list">{chips}</div>', unsafe_allow_html=True)
    if recognition.get("ca"):
        st.caption("CA identificado: " + ", ".join(recognition["ca"]))
    if recognition.get("message"):
        st.caption(str(recognition["message"]))
    if recognition.get("text"):
        with st.expander("Texto lido na imagem"):
            st.code(recognition["text"])


def render_epi_scanner(inspection_id: str, inspection: dict) -> dict:
    render_section_title(
        "Scanner de EPI por imagem — NR-06",
        "Fotografe o EPI ou a etiqueta do CA. O reconhecimento preenche o "
        "checklist automaticamente para revisão do avaliador.",
        "📷",
    )
    st.caption(f"OCR {ocr_status()} neste dispositivo.")

    tab_camera, tab_upload = st.tabs(["Câmera", "Enviar imagem"])
    camera = None
    upload = None
    with tab_camera:
        camera = st.camera_input(
            "Foto do EPI",
            key=scoped_key(inspection_id, "epi_camera"),
        )
    with tab_upload:
        upload = st.file_uploader(
            "Ou enviar imagem do EPI",
            type=IMAGE_EXTENSIONS,
            key=scoped_key(inspection_id, "epi_upload"),
        )

    image_bytes = camera.getvalue() if camera is not None else None
    if upload is not None:
        image_bytes = upload.getvalue()
    if image_bytes:
        st.image(image_bytes, caption="Imagem do EPI para análise", width="stretch")

    if st.button(
        "🔍 Analisar imagem e preencher NR-06",
        key=scoped_key(inspection_id, "epi_analyze"),
        type="primary",
        width="stretch",
    ):
        if not image_bytes:
            st.error("Tire ou envie uma foto do EPI antes de analisar.")
        else:
            with st.spinner("Analisando EPI..."):
                recognition = analyze_epi_image(image_bytes)
                st.session_state[scoped_key(inspection_id, "epi_scan")] = recognition
                answers = suggest_epi_answers(recognition)
                apply_epi_answers(inspection_id, answers)

                first_device = _first_device(inspection)
                filename = build_photo_filename(
                    datetime.now(), first_device, epi_tag(recognition)
                )
                success, _message = add_photo_to_visit(
                    inspection_id,
                    image_bytes,
                    filename,
                    "Foto de EPI analisada pelo scanner",
                    nome_arquivo=filename,
                    horario_registro=datetime.now().strftime("%H:%M:%S"),
                    equipamento_id=first_device.get("codigo") if first_device else None,
                    reconhecimento_epi=recognition,
                )
            if success:
                record_sync()
                detected = recognition.get("items") or []
                detail = ", ".join(detected) if detected else "sem EPI confirmado"
                set_flash(
                    f"Scanner concluído: {detail}. Arquivo {filename} salvo na galeria."
                )
                st.rerun()
            else:
                st.error("A imagem foi analisada, mas não foi possível salvar na galeria.")

    recognition = st.session_state.get(scoped_key(inspection_id, "epi_scan"))
    if recognition:
        _render_recognition(recognition)
        st.caption(
            "Tags disponíveis para o nome do arquivo: "
            + ", ".join(sorted(set(EPI_TAGS.values())))
            + "."
        )
    return reload_inspection(inspection_id)
