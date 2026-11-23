import html
import os
from collections import defaultdict

import streamlit as st

from src.components.photo_capture import clear_photo_input, photo_input
from src.storage_manager import (
    add_photo_to_visit,
    get_visit_measurements,
    load_visits,
    remove_photo_from_visit,
    replace_photo_in_visit,
    update_photo_in_visit,
)
from src.ui_components import (
    PHOTOS_TAB_ADD,
    PHOTOS_TAB_GALLERY,
    PHOTOS_TABS,
    record_sync,
    render_acnnorte_logo,
    render_empty_state,
    render_section_title,
    set_flash,
    set_pending_state,
)


def _visit_date_label(visit: dict) -> str:
    start = str(visit.get("date_start") or visit.get("date") or "").strip()
    end = str(visit.get("date_end") or "").strip()
    if start and end and end != start:
        return f"{start} a {end}"
    return start or "—"


def _photo_date(photo: dict, visit: dict) -> str:
    uploaded = str(photo.get("uploaded_at") or "")
    if uploaded:
        return uploaded.split(" ")[0]
    return str(visit.get("date_start") or visit.get("date") or "Sem data")


def _equipment_label_options(visit: dict):
    # Retorna labels de equipamento disponíveis (padrão horário + identificação).
    options = ["? Sem equipamento ?"]
    seen = set()
    for measurement in get_visit_measurements(visit):
        registro = str(
            measurement.get("identificacao_registro")
            or f"{measurement.get('equipment_brand','')} {measurement.get('equipment_identification','')}".strip()
            or measurement.get("id")
            or ""
        ).strip()
        label = str(
            f"{measurement.get('equipment_brand','')} {measurement.get('equipment_identification','')}".strip()
            or measurement.get("equipment_identification")
            or ""
        ).strip()
        # Preferir label limpo do equipamento; o horário é do registro da foto.
        choice = label or registro
        if choice and choice not in seen:
            options.append(choice)
            seen.add(choice)
    # Também inclui registros já existentes nas medições/fotos como referência implícita? manter simples.
    return options


def _measurement_registro_options(visit: dict):
    options = {"? Usar identifica??o manual ?": ("", "")}
    for measurement in get_visit_measurements(visit):
        code = str(measurement.get("equipment_code") or "")
        registro = str(
            measurement.get("identificacao_registro")
            or f"{measurement.get('equipment_brand','')} {measurement.get('equipment_identification','')}".strip()
            or ""
        ).strip()
        label = str(
            f"{measurement.get('equipment_brand','')} {measurement.get('equipment_identification','')}".strip()
            or measurement.get("equipment_identification")
            or ""
        ).strip()
        if registro:
            options[registro] = (code, label)
    return options


def _build_identificacao(horario: str, equipment_label: str) -> str:
    horario = str(horario or "").strip()
    equipment_label = str(equipment_label or "").strip()
    if horario and equipment_label:
        return f"{horario} — {equipment_label}"
    return equipment_label or horario


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



def _photo_capture_key(selected_v_id: str) -> str:
    """Chave estável do campo de captura da visita selecionada."""
    return f"visit_photo_capture_{selected_v_id}"


def _reset_photo_capture_state(selected_v_id: str):
    """Reinicia a captura/seleção atual sem salvar."""
    st.session_state[f"photo_mode_{selected_v_id}"] = None
    st.session_state["photo_upload_nonce"] = st.session_state.get("photo_upload_nonce", 0) + 1
    clear_photo_input(_photo_capture_key(selected_v_id))


def _get_image_source(selected_v_id: str):
    """Retorna (bytes, filename) da foto confirmada no componente."""
    file_bytes = photo_input(
        "Fotografia da evidência",
        key=_photo_capture_key(selected_v_id),
        allow_upload=True,
        allow_camera=True,
        default_camera="environment",
    )
    if file_bytes is None:
        return None, None
    return file_bytes, "evidencia.jpg"


