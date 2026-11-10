"""Formulário de campo — tela principal do aplicativo (CHANGES 08 a 12).

Fluxo direto, sem login:
1. cabeçalho da empresa + datas + clima automático;
2. identificação do funcionário com foto do rosto;
3. catálogo oficial de equipamentos da ACN Norte;
4. scanner de EPI (OCR) e checklist NR-06;
5. assinaturas digitais e acesso rápido à galeria do dia.
"""

from __future__ import annotations

import html
import os
from datetime import date, datetime

import streamlit as st

from src.components import geolocation_button, signature_pad
from src.epi_scanner import analyze_epi_image, epi_tag, ocr_status, suggest_epi_answers
from src.equipment_catalog import (
    EQUIPMENT_CATEGORIES,
    build_photo_filename,
    calibration_label,
    equipment_label,
    find_equipment,
    load_equipments,
    update_calibration_date,
)
from src.form_template import (
    TECHNICAL_FORM_SECTIONS,
    UNANSWERED_LABEL,
    section_completion,
    visit_completion,
)
from src.storage_manager import (
    add_photo_to_visit,
    create_inspection,
    get_inspection,
    load_visits,
    save_inspection_signatures,
    save_inspection_worker,
    set_inspection_devices,
    update_inspection,
)
from src.ui_components import (
    PAGE_PHOTOS,
    PHOTOS_TAB_TODAY,
    navigate_to,
    record_sync,
    render_acnnorte_logo,
    render_empty_state,
    render_section_title,
    set_flash,
    status_badge,
)
from src.weather_service import (
    WeatherError,
    capture_weather,
    format_humidity,
    format_temperature,
    is_configured,
)

SECTIONS = list(TECHNICAL_FORM_SECTIONS.items())


# ---------------------------------------------------------------------------
# Chaves e utilidades de estado
# ---------------------------------------------------------------------------
def _key(inspection_id: str, name: str) -> str:
    return f"field_{name}_{inspection_id}"


def _answer_key(inspection_id: str, category: str, field_id: str) -> str:
    return _key(inspection_id, f"answer_{category}_{field_id}")


def _as_date(value, fallback: date | None = None) -> date:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return fallback or date.today()


def _label(inspection: dict) -> str:
    empresa = inspection.get("empresa_nome") or inspection.get("client_name") or "Nova avaliação"
    when = inspection.get("data_avaliacao") or inspection.get("date") or "sem data"
    return f"{empresa} — {when} • {inspection.get('status', 'Rascunho')}"


def _reload(inspection_id: str) -> dict:
    return get_inspection(inspection_id) or {}


# ---------------------------------------------------------------------------
# Cabeçalho, empresa, datas e clima
# ---------------------------------------------------------------------------
def _save_header(inspection_id: str):
    update_inspection(
        inspection_id,
        empresa_nome=st.session_state.get(_key(inspection_id, "empresa"), ""),
        data_avaliacao=str(
            st.session_state.get(_key(inspection_id, "data_inicio"), date.today())
        ),
        data_avaliacao_fim=str(
            st.session_state.get(_key(inspection_id, "data_fim"), date.today())
        ),
    )
    record_sync()


def _init_header_widgets(inspection_id: str, inspection: dict):
    empresa_key = _key(inspection_id, "empresa")
    if empresa_key not in st.session_state:
        st.session_state[empresa_key] = (
            inspection.get("empresa_nome") or inspection.get("client_name") or ""
        )

    start_key = _key(inspection_id, "data_inicio")
    if start_key not in st.session_state:
        st.session_state[start_key] = _as_date(
            inspection.get("data_avaliacao") or inspection.get("date")
        )

    end_key = _key(inspection_id, "data_fim")
    if end_key not in st.session_state:
        st.session_state[end_key] = _as_date(
            inspection.get("data_avaliacao_fim")
            or inspection.get("data_avaliacao")
            or inspection.get("date")
        )


