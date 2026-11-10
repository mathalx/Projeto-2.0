import html
import os
from datetime import date, datetime

import streamlit as st

from src.equipment_catalog import (
    build_photo_filename,
    equipment_label,
    load_equipments,
)
from src.storage_manager import (
    add_photo_to_visit,
    load_visits,
    remove_photo_from_visit,
    replace_photo_in_visit,
)
from src.ui_components import (
    PHOTOS_TAB_ADD,
    PHOTOS_TAB_GALLERY,
    PHOTOS_TAB_TODAY,
    PHOTOS_TABS,
    record_sync,
    render_acnnorte_logo,
    render_empty_state,
    render_section_title,
    set_flash,
    set_pending_state,
)


def _select_photos_tab() -> str:
    if st.session_state.get("photos_tab") not in PHOTOS_TABS:
        st.session_state["photos_tab"] = PHOTOS_TAB_GALLERY
    return st.radio(
        "Seção de fotografias",
        PHOTOS_TABS,
        key="photos_tab",
        horizontal=True,
        label_visibility="collapsed",
    )


def _render_upload(selected_v_id: str, visit: dict):
    render_section_title(
        "Adicionar fotografia à visita",
        "Tire ou selecione a imagem, confira a pré-visualização e escreva uma legenda.",
        "📷",
    )

    nonce = st.session_state.get("photo_upload_nonce", 0)
    uploaded_file = st.file_uploader(
        "Selecionar imagem (câmera ou galeria)",
        type=["jpg", "jpeg", "png", "webp"],
        key=f"photo_upload_{nonce}",
        help="Formatos aceitos: JPG, PNG e WEBP.",
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        st.image(file_bytes, caption="Pré-visualização da imagem selecionada", width="stretch")

        caption = st.text_input(
            "Legenda da fotografia *",
            key=f"photo_caption_{nonce}",
            placeholder="Ex: Extintor vencido no corredor do setor B",
        )

        equipment_options = {"Sem equipamento": None}
        for item in load_equipments():
            equipment_options[equipment_label(item)] = item
        equipment_label_selected = st.selectbox(
            "Equipamento relacionado",
            list(equipment_options.keys()),
            key=f"photo_equipment_{nonce}",
        )
        equipment = equipment_options[equipment_label_selected]
        epi_tag = st.text_input(
            "Tag do EPI (opcional)",
            value="EPI_Geral",
            key=f"photo_epi_tag_{nonce}",
            help="Entra no nome do arquivo: [Horário]_[Aparelho]_[TagEPI].jpg",
        )
        preview_name = build_photo_filename(
            datetime.now(), equipment, epi_tag.strip() or None
        )
        st.caption(f"Nome do arquivo: `{preview_name}`")

        if st.button("📷 Anexar fotografia", key=f"attach_photo_{nonce}", type="primary", width="stretch"):
            if not caption.strip():
                st.error("Escreva uma legenda para identificar a fotografia.")
            else:
                now = datetime.now()
                filename = build_photo_filename(now, equipment, epi_tag.strip() or None)
                with st.spinner("Salvando fotografia..."):
                    success, _message = add_photo_to_visit(
                        selected_v_id,
                        file_bytes,
                        uploaded_file.name,
                        caption.strip(),
                        nome_arquivo=filename,
                        horario_registro=now.strftime("%H:%M:%S"),
                        equipamento_id=equipment.get("codigo") if equipment else None,
                        reconhecimento_epi={},
                    )
                if success:
                    st.session_state["photo_upload_nonce"] = nonce + 1
                    set_pending_state(photos_tab=PHOTOS_TAB_GALLERY)
                    record_sync()
                    set_flash("Fotografia anexada com sucesso!")
                    st.rerun()
                else:
                    st.error("Não foi possível anexar a fotografia. Tente novamente.")
    else:
        st.info("Nenhuma imagem selecionada ainda. Escolha um arquivo para ver a pré-visualização.")


def _render_photo_card(selected_v_id: str, photo: dict):
    photo_id = photo.get("id", "")
    with st.container(border=True):
        path = photo.get("path")
        if path and os.path.exists(path):
            st.image(path, width="stretch")
        else:
            st.warning("Arquivo de imagem não encontrado neste dispositivo.")

        st.markdown(
            f'<div class="acn-photo-caption">{html.escape(photo.get("description") or "Sem legenda")}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="acn-photo-meta">Enviada em {html.escape(str(photo.get("uploaded_at", "—")))}</div>',
            unsafe_allow_html=True,
        )
        file_name = photo.get("nome_arquivo") or photo.get("saved_filename")
        if file_name:
            st.caption(f"Arquivo: {file_name}")
        if photo.get("equipamento_id"):
            st.caption(f"Equipamento: {photo['equipamento_id']}")
        recognition = photo.get("reconhecimento_epi") or {}
        if recognition:
            detected = recognition.get("items") or []
            status = recognition.get("status") or "—"
            detail = ", ".join(detected) if detected else "sem EPI confirmado"
            st.caption(f"Scanner EPI: {status} — {detail}")

        if st.button("🗑️ Remover", key=f"del_photo_{selected_v_id}_{photo_id}", width="stretch"):
            st.session_state["photo_delete_pending"] = photo_id

        if st.session_state.get("photo_delete_pending") == photo_id:
            st.warning("Remover esta fotografia? Esta ação não pode ser desfeita.")
            confirm_col, cancel_col = st.columns(2)
            with confirm_col:
                if st.button(
                    "Sim, remover",
                    key=f"confirm_del_photo_{photo_id}",
                    type="primary",
                    width="stretch",
                ):
                    success, _message = remove_photo_from_visit(selected_v_id, photo_id)
                    st.session_state.pop("photo_delete_pending", None)
                    if success:
                        record_sync()
                        set_flash("Fotografia removida com sucesso.")
                        st.rerun()
                    else:
                        st.error("Não foi possível remover a fotografia.")
            with cancel_col:
                if st.button("Cancelar", key=f"cancel_del_photo_{photo_id}", width="stretch"):
                    st.session_state.pop("photo_delete_pending", None)
                    st.rerun()

        with st.expander("♻️ Substituir imagem"):
            new_file = st.file_uploader(
                "Nova imagem",
                type=["jpg", "jpeg", "png", "webp"],
                key=f"replace_file_{photo_id}",
            )
            new_caption = st.text_input(
                "Nova legenda",
                value=photo.get("description", ""),
                key=f"replace_caption_{photo_id}",
            )
            if st.button("Substituir fotografia", key=f"replace_btn_{photo_id}", width="stretch"):
                if new_file is None:
                    st.error("Selecione a nova imagem antes de substituir.")
                elif not new_caption.strip():
                    st.error("Escreva uma legenda para a nova fotografia.")
                else:
                    with st.spinner("Substituindo fotografia..."):
                        success, _message = replace_photo_in_visit(
                            selected_v_id,
                            photo_id,
                            new_file.getvalue(),
                            new_file.name,
                            new_caption.strip(),
                        )
                    if success:
                        record_sync()
                        set_flash("Fotografia substituída com sucesso.")
                        st.rerun()
                    else:
                        st.error("Não foi possível substituir a fotografia.")


def _render_gallery(selected_v_id: str, visit: dict):
    render_section_title(
        "Galeria da visita",
        "Fotografias organizadas por visita, com legenda e data de envio.",
        "🖼️",
    )

    photos = visit.get("photos", [])
    if not photos:
        render_empty_state(
            "🖼️",
            "Nenhuma fotografia anexada",
            "Use a seção “Adicionar Fotografia” para incluir a primeira imagem desta visita.",
        )
        return

    st.caption(f"{len(photos)} fotografia(s) nesta visita.")
    cols = st.columns(2)
    for index, photo in enumerate(photos):
        with cols[index % 2]:
            _render_photo_card(selected_v_id, photo)


def _render_day_gallery(visits: dict):
    render_section_title(
        "Galeria de Fotos do Dia",
        "Todas as fotografias registradas na data selecionada, com o nome padronizado.",
        "📅",
    )

    if "photo_day" not in st.session_state:
        st.session_state["photo_day"] = date.today()
    elif isinstance(st.session_state.get("photo_day"), str):
        try:
            st.session_state["photo_day"] = date.fromisoformat(st.session_state["photo_day"])
        except ValueError:
            st.session_state["photo_day"] = date.today()

    selected_day = st.date_input("Data das fotografias", key="photo_day")
    day_text = selected_day.isoformat()

    entries = []
    for visit_id, visit in visits.items():
        for photo in visit.get("photos", []):
            uploaded = str(photo.get("uploaded_at") or "")
            if uploaded[:10] == day_text:
                entries.append((visit_id, visit, photo))

    entries.sort(key=lambda item: item[2].get("uploaded_at", ""), reverse=True)
    st.caption(
        f"{len(entries)} fotografia(s) em {selected_day.strftime('%d/%m/%Y')}."
    )

    if not entries:
        render_empty_state(
            "📅",
            "Nenhuma foto nesta data",
            "As fotos do scanner de EPI e da galeria aparecem aqui automaticamente.",
        )
        return

    cols = st.columns(2)
    for index, (visit_id, visit, photo) in enumerate(entries):
        with cols[index % 2]:
            with st.container(border=True):
                path = photo.get("path")
                if path and os.path.exists(path):
                    st.image(path, width="stretch")
                else:
                    st.warning("Arquivo de imagem não encontrado neste dispositivo.")
                st.markdown(
                    f'<div class="acn-photo-caption">{html.escape(photo.get("description") or "Sem legenda")}</div>',
                    unsafe_allow_html=True,
                )
                company = visit.get("empresa_nome") or visit.get("client_name") or "—"
                file_name = photo.get("nome_arquivo") or photo.get("saved_filename") or "—"
                st.caption(f"Empresa: {company}")
                st.caption(f"Arquivo: {file_name}")
                st.caption(f"Horário: {photo.get('horario_registro') or photo.get('uploaded_at', '—')}")

                recognition = photo.get("reconhecimento_epi") or {}
                if recognition:
                    items = ", ".join(recognition.get("items") or []) or "sem EPI confirmado"
                    st.caption(f"Scanner EPI: {recognition.get('status', '—')} — {items}")

                if st.button(
                    "🗑️ Remover",
                    key=f"del_day_photo_{visit_id}_{photo.get('id')}",
                    width="stretch",
                ):
                    success, _message = remove_photo_from_visit(visit_id, photo.get("id"))
                    if success:
                        record_sync()
                        set_flash("Fotografia removida com sucesso.")
                        st.rerun()
                    else:
                        st.error("Não foi possível remover a fotografia.")


def render_photos_view():
    render_acnnorte_logo(size="medium", subtitle="Gerenciamento de Fotografias das Visitas")

    visits = load_visits()
    if not visits:
        render_empty_state(
            "📷",
            "Nenhuma visita cadastrada",
            "Inicie uma visita técnica para poder anexar fotografias.",
        )
        return

    selected_tab = _select_photos_tab()
    if selected_tab == PHOTOS_TAB_TODAY:
        _render_day_gallery(visits)
        return

    visit_options = {
        f"Visita #{v_id} — {v.get('client_name', '—')} ({v.get('date', '—')}) • "
        f"{len(v.get('photos', []))} foto(s)": v_id
        for v_id, v in visits.items()
    }
    selected_label = st.selectbox("Selecione a visita", list(visit_options.keys()), key="photo_visit_select")
    selected_v_id = visit_options[selected_label]
    visit = visits[selected_v_id]

    st.markdown(
        f"**Empresa:** {html.escape(str(visit.get('client_name', '—')))} &nbsp;|&nbsp; "
        f"**Data:** {html.escape(str(visit.get('date', '—')))} &nbsp;|&nbsp; "
        f"**Técnico:** {html.escape(str(visit.get('technician', '—')))}"
    )

    if selected_tab == PHOTOS_TAB_ADD:
        _render_upload(selected_v_id, visit)
    else:
        _render_gallery(selected_v_id, visit)