def _render_upload(selected_v_id: str, visit: dict):
    render_section_title(
        "Adicionar fotografia ? visita",
        "Tire uma fotografia pela c?mera ou selecione uma imagem existente. Registre hor?rio, equipamento, legenda e observa??es.",
        "??",
    )

    st.caption(
        f"Visita relacionada: #{selected_v_id} ? {visit.get('client_name', '?')} ({_visit_date_label(visit)}). "
        "As fotografias capturadas ou enviadas utilizam a mesma galeria, organiza??o e armazenamento desta visita."
    )

    nonce = st.session_state.get("photo_upload_nonce", 0)
    file_bytes, filename = _get_image_source(selected_v_id)
    registro_options = _measurement_registro_options(visit)
    equipment_labels = _equipment_label_options(visit)

    if file_bytes is not None:
        st.markdown("#### Pr?-visualiza??o e confirma??o")
        st.image(file_bytes, caption="Pr?-visualiza??o (n?o salva automaticamente)", width="stretch")

        col1, col2 = st.columns(2)
        with col1:
            horario = st.text_input(
                "Hor?rio da fotografia (HH:MM)",
                key=f"photo_time_{nonce}",
                placeholder="08:30",
            )
        with col2:
            # Sugere equipamento a partir dos registros/medi??es da visita
            registro_choice = st.selectbox(
                "Equipamento identificado na visita",
                list(registro_options.keys()),
                key=f"photo_reg_choice_{nonce}",
                help="Selecione um registro de equipamento da visita (padr?o hor?rio + identifica??o) ou informe manualmente.",
            )

        manual_equipment = st.selectbox(
            "Equipamento utilizado (identifica??o)",
            equipment_labels,
            key=f"photo_equip_label_{nonce}",
            help="Usado quando a identifica??o for manual.",
        )

        identificacao_preview = ""
        selected_code, selected_equip_label = registro_options.get(registro_choice, ("", ""))
        if registro_choice != "? Usar identifica??o manual ?":
            base = selected_equip_label or registro_choice.split("?", 1)[-1].strip()
            identificacao_preview = _build_identificacao(horario, base) or registro_choice
        else:
            eq_label = "" if manual_equipment == "? Sem equipamento ?" else manual_equipment
            identificacao_preview = _build_identificacao(horario, eq_label)

        st.caption(
            f"Padr?o de identifica??o: **{identificacao_preview or 'Hor?rio + identifica??o do equipamento'}**"
        )

        caption = st.text_input(
            "Legenda da fotografia *",
            key=f"photo_caption_{nonce}",
            placeholder="Ex: Medi??o no setor de prensagem",
        )
        observations = st.text_area(
            "Observa??es",
            key=f"photo_obs_{nonce}",
            placeholder="Observa??es adicionais sobre a fotografia/registro",
        )

        save_col, retry_col, cancel_col = st.columns(3)
        with save_col:
            if st.button(
                "Salvar fotografia",
                key=f"attach_photo_{nonce}",
                type="primary",
                width="stretch",
            ):
                if not caption.strip():
                    st.error("Escreva uma legenda para identificar a fotografia.")
                else:
                    if registro_choice != "? Usar identifica??o manual ?":
                        base = selected_equip_label or registro_choice.split("?", 1)[-1].strip()
                        eq_label = base
                        eq_code = selected_code
                    else:
                        eq_label = "" if manual_equipment == "? Sem equipamento ?" else manual_equipment
                        eq_code = ""
                    registro = _build_identificacao(horario, eq_label)
                    with st.spinner("Salvando fotografia..."):
                        success, _message = add_photo_to_visit(
                            selected_v_id,
                            file_bytes,
                            filename or "foto.jpg",
                            caption.strip(),
                            equipment_code=eq_code,
                            identificacao_registro=registro,
                            horario=str(horario or "").strip(),
                            equipment_label=eq_label,
                            observations=observations.strip(),
                            validate_photo=True,
                        )
                    if success:
                        _reset_photo_capture_state(selected_v_id)
                        set_pending_state(photos_tab=PHOTOS_TAB_GALLERY)
                        record_sync()
                        set_flash("Fotografia salva com sucesso!")
                        st.rerun()
                    else:
                        st.error(
                            _message
                            or "Não foi possível salvar a fotografia. Tente novamente."
                        )
        with retry_col:
            if st.button(
                "Escolher outra foto",
                key=f"retry_photo_{nonce}",
                width="stretch",
            ):
                _reset_photo_capture_state(selected_v_id)
                st.rerun()
        with cancel_col:
            if st.button("Cancelar", key=f"cancel_photo_{nonce}", width="stretch"):
                _reset_photo_capture_state(selected_v_id)
                st.rerun()
    else:
        st.info(
            "Carregue uma imagem ou capture pela câmera para visualizar a "
            "pré-visualização e preencher a identificação antes de salvar."
        )