def _render_weather(inspection_id: str, inspection: dict):
    st.markdown("#### 🌡️ Clima no local da avaliação")

    temp = inspection.get("temperatura_capturada")
    humidity = inspection.get("umidade_capturada")
    climate = inspection.get("clima") or {}

    col_temp, col_hum, col_info = st.columns(3)
    with col_temp:
        st.metric("Temperatura", format_temperature(temp))
    with col_hum:
        st.metric("Umidade relativa", format_humidity(humidity))
    with col_info:
        location = climate.get("cidade") or "Localização do dispositivo"
        st.metric("Local", location or "—")

    if climate.get("capturado_em"):
        st.caption(
            "Capturado automaticamente em "
            f"{climate.get('capturado_em')} — GPS {climate.get('latitude')}, {climate.get('longitude')}."
        )

    geo_key = _key(inspection_id, "geo")
    geo_col, manual_col = st.columns([1, 1.35])
    with geo_col:
        geolocation_button(key=geo_key)
        st.caption(
            "O navegador pedirá permissão de localização. O GPS é usado apenas "
            "para consultar temperatura e umidade."
        )
    with manual_col:
        with st.expander("Informar coordenadas ou clima manualmente"):
            manual_lat = st.text_input(
                "Latitude",
                value=str(climate.get("latitude") or ""),
                key=_key(inspection_id, "manual_lat"),
                placeholder="-23.5505",
            )
            manual_lon = st.text_input(
                "Longitude",
                value=str(climate.get("longitude") or ""),
                key=_key(inspection_id, "manual_lon"),
                placeholder="-46.6333",
            )
            if st.button("Capturar clima com estas coordenadas", key=_key(inspection_id, "manual_weather")):
                try:
                    latitude = float(manual_lat.replace(",", "."))
                    longitude = float(manual_lon.replace(",", "."))
                    reading = capture_weather(latitude, longitude)
                except (ValueError, WeatherError) as exc:
                    st.error(str(exc))
                else:
                    update_inspection(
                        inspection_id,
                        temperatura_capturada=reading.temperatura,
                        umidade_capturada=reading.umidade,
                        clima=reading.to_dict(),
                    )
                    record_sync()
                    set_flash(
                        f"Clima capturado: {format_temperature(reading.temperatura)} e "
                        f"{format_humidity(reading.umidade)}."
                    )
                    st.rerun()

            st.markdown("**Ajuste manual**")
            manual_temp = st.number_input(
                "Temperatura (°C)",
                min_value=-20.0,
                max_value=70.0,
                value=float(temp) if temp is not None else 24.0,
                step=0.1,
                key=_key(inspection_id, "manual_temp"),
            )
            manual_hum = st.number_input(
                "Umidade (%)",
                min_value=0.0,
                max_value=100.0,
                value=float(humidity) if humidity is not None else 60.0,
                step=1.0,
                key=_key(inspection_id, "manual_hum"),
            )
            if st.button("Salvar clima manual", key=_key(inspection_id, "manual_save")):
                update_inspection(
                    inspection_id,
                    temperatura_capturada=manual_temp,
                    umidade_capturada=manual_hum,
                    clima={
                        **(climate or {}),
                        "temperatura": manual_temp,
                        "umidade": manual_hum,
                        "origem": "manual",
                        "capturado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    },
                )
                record_sync()
                set_flash("Temperatura e umidade salvas.")
                st.rerun()

    # Captura automática quando o componente de GPS entrega coordenadas novas.
    geo_state = st.session_state.get(geo_key, {})
    if not isinstance(geo_state, dict):
        geo_state = {}
    latitude = geo_state.get("latitude")
    longitude = geo_state.get("longitude")
    attempt_key = _key(inspection_id, "weather_attempt")

    if latitude is not None and longitude is not None:
        location_token = f"{float(latitude):.5f},{float(longitude):.5f}"
        if st.session_state.get(attempt_key) != location_token:
            st.session_state[attempt_key] = location_token
            if not is_configured():
                st.warning(
                    "GPS capturado. Para buscar a temperatura automaticamente, "
                    "configure OPENWEATHER_API_KEY no arquivo .env."
                )
            else:
                with st.spinner("Consultando temperatura e umidade pelo GPS..."):
                    try:
                        reading = capture_weather(latitude, longitude)
                    except WeatherError as exc:
                        st.warning(str(exc))
                    else:
                        update_inspection(
                            inspection_id,
                            temperatura_capturada=reading.temperatura,
                            umidade_capturada=reading.umidade,
                            clima=reading.to_dict(),
                        )
                        record_sync()
                        set_flash(
                            f"Clima capturado automaticamente: "
                            f"{format_temperature(reading.temperatura)} e "
                            f"{format_humidity(reading.umidade)}."
                        )
                        st.rerun()


def _render_header(inspection_id: str, inspection: dict):
    render_section_title(
        "Formulário de campo",
        "Dados da empresa, período de avaliação e clima do local.",
        "📝",
    )
    _init_header_widgets(inspection_id, inspection)

    with st.container(border=True):
        col_company, col_start, col_end = st.columns([2, 1, 1])
        with col_company:
            st.text_input(
                "Nome da empresa *",
                key=_key(inspection_id, "empresa"),
                placeholder="Razão social ou nome fantasia",
                on_change=_save_header,
                args=(inspection_id,),
            )
        with col_start:
            st.date_input(
                "Data de avaliação *",
                key=_key(inspection_id, "data_inicio"),
                on_change=_save_header,
                args=(inspection_id,),
            )
        with col_end:
            st.date_input(
                "Data final da avaliação",
                key=_key(inspection_id, "data_fim"),
                on_change=_save_header,
                args=(inspection_id,),
            )

        st.markdown(
            f"**Situação:** {status_badge(inspection.get('status', 'Rascunho'))}",
            unsafe_allow_html=True,
        )

    _render_weather(inspection_id, inspection)


# ---------------------------------------------------------------------------
# Identificação do funcionário com foto
# ---------------------------------------------------------------------------
def _render_worker(inspection_id: str, inspection: dict):
    render_section_title(
        "Identificação do funcionário avaliado",
        "O nome deve vir acompanhado da foto do rosto para o laudo.",
        "🧑",
    )
    worker = inspection.get("worker") or {}

    col_text, col_photo = st.columns([1.6, 1])
    with col_text:
        name_key = _key(inspection_id, "worker_nome")
        if name_key not in st.session_state:
            st.session_state[name_key] = worker.get("funcionario_nome", "")
        name = st.text_input(
            "Nome do funcionário *",
            key=name_key,
            placeholder="Nome completo",
        )

        role_key = _key(inspection_id, "worker_funcao")
        if role_key not in st.session_state:
            st.session_state[role_key] = worker.get("funcao", "")
        role = st.text_input("Função", key=role_key, placeholder="Ex.: Operador de produção")

        sector_key = _key(inspection_id, "worker_setor")
        if sector_key not in st.session_state:
            st.session_state[sector_key] = worker.get("setor", "")
        sector = st.text_input("Setor", key=sector_key, placeholder="Ex.: Setor B — prensas")

    with col_photo:
        st.markdown("**Foto do rosto**")
        camera = st.camera_input("Tirar foto", key=_key(inspection_id, "worker_camera"))
        upload = st.file_uploader(
            "Ou enviar da galeria",
            type=["jpg", "jpeg", "png", "webp"],
            key=_key(inspection_id, "worker_upload"),
        )
        photo_bytes = camera.getvalue() if camera is not None else None
        photo_name = "foto_funcionario.jpg"
        if upload is not None:
            photo_bytes = upload.getvalue()
            photo_name = upload.name
        if photo_bytes:
            st.image(photo_bytes, caption="Pré-visualização da foto do rosto", width="stretch")
        elif worker.get("funcionario_foto_url") and os.path.exists(worker["funcionario_foto_url"]):
            st.image(worker["funcionario_foto_url"], caption="Foto já salva", width="stretch")
        else:
            st.info("A foto do rosto é obrigatória para o laudo. Tire ou envie uma imagem.")

    if st.button("💾 Salvar identificação do funcionário", key=_key(inspection_id, "worker_save"), type="primary"):
        if not name.strip():
            st.error("Informe o nome do funcionário.")
        elif not photo_bytes and not worker.get("funcionario_foto_url"):
            st.error("Tire ou envie a foto do rosto do funcionário.")
        else:
            with st.spinner("Salvando identificação..."):
                success, message, _photo_url = save_inspection_worker(
                    inspection_id,
                    name,
                    role,
                    sector,
                    photo_bytes=photo_bytes,
                    photo_filename=photo_name,
                )
            if success:
                record_sync()
                set_flash(message)
                st.rerun()
            else:
                st.error(message)


# ---------------------------------------------------------------------------
# Catálogo de equipamentos e nomes de arquivos
# ---------------------------------------------------------------------------
def _render_equipment(inspection_id: str, inspection: dict):
    render_section_title(
        "Equipamentos utilizados (catálogo ACN Norte)",
        "Selecione rapidamente. A data de calibração e o nome dos arquivos são gerados automaticamente.",
        "🧰",
    )
    equipments = load_equipments()
    by_code = {item["codigo"]: item for item in equipments}

    devices_key = _key(inspection_id, "devices")
    if devices_key not in st.session_state:
        st.session_state[devices_key] = {
            item.get("codigo"): item for item in (inspection.get("devices") or [])
        }
    stored_devices = dict(st.session_state[devices_key])

    category_key = _key(inspection_id, "equipment_category")
    if category_key not in st.session_state:
        st.session_state[category_key] = EQUIPMENT_CATEGORIES[0]
    category = st.segmented_control(
        "Tipo de equipamento",
        EQUIPMENT_CATEGORIES,
        key=category_key,
    )
    category = category or EQUIPMENT_CATEGORIES[0]

    category_items = [item for item in equipments if item.get("categoria") == category]
    label_to_code = {equipment_label(item): item["codigo"] for item in category_items}
    code_to_label = {value: key for key, value in label_to_code.items()}
    selected_default = [
        code_to_label[code] for code in stored_devices if code in code_to_label
    ]

    select_key = _key(inspection_id, f"equipment_select_{category}")
    if select_key not in st.session_state:
        st.session_state[select_key] = selected_default
    selected_labels = st.multiselect(
        "Selecione um ou mais equipamentos",
        list(label_to_code.keys()),
        key=select_key,
        placeholder="Digite ou escolha no catálogo",
    )

    # Mantém a seleção das outras categorias e atualiza apenas a atual.
    for code in [item["codigo"] for item in category_items]:
        stored_devices.pop(code, None)
    for label in selected_labels:
        code = label_to_code.get(label)
        if code:
            stored_devices[code] = by_code[code]

    st.session_state[devices_key] = stored_devices
    current_snapshot = list(stored_devices.values())
    if current_snapshot != (inspection.get("devices") or []):
        set_inspection_devices(inspection_id, current_snapshot)
        record_sync()

    selected_items = list(stored_devices.values())
    if not selected_items:
        st.info("Nenhum equipamento selecionado nesta categoria ainda.")
    else:
        st.markdown("#### Data da última calibração")
        for item in selected_items:
            with st.container(border=True):
                col_info, col_cal = st.columns([2, 1])
                with col_info:
                    st.markdown(f"**{equipment_label(item)}**")
                    st.caption(
                        f"Código {item.get('codigo')} • Série/equipamento "
                        f"{item.get('num_equipamento') or item.get('num_serie') or '—'}"
                    )
                with col_cal:
                    st.metric("Última calibração", calibration_label(item))

    # Pré-visualização da nomenclatura padrão.
    first_device = selected_items[0] if selected_items else None
    preview = build_photo_filename(datetime.now(), first_device, "EPI_ProtetorAuditivo")
    st.caption(
        "Padrão dos arquivos: [Horário]_[Identificação do aparelho]_[TagEPI].jpg — "
        f"exemplo agora: `{preview}`"
    )

    if selected_items:
        with st.expander("Atualizar data de calibração"):
            calibration_labels = {
                equipment_label(item): item for item in selected_items
            }
            chosen_label = st.selectbox(
                "Equipamento",
                list(calibration_labels.keys()),
                key=_key(inspection_id, "calibration_select"),
            )
            chosen = calibration_labels[chosen_label]
            current_date = _as_date(chosen.get("data_ultima_calibracao"))
            new_date = st.date_input(
                "Nova data da última calibração",
                value=current_date,
                key=_key(inspection_id, "calibration_date"),
            )
            if st.button("Registrar calibração", key=_key(inspection_id, "calibration_save")):
                update_calibration_date(chosen["codigo"], new_date)
                refreshed = find_equipment(codigo=chosen["codigo"])
                if refreshed:
                    stored_devices[chosen["codigo"]] = refreshed
                    st.session_state[devices_key] = stored_devices
                    set_inspection_devices(inspection_id, list(stored_devices.values()))
                set_flash("Data de calibração atualizada.")
                st.rerun()


# ---------------------------------------------------------------------------
# Scanner de EPI e checklist NR-06
# ---------------------------------------------------------------------------
def _first_device(inspection_id: str) -> dict | None:
    devices = st.session_state.get(_key(inspection_id, "devices"), {})
    if isinstance(devices, dict) and devices:
        return next(iter(devices.values()))
    return None


def _persist_forms(inspection_id: str, forms: dict):
    update_inspection(inspection_id, forms=forms)
    record_sync()


def _apply_epi_suggestions(inspection_id: str, answers: dict):
    inspection = _reload(inspection_id)
    forms = {key: dict(value or {}) for key, value in (inspection.get("forms") or {}).items()}
    forms.setdefault("epi", {}).update(answers)
    for field_id, value in answers.items():
        st.session_state[_answer_key(inspection_id, "epi", field_id)] = value
    _persist_forms(inspection_id, forms)


def _render_epi_scanner(inspection_id: str, inspection: dict):
    st.markdown("#### 📷 Scanner de EPI por imagem (NR-06)")
    st.caption(
        "Tire a foto do EPI ou da etiqueta com CA. O reconhecimento preenche o "
        f"checklist automaticamente (OCR {ocr_status()})."
    )

    col_camera, col_upload = st.columns(2)
    with col_camera:
        camera = st.camera_input("Foto do EPI", key=_key(inspection_id, "epi_camera"))
    with col_upload:
        upload = st.file_uploader(
            "Ou enviar imagem do EPI",
            type=["jpg", "jpeg", "png", "webp"],
            key=_key(inspection_id, "epi_upload"),
        )

    image_bytes = camera.getvalue() if camera is not None else None
    if upload is not None:
        image_bytes = upload.getvalue()
    if image_bytes:
        st.image(image_bytes, caption="Imagem do EPI para análise", width="stretch")

    if st.button("🔍 Analisar imagem do EPI", key=_key(inspection_id, "epi_analyze"), type="primary"):
        if not image_bytes:
            st.error("Tire ou envie uma foto do EPI antes de analisar.")
        else:
            with st.spinner("Analisando EPI..."):
                recognition = analyze_epi_image(image_bytes)
                st.session_state[_key(inspection_id, "epi_scan")] = recognition
                answers = suggest_epi_answers(recognition)
                _apply_epi_suggestions(inspection_id, answers)
                first_device = _first_device(inspection_id)
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
                detected = recognition.get("items") or []
                detail = ", ".join(detected) if detected else "sem EPI confirmado"
                set_flash(f"Scanner concluído: {detail}. Arquivo {filename} salvo na galeria.")
                st.rerun()
            else:
                st.error("A imagem foi analisada, mas não foi possível salvar na galeria.")

    recognition = st.session_state.get(_key(inspection_id, "epi_scan"))
    if recognition:
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
        if recognition.get("text"):
            with st.expander("Texto lido na imagem"):
                st.code(recognition["text"])


def _save_answer(inspection_id: str, category: str, field_id: str):
    key = _answer_key(inspection_id, category, field_id)
    value = st.session_state.get(key, "")
    if value == UNANSWERED_LABEL:
        value = ""
    inspection = _reload(inspection_id)
    forms = {name: dict(data or {}) for name, data in (inspection.get("forms") or {}).items()}
    forms.setdefault(category, {})[field_id] = value
    _persist_forms(inspection_id, forms)


def _render_checklist(inspection_id: str, inspection: dict):
    render_section_title(
        "Checklist técnico de segurança",
        "As respostas são salvas automaticamente a cada alteração.",
        "✅",
    )
    forms = inspection.get("forms") or {}

    for index, (category, category_info) in enumerate(SECTIONS):
        answers = forms.get(category) or {}
        with st.expander(category_info["title"], expanded=(index == 0)):
            for field in category_info["fields"]:
                key = _answer_key(inspection_id, category, field["id"])
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
                        on_change=_save_answer,
                        args=(inspection_id, category, field["id"]),
                    )
                else:
                    if key not in st.session_state:
                        st.session_state[key] = str(value or "")
                    st.text_area(
                        label,
                        key=key,
                        on_change=_save_answer,
                        args=(inspection_id, category, field["id"]),
                    )