def _render_photo_card(selected_v_id: str, photo: dict, visit: dict):
    photo_id = photo.get("id", "")
    with st.container(border=True):
        path = photo.get("path")
        if path and os.path.exists(path):
            st.image(path, width="stretch")
        else:
            st.warning("Arquivo de imagem não encontrado neste dispositivo.")

        st.markdown(
            f'<div class="acn-photo-caption"><b>Legenda:</b> {html.escape(photo.get("description") or "Sem legenda")}</div>',
            unsafe_allow_html=True,
        )
        registro = photo.get("identificacao_registro") or _build_identificacao(
            photo.get("horario", ""), photo.get("equipment_label", "")
        )
        if registro:
            st.markdown(f"**Identificação:** {html.escape(str(registro))}")
        if photo.get("observations"):
            st.markdown(f"**Observações:** {html.escape(str(photo.get('observations')))}")
        st.markdown(
            f'<div class="acn-photo-meta">Data/hora do registro: {html.escape(str(photo.get("uploaded_at", "—")))}</div>',
            unsafe_allow_html=True,
        )

        col_edit, col_del = st.columns(2)
        with col_del:
            if st.button("🗑️ Excluir", key=f"del_photo_{selected_v_id}_{photo_id}", width="stretch"):
                st.session_state["photo_delete_pending"] = photo_id

        if st.session_state.get("photo_delete_pending") == photo_id:
            st.warning("Remover esta fotografia? Esta ação não pode ser desfeita.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Sim, remover", key=f"confirm_del_photo_{photo_id}", type="primary", width="stretch"):
                    success, _message = remove_photo_from_visit(selected_v_id, photo_id)
                    st.session_state.pop("photo_delete_pending", None)
                    if success:
                        record_sync()
                        set_flash("Fotografia removida com sucesso.")
                        st.rerun()
                    else:
                        st.error("Não foi possível remover a fotografia.")
            with c2:
                if st.button("Cancelar", key=f"cancel_del_photo_{photo_id}", width="stretch"):
                    st.session_state.pop("photo_delete_pending", None)
                    st.rerun()

        with st.expander("✏️ Editar identificação, legenda e observações"):
            e_horario = st.text_input(
                "Horário (HH:MM)",
                value=str(photo.get("horario") or ""),
                key=f"edit_time_{photo_id}",
                placeholder="08:30",
            )
            e_equip = st.text_input(
                "Equipamento utilizado (identificação)",
                value=str(photo.get("equipment_label") or ""),
                key=f"edit_equip_{photo_id}",
                placeholder="Ex.: Dosímetro 3440",
            )
            st.caption(f"Padrão: **{_build_identificacao(e_horario, e_equip) or '—'}**")
            e_caption = st.text_input(
                "Legenda",
                value=photo.get("description", ""),
                key=f"edit_caption_{photo_id}",
            )
            e_obs = st.text_area(
                "Observações",
                value=photo.get("observations", ""),
                key=f"edit_obs_{photo_id}",
            )
            if st.button("Salvar alterações", key=f"save_meta_{photo_id}", width="stretch"):
                if not e_caption.strip():
                    st.error("A legenda é obrigatória.")
                else:
                    registro = _build_identificacao(e_horario, e_equip)
                    success, _ = update_photo_in_visit(
                        selected_v_id,
                        photo_id,
                        description=e_caption.strip(),
                        observations=e_obs.strip(),
                        horario=e_horario.strip(),
                        equipment_label=e_equip.strip(),
                        identificacao_registro=registro,
                    )
                    if success:
                        record_sync()
                        set_flash("Fotografia atualizada com sucesso.")
                        st.rerun()
                    else:
                        st.error("Não foi possível atualizar a fotografia.")

        with st.expander("♻️ Substituir imagem"):
            replace_key = f"replace_photo_input_{photo_id}"
            new_file_bytes = photo_input(
                "Nova imagem",
                key=replace_key,
                allow_upload=True,
                allow_camera=True,
                default_camera="environment",
            )
            r_horario = st.text_input(
                "Horário (HH:MM)",
                value=str(photo.get("horario") or ""),
                key=f"rep_time_{photo_id}",
            )
            r_equip = st.text_input(
                "Equipamento utilizado (identificação)",
                value=str(photo.get("equipment_label") or ""),
                key=f"rep_equip_{photo_id}",
            )
            r_caption = st.text_input(
                "Legenda",
                value=photo.get("description", ""),
                key=f"replace_caption_{photo_id}",
            )
            r_obs = st.text_area(
                "Observações",
                value=photo.get("observations", ""),
                key=f"replace_obs_{photo_id}",
            )
            if st.button("Substituir fotografia", key=f"replace_btn_{photo_id}", width="stretch"):
                if new_file_bytes is None:
                    st.error("Selecione ou capture a nova imagem antes de substituir.")
                elif not r_caption.strip():
                    st.error("Escreva uma legenda para a fotografia.")
                else:
                    registro = _build_identificacao(r_horario, r_equip)
                    with st.spinner("Substituindo fotografia..."):
                        success, _message = replace_photo_in_visit(
                            selected_v_id,
                            photo_id,
                            new_file_bytes,
                            "evidencia.jpg",
                            r_caption.strip(),
                            equipment_code=str(photo.get("equipment_code") or ""),
                            identificacao_registro=registro,
                            horario=r_horario.strip(),
                            equipment_label=r_equip.strip(),
                            observations=r_obs.strip(),
                            validate_photo=True,
                        )
                    if success:
                        clear_photo_input(replace_key)
                        record_sync()
                        set_flash("Fotografia substituída com sucesso.")
                        st.rerun()
                    else:
                        st.error(
                            _message
                            or "Não foi possível substituir a fotografia."
                        )


def _render_gallery(selected_v_id: str, visit: dict):
    render_section_title(
        "Galeria da visita",
        "Fotos organizadas por visita, data e equipamento, sem misturar registros de outras empresas ou visitas.",
        "🖼️",
    )

    photos = list(visit.get("photos", []))
    if not photos:
        render_empty_state(
            "🖼️",
            "Nenhuma fotografia anexada",
            "Use a seção “Adicionar Fotografia” para incluir a primeira imagem desta visita.",
        )
        return

    st.caption(f"{len(photos)} fotografia(s) nesta visita.")

    # Filtros / organização
    dates = sorted({_photo_date(p, visit) for p in photos}, reverse=True)
    equipments = sorted(
        {
            str(p.get("identificacao_registro") or p.get("equipment_label") or "Sem equipamento")
            for p in photos
        }
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        date_filter = st.selectbox("Filtrar por data", ["Todas"] + dates, key=f"photo_filter_date_{selected_v_id}")
    with c2:
        equip_filter = st.selectbox("Filtrar por equipamento", ["Todos"] + equipments, key=f"photo_filter_equip_{selected_v_id}")
    with c3:
        group_by = st.selectbox(
            "Organizar por",
            ["Data e equipamento", "Data", "Equipamento", "Sem agrupamento"],
            key=f"photo_group_{selected_v_id}",
        )

    filtered = []
    for p in photos:
        p_date = _photo_date(p, visit)
        p_equip = str(p.get("identificacao_registro") or p.get("equipment_label") or "Sem equipamento")
        if date_filter != "Todas" and p_date != date_filter:
            continue
        if equip_filter != "Todos" and p_equip != equip_filter:
            continue
        filtered.append(p)

    if not filtered:
        render_empty_state("🔍", "Nenhuma fotografia encontrada", "Ajuste os filtros de data ou equipamento.")
        return

    def render_cards(items):
        cols = st.columns(2)
        for index, photo in enumerate(items):
            with cols[index % 2]:
                _render_photo_card(selected_v_id, photo, visit)

    if group_by == "Sem agrupamento":
        render_cards(filtered)
        return

    groups = defaultdict(list)
    for p in filtered:
        p_date = _photo_date(p, visit)
        p_equip = str(p.get("identificacao_registro") or p.get("equipment_label") or "Sem equipamento")
        if group_by == "Data":
            key = f"📅 {p_date}"
        elif group_by == "Equipamento":
            key = f"🧰 {p_equip}"
        else:
            key = f"📅 {p_date} • 🧰 {p_equip}"
        groups[key].append(p)

    for group_key in sorted(groups.keys(), reverse=True):
        st.markdown(f"### {group_key}")
        st.caption(f"{len(groups[group_key])} fotografia(s)")
        render_cards(groups[group_key])


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

    visit_options = {
        f"Visita #{v_id} — {v.get('client_name', '—')} ({_visit_date_label(v)}) • "
        f"{len(v.get('photos', []))} foto(s)": v_id
        for v_id, v in visits.items()
    }
    labels = list(visit_options.keys())
    ids = list(visit_options.values())

    desired_id = st.session_state.pop("photo_active_visit_id", None) or st.session_state.get("active_visit_id")
    if desired_id in ids:
        st.session_state["photo_visit_select"] = labels[ids.index(desired_id)]

    selected_label = st.selectbox("Selecione a visita", labels, key="photo_visit_select")
    selected_v_id = visit_options[selected_label]
    visit = visits[selected_v_id]

    st.markdown(
        f"**Empresa:** {html.escape(str(visit.get('client_name', '—')))} &nbsp;|&nbsp; "
        f"**Data:** {html.escape(_visit_date_label(visit))} &nbsp;|&nbsp; "
        f"**Técnico:** {html.escape(str(visit.get('technician', '—')))}"
    )
    st.caption("Os registros exibidos pertencem apenas à visita selecionada, sem mistura com outras empresas ou visitas.")

    if selected_tab == PHOTOS_TAB_ADD:
        _render_upload(selected_v_id, visit)
    else:
        _render_gallery(selected_v_id, visit)