def _save_notes(inspection_id: str, field: str):
    key = _key(inspection_id, field)
    update_inspection(inspection_id, **{field: st.session_state.get(key, "")})
    record_sync()


def _render_notes(inspection_id: str, inspection: dict):
    render_section_title("Observações e conclusão", "Registre os pontos relevantes da avaliação.", "📝")
    obs_key = _key(inspection_id, "observations")
    if obs_key not in st.session_state:
        st.session_state[obs_key] = inspection.get("observations", "")
    st.text_area(
        "Observações gerais",
        key=obs_key,
        on_change=_save_notes,
        args=(inspection_id, "observations"),
    )

    conc_key = _key(inspection_id, "conclusions")
    if conc_key not in st.session_state:
        st.session_state[conc_key] = inspection.get("conclusions", "")
    st.text_area(
        "Conclusões e recomendações",
        key=conc_key,
        on_change=_save_notes,
        args=(inspection_id, "conclusions"),
    )


# ---------------------------------------------------------------------------
# Assinaturas digitais
# ---------------------------------------------------------------------------
def _render_signatures(inspection_id: str, inspection: dict):
    render_section_title(
        "Assinaturas digitais",
        "Assine com o dedo, stylus ou mouse. As assinaturas entram no rodapé do laudo.",
        "✍️",
    )
    signatures = inspection.get("signatures") or {}
    col_resp, col_aval = st.columns(2)
    with col_resp:
        resp = signature_pad(
            "Responsável Técnico",
            key=_key(inspection_id, "signature_resp"),
            initial_value=signatures.get("ass_responsavel_tecnico", ""),
        )
    with col_aval:
        aval = signature_pad(
            "Avaliador",
            key=_key(inspection_id, "signature_aval"),
            initial_value=signatures.get("ass_avaliador", ""),
        )

    if st.button("💾 Salvar assinaturas", key=_key(inspection_id, "signature_save")):
        if not resp or not aval:
            st.error("As duas assinaturas são obrigatórias para homologar o laudo.")
        else:
            success, message = save_inspection_signatures(inspection_id, resp, aval)
            if success:
                record_sync()
                set_flash(message)
                st.rerun()
            else:
                st.error(message)
    return resp, aval


# ---------------------------------------------------------------------------
# Persistência e finalização
# ---------------------------------------------------------------------------
def _persist_all_answers(inspection_id: str):
    inspection = _reload(inspection_id)
    forms = {name: dict(data or {}) for name, data in (inspection.get("forms") or {}).items()}
    for category, category_info in SECTIONS:
        for field in category_info["fields"]:
            key = _answer_key(inspection_id, category, field["id"])
            if key in st.session_state:
                value = st.session_state[key]
                if value == UNANSWERED_LABEL:
                    value = ""
                forms.setdefault(category, {})[field["id"]] = value
    update_inspection(
        inspection_id,
        forms=forms,
        observations=st.session_state.get(_key(inspection_id, "observations"), ""),
        conclusions=st.session_state.get(_key(inspection_id, "conclusions"), ""),
    )
    record_sync()
    return forms


def _validate_for_finalize(inspection: dict, forms: dict, resp: str, aval: str) -> list[str]:
    pending = []
    if not (inspection.get("empresa_nome") or inspection.get("client_name")):
        pending.append("Nome da empresa")
    worker = inspection.get("worker") or {}
    if not worker.get("funcionario_nome"):
        pending.append("Nome do funcionário")
    if not worker.get("funcionario_foto_url"):
        pending.append("Foto do rosto do funcionário")
    if not (inspection.get("devices") or []):
        pending.append("Pelo menos um equipamento")
    answered, total = visit_completion(forms)
    if answered < total:
        pending.append(f"Checklist ({answered}/{total} campos obrigatórios)")
    if not resp:
        pending.append("Assinatura do responsável técnico")
    if not aval:
        pending.append("Assinatura do avaliador")
    return pending


def _render_actions(inspection_id: str, inspection: dict, resp: str, aval: str):
    st.markdown("---")
    col_save, col_finish = st.columns(2)
    with col_save:
        if st.button("💾 Salvar tudo", key=_key(inspection_id, "save_all"), width="stretch"):
            forms = _persist_all_answers(inspection_id)
            save_inspection_signatures(inspection_id, resp, aval)
            answered, total = visit_completion(forms)
            set_flash(f"Formulário salvo. Checklist: {answered}/{total} campos obrigatórios.")
            st.rerun()
    with col_finish:
        if st.button(
            "✅ Finalizar avaliação",
            key=_key(inspection_id, "finalize"),
            type="primary",
            width="stretch",
        ):
            forms = _persist_all_answers(inspection_id)
            save_inspection_signatures(inspection_id, resp, aval)
            fresh = _reload(inspection_id)
            pending = _validate_for_finalize(fresh, forms, resp, aval)
            if pending:
                st.error("Pendências antes de finalizar: " + "; ".join(pending) + ".")
            else:
                update_inspection(inspection_id, status="Finalizada")
                record_sync()
                set_flash("Avaliação finalizada. O laudo PDF já pode ser gerado.")
                st.rerun()

    if st.button("➡️ Galeria do dia", key="gallery_fab"):
        navigate_to(
            PAGE_PHOTOS,
            photos_tab=PHOTOS_TAB_TODAY,
            photo_day=inspection.get("data_avaliacao")
            or inspection.get("date")
            or date.today().isoformat(),
        )


# ---------------------------------------------------------------------------
# Seleção/criação da avaliação e entrada da página
# ---------------------------------------------------------------------------
def _create_new_inspection() -> str:
    today = date.today().isoformat()
    success, inspection_id, _message = create_inspection(
        "",
        today,
        today,
        st.session_state.get("username", "Avaliador ACNnorte"),
    )
    if success:
        st.session_state["field_inspection_id"] = inspection_id
        st.session_state["field_inspection_select_pending"] = inspection_id
        return inspection_id
    return ""


def _select_inspection(visits: dict) -> str:
    options = {_label(inspection): inspection_id for inspection_id, inspection in visits.items()}
    options["➕ Nova avaliação"] = "__new__"

    current_id = st.session_state.get("field_inspection_id")
    desired_id = st.session_state.pop("field_inspection_select_pending", None)
    if desired_id in visits:
        current_id = desired_id
    if current_id not in visits:
        # Prioriza rascunhos e, depois, a avaliação mais recente.
        drafts = [
            (inspection_id, inspection)
            for inspection_id, inspection in visits.items()
            if inspection.get("status") != "Finalizada"
        ]
        pool = drafts or list(visits.items())
        pool.sort(key=lambda item: item[1].get("updated_at", ""), reverse=True)
        current_id = pool[0][0] if pool else ""

    labels = list(options.keys())
    ids = list(options.values())
    if desired_id in ids:
        st.session_state["field_inspection_select"] = labels[ids.index(desired_id)]
    elif "field_inspection_select" not in st.session_state and current_id in ids:
        st.session_state["field_inspection_select"] = labels[ids.index(current_id)]

    selected_label = st.selectbox(
        "Avaliação em andamento",
        labels,
        key="field_inspection_select",
        help="O aplicativo abre direto no formulário. Escolha uma avaliação existente ou crie outra.",
    )
    selected_id = options[selected_label]
    if selected_id == "__new__":
        return _create_new_inspection()

    st.session_state["field_inspection_id"] = selected_id
    return selected_id


def render_field_form_view():
    render_acnnorte_logo(size="medium", subtitle="Formulário de Campo — Avaliação de Segurança do Trabalho")

    visits = load_visits()
    if not visits:
        inspection_id = _create_new_inspection()
        if not inspection_id:
            render_empty_state("📝", "Não foi possível iniciar a avaliação", "Tente novamente.")
            return
        st.rerun()

    inspection_id = _select_inspection(visits)
    if inspection_id not in visits:
        st.rerun()

    inspection = visits[inspection_id]
    st.markdown(
        f"**Empresa:** {html.escape(str(inspection.get('empresa_nome') or inspection.get('client_name') or '—'))} "
        f"&nbsp;|&nbsp; **Avaliador:** {html.escape(str(inspection.get('technician') or st.session_state.get('username', '—')))} "
        f"&nbsp;|&nbsp; **Situação:** {status_badge(inspection.get('status', 'Rascunho'))}",
        unsafe_allow_html=True,
    )

    _render_header(inspection_id, inspection)
    inspection = _reload(inspection_id)

    st.markdown("---")
    _render_worker(inspection_id, inspection)
    inspection = _reload(inspection_id)

    st.markdown("---")
    _render_equipment(inspection_id, inspection)
    inspection = _reload(inspection_id)

    st.markdown("---")
    _render_epi_scanner(inspection_id, inspection)
    _render_checklist(inspection_id, inspection)

    st.markdown("---")
    _render_notes(inspection_id, inspection)

    st.markdown("---")
    resp, aval = _render_signatures(inspection_id, inspection)

    inspection = _reload(inspection_id)
    _render_actions(inspection_id, inspection, resp, aval)

    answered, total = visit_completion(inspection.get("forms") or {})
    st.caption(
        f"Progresso do checklist: {answered} de {total} campos obrigatórios. "
        "Todas as respostas são salvas neste dispositivo."
    )
