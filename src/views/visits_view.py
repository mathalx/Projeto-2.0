import base64
import html
import os
from datetime import date, datetime, time
from functools import partial

import streamlit as st

from src.equipment_catalog import equipment_grouped, equipment_label
from src.features.visit_enhancements.integration import (
    finalize_visit_guard,
    render_visit_enhancements_panel,
)
from src.form_template import (
    TECHNICAL_FORM_SECTIONS,
    UNANSWERED_LABEL,
    section_completion,
    visit_completion,
)
from src.components.photo_capture import clear_photo_input, photo_input
from src.geolocation import geolocation
from src.signature_pad import (
    signature_data_url,
    signature_pad,
    signature_state_has_drawing,
)
from src.storage_manager import (
    SIGNATURE_LABELS,
    SIGNATURE_ROLES,
    add_client,
    add_visit,
    get_caderno_avaliacao,
    get_visit_equipment,
    get_visit_measurements,
    load_clients,
    load_visits,
    remove_worker_photo,
    save_visit_equipment,
    save_visit_signature,
    save_visit_weather,
    save_worker_photo,
    first_pending_visit_step,
    update_visit,
    update_visit_measurement,
    update_worker_info,
    visit_has_signature,
)
from src.weather_service import (
    SOURCE_MANUAL,
    WeatherError,
    capture_weather_auto,
    format_humidity,
    format_temperature,
)
from src.ui_components import (
    CLIENTS_TAB_NEW,
    PAGE_CLIENTS,
    PAGE_PHOTOS,
    PAGE_VISITS,
    PHOTOS_TAB_GALLERY,
    VISITS_TAB_FILL,
    VISITS_TAB_LIST,
    VISITS_TAB_NEW,
    VISITS_TABS,
    navigate_to,
    record_sync,
    render_acnnorte_logo,
    render_empty_state,
    render_section_title,
    set_flash,
    set_pending_state,
    status_badge,
)

SECTIONS = list(TECHNICAL_FORM_SECTIONS.items())

# Etapas do preenchimento (após selecionar/criar visita)
FILL_STEP_IDENTIFICACAO = 0
FILL_STEP_EQUIPAMENTOS = 1
FILL_STEP_CADERNO = 2
FILL_TOTAL_STEPS = 3
FILL_STEP_TITLES = {
    FILL_STEP_IDENTIFICACAO: "Identificação da visita",
    FILL_STEP_EQUIPAMENTOS: "Equipamentos utilizados",
    FILL_STEP_CADERNO: "Caderno de Avaliação",
}


# ---------------------------------------------------------------------------
# Chaves de estado
# ---------------------------------------------------------------------------
def _draft_key(visit_id: str) -> str:
    return f"draft_{visit_id}"


def _step_key(visit_id: str) -> str:
    return f"form_step_{visit_id}"


def _field_key(visit_id: str, category: str, field_id: str) -> str:
    return f"form_{visit_id}_{category}_{field_id}"


def _obs_key(visit_id: str) -> str:
    return f"obs_{visit_id}"


def _conc_key(visit_id: str) -> str:
    return f"conc_{visit_id}"


def _status_key(visit_id: str) -> str:
    return f"status_{visit_id}"


def _signature_key(visit_id: str, role: str, suffix: str) -> str:
    return f"signature_{visit_id}_{role}_{suffix}"


def _caderno_key(visit_id: str, field: str) -> str:
    return f"caderno_{visit_id}_{field}"


def _select_visits_tab() -> str:
    if st.session_state.get("visits_tab") not in VISITS_TABS:
        st.session_state["visits_tab"] = VISITS_TAB_LIST
    return st.radio(
        "Seção de visitas",
        VISITS_TABS,
        key="visits_tab",
        horizontal=True,
        label_visibility="collapsed",
    )


# ---------------------------------------------------------------------------
# Utilidades e identificação
# ---------------------------------------------------------------------------
def _visit_date_label(visit: dict) -> str:
    start = str(visit.get("date_start") or visit.get("date") or "").strip()
    end = str(visit.get("date_end") or "").strip()
    if start and end and end != start:
        return f"{start} a {end}"
    return start or "—"


def _parse_date_safe(value):
    """Converte datas de forma segura para datetime.date (ou None)."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except Exception:
            continue
    # tenta ISO com horário
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except Exception:
        return None


def _parse_time_safe(value):
    """Converte horários de forma segura para datetime.time (ou None)."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.time().replace(microsecond=0)
    if isinstance(value, time):
        return value.replace(microsecond=0)
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%H:%M", "%H:%M:%S", "%Hh%M"):
        try:
            return datetime.strptime(text, fmt).time().replace(microsecond=0)
        except Exception:
            continue
    return None


def _format_display_date(value) -> str:
    parsed = _parse_date_safe(value)
    if parsed:
        return parsed.strftime("%d/%m/%Y")
    text = str(value or "").strip()
    return text if text else "—"


def _as_date_value(value, fallback=None, allow_none=False):
    parsed = _parse_date_safe(value)
    if parsed is not None:
        return parsed
    if allow_none:
        return None
    return fallback or date.today()


def _as_time_value(value, allow_none=True):
    parsed = _parse_time_safe(value)
    if parsed is not None:
        return parsed
    return None if allow_none else time(0, 0)


def _visit_worker_name(visit: dict) -> str:
    worker = visit.get("worker") if isinstance(visit.get("worker"), dict) else {}
    name = str(worker.get("name") or visit.get("worker_name") or "").strip()
    return name


def visit_identification_label(visit: dict) -> str:
    """Identificação visual: DATA / NOME DO FUNCIONÁRIO / HORÁRIO."""
    data = _format_display_date(visit.get("date_start") or visit.get("date"))
    nome = _visit_worker_name(visit) or "Funcionário não identificado"
    horario = str(visit.get("horario") or "").strip() or "Horário não informado"
    return f"{data} / {nome} / {horario}"


def _display_status(status: str) -> str:
    text = str(status or "").strip()
    if not text or text.upper() == "N/A":
        return "Não visitado"
    return text


# ---------------------------------------------------------------------------
# Rascunho e salvamento automático
# ---------------------------------------------------------------------------
def _build_draft(visit: dict) -> dict:
    forms = {}
    for cat_key in TECHNICAL_FORM_SECTIONS:
        forms[cat_key] = dict((visit.get("forms") or {}).get(cat_key, {}))
    status = visit.get("status", "Rascunho")
    if status not in ("Rascunho", "Em Andamento"):
        status = "Em Andamento"
    worker_name = _visit_worker_name(visit)
    worker_data = visit.get("worker", {}) if isinstance(visit.get("worker"), dict) else {}
    worker_photo = worker_data.get("photo_path") or visit.get("worker_photo", "")
    return {
        "forms": forms,
        "observations": visit.get("observations", ""),
        "conclusions": visit.get("conclusions", ""),
        "status": status,
        "worker_name": worker_name or "",
        "worker_photo": worker_photo or "",
        "client_id": visit.get("client_id", ""),
        "client_name": visit.get("client_name", ""),
        "date_start": visit.get("date_start") or visit.get("date") or "",
        "date_end": visit.get("date_end") or visit.get("date_start") or visit.get("date") or "",
        "horario": visit.get("horario", ""),
        "technician": visit.get("technician", ""),
        "caderno_avaliacao": get_caderno_avaliacao(visit),
    }


def _first_pending_step(visit: dict) -> int:
    """Usa a regra compartilhada de etapas pendentes (0/1/2)."""
    return first_pending_visit_step(visit)


def _collect_widgets(visit_id: str, draft: dict) -> dict:
    for cat_key, cat_info in SECTIONS:
        for field in cat_info["fields"]:
            key = _field_key(visit_id, cat_key, field["id"])
            if key in st.session_state:
                value = st.session_state[key]
                if value == UNANSWERED_LABEL:
                    value = ""
                draft["forms"].setdefault(cat_key, {})[field["id"]] = value

    obs_key = _obs_key(visit_id)
    if obs_key in st.session_state:
        draft["observations"] = st.session_state[obs_key]
    conc_key = _conc_key(visit_id)
    if conc_key in st.session_state:
        draft["conclusions"] = st.session_state[conc_key]
    status_key = _status_key(visit_id)
    if status_key in st.session_state:
        draft["status"] = st.session_state[status_key]
    worker_key = f"worker_name_{visit_id}"
    if worker_key in st.session_state:
        draft["worker_name"] = st.session_state[worker_key]

    caderno = draft.get("caderno_avaliacao") or {}
    for field in list(get_caderno_avaliacao({}).keys()):
        key = _caderno_key(visit_id, field)
        if key in st.session_state:
            caderno[field] = st.session_state[key]
    draft["caderno_avaliacao"] = caderno
    return draft


def _persist_draft(visit_id: str, draft: dict, status: str = None) -> bool:
    visits = load_visits()
    current = visits.get(visit_id, {})
    final_status = status or current.get("status", "Rascunho")
    success, _message = update_visit(
        visit_id,
        draft["forms"],
        draft.get("observations", ""),
        draft.get("conclusions", ""),
        final_status,
        worker={"name": draft.get("worker_name", "")},
        client_id=draft.get("client_id") or None,
        technician=draft.get("technician") or None,
        date_start=draft.get("date_start") or None,
        date_end=draft.get("date_end") or None,
        horario=draft.get("horario"),
        caderno_avaliacao=draft.get("caderno_avaliacao"),
    )
    if success:
        record_sync()
    return success


def _autosave_field(visit_id: str, category: str, field_id: str):
    draft = st.session_state.get(_draft_key(visit_id))
    if draft is None:
        return
    value = st.session_state.get(_field_key(visit_id, category, field_id), "")
    if value == UNANSWERED_LABEL:
        value = ""
    draft["forms"].setdefault(category, {})[field_id] = value
    _collect_widgets(visit_id, draft)
    _persist_draft(visit_id, draft)


def _autosave_text(visit_id: str, field: str):
    draft = st.session_state.get(_draft_key(visit_id))
    if draft is None:
        return
    key = _obs_key(visit_id) if field == "observations" else _conc_key(visit_id)
    if key in st.session_state:
        draft[field] = st.session_state[key]
    _collect_widgets(visit_id, draft)
    _persist_draft(visit_id, draft)


def _autosave_status(visit_id: str):
    draft = st.session_state.get(_draft_key(visit_id))
    key = _status_key(visit_id)
    if draft is None or key not in st.session_state:
        return
    draft["status"] = st.session_state[key]
    _collect_widgets(visit_id, draft)
    _persist_draft(visit_id, draft)


def _autosave_caderno(visit_id: str, field: str):
    draft = st.session_state.get(_draft_key(visit_id))
    if draft is None:
        return
    key = _caderno_key(visit_id, field)
    if key in st.session_state:
        draft.setdefault("caderno_avaliacao", {})[field] = st.session_state[key]
    _collect_widgets(visit_id, draft)
    _persist_draft(visit_id, draft)


def _open_visit_for_editing(visit: dict, step: int = None):
    visit_id = visit.get("id", "")
    st.session_state["active_visit_id"] = visit_id
    if step is None:
        step = _first_pending_step(visit)
    st.session_state[_step_key(visit_id)] = int(step)
    navigate_to(PAGE_VISITS, visits_tab=VISITS_TAB_FILL)


# ---------------------------------------------------------------------------
# Lista de visitas / ETAPA 1 VISITAS (empresas e visitas relacionadas)
# ---------------------------------------------------------------------------
def _render_orphan_visits(visits: dict, clients: dict):
    """Exibe visitas cuja empresa não está mais cadastrada, sem apagar dados."""
    client_ids = {str(cid) for cid in clients}
    orphans = [
        (v_id, visit)
        for v_id, visit in visits.items()
        if str(visit.get("client_id") or "") not in client_ids
    ]
    if not orphans:
        return

    orphans.sort(
        key=lambda item: str(item[1].get("date_start") or item[1].get("date") or ""),
        reverse=True,
    )
    st.markdown("---")
    with st.expander(
        f"🗂️ Visitas sem empresa vinculada ({len(orphans)}) — registros preservados",
        expanded=False,
    ):
        st.info(
            "Estas visitas pertencem a empresas que não estão mais no cadastro. "
            "Nenhum dado foi removido: abra a visita para consultar ou selecione uma "
            "empresa ativa na etapa de identificação, se desejar vincular o registro."
        )
        for v_id, visit in orphans:
            status = _display_status(visit.get("status", "Rascunho"))
            ident = visit_identification_label({**visit, "id": v_id})
            with st.container(border=True):
                st.markdown(f"**{ident}**")
                st.markdown(
                    f"Código: `{v_id}` &nbsp;|&nbsp; Situação: {status_badge(status)}",
                    unsafe_allow_html=True,
                )
                st.caption(
                    f"Empresa no registro: {str(visit.get('client_name') or '—')} "
                    f"(código: {str(visit.get('client_id') or '—')})"
                )
                if st.button(
                    "Abrir visita preservada",
                    key=f"open_orphan_{v_id}",
                    width="stretch",
                ):
                    _open_visit_for_editing({**visit, "id": v_id})


def _render_visits_overview(visits: dict, clients: dict):
    render_section_title(
        "Visitas — Empresas e visitas relacionadas",
        "Visualize as empresas, pesquise, selecione uma empresa e acesse suas visitas.",
        "🏢",
    )

    client_items = list(clients.items())
    search_company = st.text_input(
        "Pesquisar empresa",
        key="visits_company_search",
        placeholder="Nome da empresa, CNPJ ou responsável...",
    ).strip().lower()

    if search_company:
        client_items = [
            (cid, c)
            for cid, c in client_items
            if search_company
            in " ".join(
                [
                    str(c.get("name", "")),
                    str(c.get("cnpj", "")),
                    str(c.get("responsible", "")),
                    str(cid),
                ]
            ).lower()
        ]

    if not client_items:
        render_empty_state(
            "🏢",
            "Nenhuma empresa encontrada" if clients else "Nenhuma empresa cadastrada",
            "Cadastre uma empresa para iniciar visitas vinculadas a ela.",
        )
        if st.button("Ir para cadastro de clientes", key="visits_overview_go_clients", type="primary"):
            navigate_to(PAGE_CLIENTS, clients_tab=CLIENTS_TAB_NEW)
        _render_orphan_visits(visits, clients)
        return

    client_items.sort(key=lambda item: str(item[1].get("name", "")).lower())

    visits_by_client = {}
    for v_id, visit in visits.items():
        cid = str(visit.get("client_id") or "")
        visits_by_client.setdefault(cid, []).append((v_id, visit))

    st.caption(f"{len(client_items)} empresa(s) exibida(s).")

    for cid, client in client_items:
        company_name = client.get("name", "—")
        cnpj = client.get("cnpj", "—")
        company_visits = visits_by_client.get(cid, [])
        company_visits.sort(
            key=lambda item: str(item[1].get("date_start") or item[1].get("date") or ""),
            reverse=True,
        )
        header = f"🏢 {company_name} — {cnpj} • {len(company_visits)} visita(s)"
        with st.expander(header, expanded=(search_company != "" and len(client_items) <= 3)):
            col_info, col_actions = st.columns([2, 1])
            with col_info:
                st.markdown(f"**Responsável:** {client.get('responsible', '—')}")
                st.markdown(f"**Endereço:** {client.get('address', '—')}")
                st.markdown(f"**Telefone:** {client.get('phone', '—')}")
            with col_actions:
                if st.button(
                    "➕ Criar nova visita",
                    key=f"create_visit_for_{cid}",
                    type="primary",
                    width="stretch",
                ):
                    st.session_state["new_visit_client_id"] = cid
                    navigate_to(PAGE_VISITS, visits_tab=VISITS_TAB_NEW)

            st.markdown("**Visitas relacionadas**")
            if not company_visits:
                st.caption("Nenhuma visita registrada para esta empresa.")
            else:
                for v_id, visit in company_visits:
                    status = _display_status(visit.get("status", "Rascunho"))
                    ident = visit_identification_label({**visit, "id": v_id})
                    with st.container(border=True):
                        st.markdown(f"**{ident}**")
                        st.markdown(
                            f"Código: `{v_id}` &nbsp;|&nbsp; Situação: {status_badge(status)}",
                            unsafe_allow_html=True,
                        )
                        b1, b2 = st.columns(2)
                        with b1:
                            if st.button(
                                "Abrir visita",
                                key=f"open_v_{v_id}",
                                width="stretch",
                            ):
                                _open_visit_for_editing({**visit, "id": v_id})
                        with b2:
                            if status != "Finalizada":
                                if st.button(
                                    "Continuar visita",
                                    key=f"continue_v_{v_id}",
                                    type="primary",
                                    width="stretch",
                                ):
                                    _open_visit_for_editing({**visit, "id": v_id})
                            else:
                                if st.button(
                                    "Ver visita",
                                    key=f"view_v_{v_id}",
                                    width="stretch",
                                ):
                                    _open_visit_for_editing({**visit, "id": v_id}, step=FILL_STEP_CADERNO)

    _render_orphan_visits(visits, clients)

    st.markdown("---")
    st.caption("Selecione uma empresa para visualizar suas visitas, criar uma nova visita vinculada, abrir ou continuar uma visita.")


# ---------------------------------------------------------------------------
# Nova visita (vinculada à empresa selecionada quando aplicável)
# ---------------------------------------------------------------------------
def _render_new_visit(clients: dict):
    render_section_title(
        "Iniciar nova visita técnica",
        "Crie uma nova visita vinculada à empresa selecionada e identifique data, funcionário e horário.",
        "➕",
    )

    if not clients:
        render_empty_state(
            "🏢",
            "Cadastre um cliente primeiro",
            "É necessário ter pelo menos uma empresa cadastrada para iniciar uma visita.",
        )
        if st.button("Ir para cadastro de clientes", key="new_visit_go_clients", type="primary"):
            navigate_to(PAGE_CLIENTS, clients_tab=CLIENTS_TAB_NEW)
        return

    preselected = st.session_state.get("new_visit_client_id")
    client_options = {
        f"{c.get('name', '—')} — {c.get('cnpj', '—')}": c_id for c_id, c in clients.items()
    }
    labels = list(client_options.keys())
    ids = list(client_options.values())
    default_index = 0
    if preselected in ids:
        default_index = ids.index(preselected)

    with st.form("new_visit_form"):
        selected_client_label = st.selectbox(
            "Empresa cliente *",
            labels,
            index=default_index,
            key="new_visit_empresa_cliente",
        )
        technician_name = st.text_input(
            "Técnico/Avaliador responsável *",
            value=st.session_state.get("username", "Eng. Técnico"),
        )
        worker_name = st.text_input("Funcionário (identificação da visita)", placeholder="Nome do funcionário")
        col1, col2, col3 = st.columns(3)
        with col1:
            visit_start = st.date_input("Data da visita *", value=date.today(), key="new_visit_data_visita")
        with col2:
            visit_time = st.time_input(
                "Horário",
                value=time(hour=datetime.now().hour, minute=datetime.now().minute),
                key="new_visit_horario",
            )
        with col3:
            visit_end = st.date_input("Data de término", value=date.today(), key="new_visit_data_termino")

        submitted = st.form_submit_button("Iniciar visita", type="primary", width="stretch")
        if submitted:
            if not technician_name.strip():
                st.error("Informe o nome do técnico/avaliador responsável para iniciar a visita.")
            else:
                end_str = str(visit_end) if visit_end else str(visit_start)
                with st.spinner("Criando visita..."):
                    success, visit_id, _message = add_visit(
                        client_options[selected_client_label],
                        technician_name.strip(),
                        str(visit_start),
                        status="Em Andamento",
                        worker_name=worker_name.strip(),
                        date_start=str(visit_start),
                        date_end=end_str,
                        horario=visit_time.strftime("%H:%M") if visit_time else "",
                    )
                if success:
                    st.session_state.pop("new_visit_client_id", None)
                    st.session_state["active_visit_id"] = visit_id
                    st.session_state[_step_key(visit_id)] = FILL_STEP_IDENTIFICACAO
                    record_sync()
                    set_flash("Visita iniciada com sucesso! Continue pelo caderno de avaliação.")
                    navigate_to(PAGE_VISITS, visits_tab=VISITS_TAB_FILL)
                else:
                    st.error("Não foi possível iniciar a visita. Verifique os dados e tente novamente.")


# ---------------------------------------------------------------------------
# Temperatura e clima do local (reutilizado)
# ---------------------------------------------------------------------------
def _weather_key(visit_id: str, suffix: str) -> str:
    return f"weather_{visit_id}_{suffix}"


def _weather_of(visit: dict) -> dict:
    weather = visit.get("weather")
    return weather if isinstance(weather, dict) else {}


def _weather_location_label(weather: dict) -> str:
    city = str(weather.get("city") or "").strip()
    if city:
        return city
    latitude = weather.get("latitude")
    longitude = weather.get("longitude")
    try:
        return f"{float(latitude):.5f}, {float(longitude):.5f}"
    except (TypeError, ValueError):
        return "Local não identificado"


def _weather_source_label(source) -> str:
    return {
        "OpenWeather": "Clima externo • OpenWeather",
        "Open-Meteo": "Clima externo • Open-Meteo",
        "Manual": "Preenchimento manual",
    }.get(str(source or ""), "Origem não informada")


def _weather_optional(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _same_number(first, second) -> bool:
    try:
        return (
            first is not None
            and second is not None
            and abs(float(first) - float(second)) < 0.05
        )
    except (TypeError, ValueError):
        return False


def _capture_weather_for_visit(visit_id: str, latitude, longitude, weather: dict):
    lat, lon = latitude, longitude
    manual_lat = st.session_state.get(_weather_key(visit_id, "manual_lat"))
    manual_lon = st.session_state.get(_weather_key(visit_id, "manual_lon"))

    if lat is None or lon is None:
        if manual_lat and manual_lon:
            try:
                lat = float(str(manual_lat).replace(",", "."))
                lon = float(str(manual_lon).replace(",", "."))
            except ValueError:
                lat = lon = None
        elif weather.get("latitude") is not None and weather.get("longitude") is not None:
            lat, lon = weather.get("latitude"), weather.get("longitude")

    if lat is None or lon is None:
        st.error(
            "Não foi possível obter a localização do dispositivo. "
            "Autorize o GPS ou informe latitude e longitude no campo manual."
        )
        return

    with st.spinner("Consultando a temperatura do local..."):
        try:
            reading = capture_weather_auto(lat, lon)
        except WeatherError as exc:
            st.error(str(exc))
            return
        except Exception:
            st.error(
                "Não foi possível consultar o clima agora. Verifique a conexão "
                "e informe a temperatura manualmente."
            )
            return

    has_internal = st.session_state.get(
        _weather_key(visit_id, "has_internal"),
        weather.get("internal_temperature_c") is not None,
    )
    internal_temp = (
        st.session_state.get(
            _weather_key(visit_id, "internal_temp"),
            weather.get("internal_temperature_c"),
        )
        if has_internal
        else None
    )
    success, message = save_visit_weather(
        visit_id,
        reading.temperatura,
        reading.umidade,
        internal_temperature_c=internal_temp,
        description=reading.descricao,
        city=reading.cidade,
        latitude=reading.latitude,
        longitude=reading.longitude,
        source=reading.fonte,
        captured_at=reading.capturado_em,
    )
    if success:
        record_sync()
        set_pending_state(
            **{
                _weather_key(visit_id, "external_temp"): reading.temperatura,
                _weather_key(visit_id, "humidity"): reading.umidade,
            }
        )
        set_flash(
            f"Temperatura externa capturada ({reading.fonte}): "
            f"{format_temperature(reading.temperatura)} e umidade "
            f"{format_humidity(reading.umidade)}."
        )
        st.rerun()
    else:
        st.error(message)


def _render_weather_section(visit_id: str, visit: dict):
    weather = _weather_of(visit)
    geo_state = geolocation(key=_weather_key(visit_id, "geo"))
    gps_lat = geo_state.get("latitude")
    gps_lon = geo_state.get("longitude")

    st.markdown("#### 🌡️ Temperatura no local da visita (clima)")
    st.caption(
        "A temperatura externa é obtida do clima da localização informada e "
        "não substitui a temperatura da amostragem química registrada no caderno."
    )

    action_col, hint_col = st.columns([1, 2])
    with action_col:
        capture_clicked = st.button(
            "🌡️ Obter temperatura",
            key=_weather_key(visit_id, "get"),
            type="primary",
            width="stretch",
        )
    with hint_col:
        if gps_lat is not None and gps_lon is not None:
            st.caption(f"GPS disponível: {float(gps_lat):.5f}, {float(gps_lon):.5f}.")
        elif geo_state.get("error"):
            st.caption(str(geo_state["error"]))
        else:
            st.caption("Aguardando autorização de localização do dispositivo.")

    if capture_clicked:
        _capture_weather_for_visit(visit_id, gps_lat, gps_lon, weather)

    ext_key = _weather_key(visit_id, "external_temp")
    int_key = _weather_key(visit_id, "internal_temp")
    hum_key = _weather_key(visit_id, "humidity")
    has_internal_key = _weather_key(visit_id, "has_internal")
    st.session_state.setdefault(ext_key, _weather_optional(weather.get("temperature_c")))
    st.session_state.setdefault(int_key, _weather_optional(weather.get("internal_temperature_c")))
    st.session_state.setdefault(hum_key, _weather_optional(weather.get("humidity_pct")))
    st.session_state.setdefault(has_internal_key, weather.get("internal_temperature_c") is not None)

    has_internal = st.checkbox(
        "Registrar temperatura interna medida na empresa (opcional)",
        key=has_internal_key,
    )

    with st.container(border=True):
        if has_internal:
            col_ext, col_int, col_hum = st.columns(3)
        else:
            col_ext, col_hum = st.columns(2)
            col_int = None

        with col_ext:
            external_temp = st.number_input(
                "Temperatura externa (°C) — clima",
                min_value=-20.0,
                max_value=70.0,
                value=None,
                step=0.1,
                key=ext_key,
                placeholder="Não capturada",
            )
        if col_int is not None:
            with col_int:
                internal_temp = st.number_input(
                    "Temperatura interna medida (°C)",
                    min_value=-20.0,
                    max_value=70.0,
                    value=None,
                    step=0.1,
                    key=int_key,
                    placeholder="Não informada",
                )
        else:
            internal_temp = None
        with col_hum:
            humidity = st.number_input(
                "Umidade relativa (%)",
                min_value=0.0,
                max_value=100.0,
                value=None,
                step=1.0,
                key=hum_key,
                placeholder="Não informada",
            )

        if weather.get("captured_at"):
            st.caption(
                f"Origem: {_weather_source_label(weather.get('source'))} • "
                f"Local: {_weather_location_label(weather)} • "
                f"Consulta: {weather.get('captured_at')}"
            )

        if st.button(
            "💾 Salvar temperaturas",
            key=_weather_key(visit_id, "manual_save"),
            width="stretch",
        ):
            if external_temp is None:
                st.error("Informe a temperatura externa ou clique em “Obter temperatura”.")
            elif humidity is None:
                st.error("Informe a umidade relativa.")
            else:
                external_unchanged = _same_number(external_temp, weather.get("temperature_c"))
                if external_unchanged and weather.get("source"):
                    source = weather.get("source")
                    metadata = {
                        "description": weather.get("description", ""),
                        "city": weather.get("city", ""),
                        "latitude": weather.get("latitude"),
                        "longitude": weather.get("longitude"),
                        "captured_at": weather.get("captured_at"),
                    }
                else:
                    source = SOURCE_MANUAL
                    metadata = {
                        "latitude": st.session_state.get(_weather_key(visit_id, "manual_lat"))
                        or weather.get("latitude"),
                        "longitude": st.session_state.get(_weather_key(visit_id, "manual_lon"))
                        or weather.get("longitude"),
                    }
                internal_value = (
                    float(internal_temp) if has_internal and internal_temp is not None else None
                )
                success, message = save_visit_weather(
                    visit_id,
                    float(external_temp),
                    float(humidity),
                    internal_temperature_c=internal_value,
                    source=source,
                    **metadata,
                )
                if success:
                    record_sync()
                    set_flash("Temperaturas e umidade salvas.")
                    st.rerun()
                else:
                    st.error(message)

    with st.expander("Informar coordenadas manualmente", expanded=False):
        coord_col1, coord_col2 = st.columns(2)
        with coord_col1:
            st.text_input(
                "Latitude",
                value=str(weather.get("latitude") or ""),
                key=_weather_key(visit_id, "manual_lat"),
                placeholder="-23.5505",
            )
        with coord_col2:
            st.text_input(
                "Longitude",
                value=str(weather.get("longitude") or ""),
                key=_weather_key(visit_id, "manual_lon"),
                placeholder="-46.6333",
            )


# ---------------------------------------------------------------------------
# Campos do checklist NR (preservado)
# ---------------------------------------------------------------------------
def _render_field(visit_id: str, cat_key: str, field: dict, answers: dict):
    required = field.get("type") == "select"
    label = field["label"] + (" *" if required else "")
    key = _field_key(visit_id, cat_key, field["id"])
    current_value = answers.get(field["id"], "")

    if field["type"] == "select":
        options = [UNANSWERED_LABEL] + list(field.get("options", []))
        if key not in st.session_state:
            index = options.index(current_value) if current_value in options else 0
            st.selectbox(
                label,
                options,
                index=index,
                key=key,
                on_change=_autosave_field,
                args=(visit_id, cat_key, field["id"]),
            )
        else:
            st.selectbox(
                label,
                options,
                key=key,
                on_change=_autosave_field,
                args=(visit_id, cat_key, field["id"]),
            )
    else:
        if key not in st.session_state:
            st.text_area(
                label,
                value=str(current_value or ""),
                key=key,
                on_change=_autosave_field,
                args=(visit_id, cat_key, field["id"]),
            )
        else:
            st.text_area(
                label,
                key=key,
                on_change=_autosave_field,
                args=(visit_id, cat_key, field["id"]),
            )


def _validate_required(forms: dict):
    pending = []
    for cat_key, cat_info in SECTIONS:
        answered, total = section_completion(cat_key, forms.get(cat_key, {}))
        if answered < total:
            pending.append((cat_info["title"], total - answered))
    return pending


# ---------------------------------------------------------------------------
# Assinaturas digitais (preservado/reutilizado)
# ---------------------------------------------------------------------------
def _signatures_of(visit: dict) -> dict:
    signatures = visit.get("signatures")
    return signatures if isinstance(signatures, dict) else {}


def _saved_signature_data_url(signature: dict) -> str:
    path = signature.get("path") if isinstance(signature, dict) else None
    if not path or not os.path.exists(path):
        return ""
    try:
        with open(path, "rb") as file:
            encoded = base64.b64encode(file.read()).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    except Exception:
        return ""


def _save_signature_name(visit_id: str, role: str):
    key = _signature_key(visit_id, role, "name")
    name = st.session_state.get(key, "")
    success, message = save_visit_signature(visit_id, role, name=name)
    if success:
        record_sync()
    else:
        st.session_state["_signature_error"] = message


def _on_signature_change(visit_id: str, role: str, key: str):
    state = st.session_state.get(key, {})
    data_url = signature_data_url(state)
    success, message = save_visit_signature(visit_id, role, data_url=data_url)
    if success:
        record_sync()
    else:
        st.session_state["_signature_error"] = message


def _persist_signatures(visit_id: str) -> bool:
    ok = True
    for role in SIGNATURE_ROLES:
        name_key = _signature_key(visit_id, role, "name")
        pad_key = _signature_key(visit_id, role, "pad")
        name_present = name_key in st.session_state
        state = st.session_state.get(pad_key)
        drawing_present = signature_state_has_drawing(state)
        if not name_present and not drawing_present:
            continue
        name = st.session_state.get(name_key, "") if name_present else None
        if drawing_present:
            success, _ = save_visit_signature(
                visit_id, role, data_url=signature_data_url(state), name=name
            )
        else:
            success, _ = save_visit_signature(visit_id, role, name=name)
        ok = ok and success
    if ok:
        record_sync()
    return ok


def _render_signatures_section(visit_id: str, visit: dict, read_only: bool = False):
    st.markdown("#### Responsáveis e assinaturas (reutilizadas)")
    st.caption(
        "As assinaturas existentes são reutilizadas. Ambas permanecem obrigatórias para finalizar a visita, "
        "mas não para salvar um rascunho. Registros eletrônicos sem validade jurídica automática."
    )

    signatures = _signatures_of(visit)
    if read_only:
        for role in SIGNATURE_ROLES:
            label = SIGNATURE_LABELS[role]
            signature = signatures.get(role)
            if not isinstance(signature, dict):
                signature = {}
            name = str(signature.get("name") or "").strip() or "Não informado"
            st.markdown(f"**{label}:** {name}")
            if visit_has_signature(visit, role):
                st.caption(
                    f"Assinatura registrada em {signature.get('signed_at') or 'data não informada'}."
                )
                st.image(signature.get("path"), width=320)
            else:
                st.caption("Não assinado.")
        return

    for role in SIGNATURE_ROLES:
        label = SIGNATURE_LABELS[role]
        signature = signatures.get(role)
        if not isinstance(signature, dict):
            signature = {}
        with st.container(border=True):
            st.markdown(f"**{label}**")
            name_key = _signature_key(visit_id, role, "name")
            st.session_state.setdefault(name_key, signature.get("name", ""))
            st.text_input(
                f"Nome do {label} *",
                key=name_key,
                placeholder="Nome completo",
                on_change=_save_signature_name,
                args=(visit_id, role),
            )
            pad_key = _signature_key(visit_id, role, "pad")
            signature_pad(
                key=pad_key,
                image=_saved_signature_data_url(signature),
                on_change=partial(_on_signature_change, visit_id, role, pad_key),
            )
            if visit_has_signature(visit, role):
                st.caption(
                    f"Assinatura registrada em {signature.get('signed_at') or 'data não informada'}."
                )
                with st.expander("Visualizar assinatura salva", expanded=False):
                    st.image(signature.get("path"), width=320)
            else:
                st.caption("Ainda não assinado.")

    if st.button("💾 Salvar assinaturas", key=_signature_key(visit_id, "all", "save"), type="primary", width="stretch"):
        if _persist_signatures(visit_id):
            set_flash("Assinaturas salvas.")
            st.rerun()
        else:
            st.error("Não foi possível salvar as assinaturas.")

    error = st.session_state.pop("_signature_error", None)
    if error:
        st.error(error)


# ---------------------------------------------------------------------------
# Equipamentos (ETAPA 3) - reutiliza lógica existente
# ---------------------------------------------------------------------------
def _equipment_summary(visit: dict) -> str:
    labels = [equipment_label(item) for item in get_visit_equipment(visit)]
    return ", ".join(labels) if labels else "Nenhum equipamento selecionado"


def _toggle_equipment(visit_id: str, code: str):
    visit = load_visits().get(visit_id, {})
    codes = {
        str(item.get("codigo"))
        for item in get_visit_equipment(visit)
        if item.get("codigo")
    }
    if code in codes:
        codes.remove(code)
    else:
        codes.add(code)
    success, message = save_visit_equipment(visit_id, list(codes))
    if success:
        record_sync()
    else:
        st.session_state["_equipment_error"] = message


def _save_measurement_time(visit_id: str, code: str, widget_key: str):
    horario = str(st.session_state.get(widget_key, "") or "").strip()
    success, message = update_visit_measurement(visit_id, code, horario=horario)
    if success:
        record_sync()
    else:
        st.session_state["_equipment_error"] = message


def _render_equipamentos_step(visit_id: str, visit: dict):
    render_section_title(
        "Equipamentos utilizados",
        "Selecione os equipamentos utilizados na visita (catálogo existente). O equipamento 3440 está disponível conforme o cadastro.",
        "🧰",
    )

    read_only = visit.get("status") == "Finalizada"
    selected = get_visit_equipment(visit)
    selected_codes = {str(item.get("codigo")) for item in selected if item.get("codigo")}

    if not read_only:
        grouped = equipment_grouped()
        for category, brands in grouped.items():
            st.markdown(f"#### {category}")
            for brand, items in brands.items():
                st.markdown(f"**{brand}**")
                columns_per_row = 3
                for start in range(0, len(items), columns_per_row):
                    row = items[start : start + columns_per_row]
                    columns = st.columns(len(row))
                    for column, item in zip(columns, row):
                        code = item["codigo"]
                        with column:
                            st.button(
                                item["identificacao"],
                                key=f"equipment_{visit_id}_{code}",
                                type=("primary" if code in selected_codes else "secondary"),
                                width="stretch",
                                on_click=_toggle_equipment,
                                args=(visit_id, code),
                                help=equipment_label(item),
                            )

    measurements = {str(m.get("equipment_code")): m for m in get_visit_measurements(visit)}

    st.markdown("#### Identificação vinculada (horário + equipamento)")
    if not selected:
        st.info("Nenhum equipamento selecionado. Você pode adicionar equipamentos agora ou antes de finalizar.")
    else:
        for index, item in enumerate(selected, start=1):
            code = str(item.get("codigo"))
            measurement = measurements.get(code, {})
            base_label = equipment_label(item)
            with st.container(border=True):
                st.markdown(f"**Equipamento {index}:** {base_label}")
                time_key = f"equip_time_{visit_id}_{code}"
                current_time = str(measurement.get("horario") or item.get("horario") or "")
                if time_key not in st.session_state:
                    st.session_state[time_key] = current_time
                if read_only:
                    registro = measurement.get("identificacao_registro") or base_label
                    st.markdown(f"**Identificação do registro:** {registro}")
                    st.caption(f"Medição vinculada: {measurement.get('id', '—')}")
                else:
                    st.text_input(
                        "Horário (HH:MM)",
                        key=time_key,
                        placeholder="08:30",
                        on_change=_save_measurement_time,
                        args=(visit_id, code, time_key),
                    )
                    horario = str(st.session_state.get(time_key, "") or "").strip()
                    registro = f"{horario} — {base_label}" if horario else base_label
                    st.caption(f"Identificação do registro: **{registro}**")
                    st.caption(f"Medição vinculada: {measurement.get('id', '—')}")

    error = st.session_state.pop("_equipment_error", None)
    if error:
        st.error(error)


# ---------------------------------------------------------------------------
# Identificação da visita (ETAPA 2 do preenchimento)
# ---------------------------------------------------------------------------
def _render_identificacao_step(visit_id: str, visit: dict, draft: dict):
    render_section_title(
        "Identificação da visita",
        "Confirme a empresa, a data, o horário e o funcionário para identificar a visita.",
        "🪪",
    )

    clients = load_clients()
    current_client_id = str(draft.get("client_id") or visit.get("client_id") or "")
    client = clients.get(current_client_id, {})

    with st.container(border=True):
        st.markdown("#### Empresa da visita")
        if clients:
            options = {"— Selecionar empresa —": ""}
            for c_id, c in clients.items():
                options[f"{c.get('name', '—')} — {c.get('cnpj', '—')}"] = c_id
            labels = list(options.keys())
            ids = list(options.values())
            default_index = ids.index(current_client_id) if current_client_id in ids else 0
            selected_label = st.selectbox(
                "Empresa (cadastro existente) *",
                labels,
                index=default_index,
                key=f"visit_client_{visit_id}",
            )
            selected_id = options[selected_label]
            if selected_id and selected_id != current_client_id:
                draft["client_id"] = selected_id
                draft["client_name"] = clients[selected_id].get("name", "")
                draft.setdefault("caderno_avaliacao", {})["empresa_avaliada"] = draft["client_name"]
                _persist_draft(visit_id, draft)
                set_flash("Empresa da visita atualizada.")
                st.rerun()
        else:
            st.info("Nenhuma empresa cadastrada. Cadastre uma empresa para vincular à visita.")

        if client:
            st.caption(
                f"CNPJ: {client.get('cnpj', '—')} • Responsável: {client.get('responsible', '—')} • "
                f"Endereço: {client.get('address', '—')}"
            )
        elif current_client_id:
            st.warning("A empresa vinculada não foi encontrada. Selecione outra empresa.")

    with st.container(border=True):
        st.markdown("#### Data, horário e responsável")
        c1, c2, c3 = st.columns(3)
        with c1:
            date_start = st.date_input(
                "Data da visita *",
                value=_as_date_value(draft.get("date_start") or draft.get("date")),
                key=f"visit_date_start_{visit_id}",
            )
        with c2:
            current_time = _as_time_value(draft.get("horario") or visit.get("horario"))
            if current_time is None:
                current_time = time(hour=datetime.now().hour, minute=datetime.now().minute)
            visit_time = st.time_input("Horário *", value=current_time, key=f"visit_horario_{visit_id}")
        with c3:
            date_end = st.date_input(
                "Data de término",
                value=_as_date_value(draft.get("date_end") or draft.get("date_start") or draft.get("date")),
                key=f"visit_date_end_{visit_id}",
            )

        technician = st.text_input(
            "Técnico/Avaliador responsável *",
            value=str(draft.get("technician") or visit.get("technician") or st.session_state.get("username", "")),
            key=f"visit_technician_{visit_id}",
        )
        worker_name = st.text_input(
            "Funcionário (identificação da visita)",
            value=str(draft.get("worker_name") or ""),
            key=f"visit_worker_name_{visit_id}",
            placeholder="Nome do funcionário",
            help="Utilize os dados já existentes na visita quando disponíveis.",
        )

        if st.button("💾 Salvar identificação", key=f"save_ident_{visit_id}", type="primary", width="stretch"):
            if not technician.strip():
                st.error("Informe o técnico/avaliador responsável.")
            elif date_end < date_start:
                st.error("A data de término não pode ser anterior à data de início.")
            else:
                draft["date_start"] = str(date_start)
                draft["date_end"] = str(date_end)
                draft["horario"] = visit_time.strftime("%H:%M") if visit_time else ""
                draft["technician"] = technician.strip()
                draft["worker_name"] = worker_name.strip()
                caderno = draft.setdefault("caderno_avaliacao", {})
                if draft.get("client_name") and not caderno.get("empresa_avaliada"):
                    caderno["empresa_avaliada"] = draft.get("client_name", "")
                if worker_name.strip() and not caderno.get("funcionario"):
                    caderno["funcionario"] = worker_name.strip()
                if technician.strip() and not caderno.get("avaliador"):
                    caderno["avaliador"] = technician.strip()
                if _persist_draft(visit_id, draft):
                    update_worker_info(visit_id, worker_name.strip())
                    set_flash("Identificação da visita salva.")
                    st.rerun()
                else:
                    st.error("Não foi possível salvar a identificação.")

    st.info(f"Identificação: **{visit_identification_label({**visit, **draft, 'id': visit_id})}**")

    with st.expander("Condições ambientais da visita (clima externo) — opcional", expanded=False):
        _render_weather_section(visit_id, visit)


# ---------------------------------------------------------------------------
# Caderno de Avaliação (ETAPA 4) - etapa principal
# ---------------------------------------------------------------------------
def _sync_caderno_date_time_widgets(visit_id: str, draft: dict, fields: list[tuple[str, str]]):
    caderno = draft.setdefault("caderno_avaliacao", {})
    changed = False
    for field, kind in fields:
        key = _caderno_key(visit_id, field)
        if key not in st.session_state:
            continue
        val = st.session_state.get(key)
        current = str(caderno.get(field) or "")
        if kind == "date":
            if isinstance(val, datetime):
                sval = val.date().isoformat()
            elif isinstance(val, date):
                sval = val.isoformat()
            elif val is None or val == "":
                # Não sobrescrever valor original não parseável/vazio indevidamente
                if current and _parse_date_safe(current) is None:
                    continue
                sval = ""
            else:
                parsed = _parse_date_safe(val)
                if parsed:
                    sval = parsed.isoformat()
                elif current and _parse_date_safe(current) is None:
                    continue
                else:
                    sval = str(val).strip()
        elif kind == "time":
            if isinstance(val, datetime):
                sval = val.time().strftime("%H:%M")
            elif isinstance(val, time):
                sval = val.strftime("%H:%M")
            elif val is None or val == "":
                if current and _parse_time_safe(current) is None:
                    continue
                sval = ""
            else:
                parsed = _parse_time_safe(val)
                if parsed:
                    sval = parsed.strftime("%H:%M")
                elif current and _parse_time_safe(current) is None:
                    continue
                else:
                    sval = str(val).strip()
        else:
            sval = "" if val is None else str(val)
        if current != sval:
            caderno[field] = sval
            changed = True
    if changed:
        _persist_draft(visit_id, draft)
    return changed


def _render_worker_photo_block(visit_id: str, visit: dict, draft: dict, read_only: bool = False):
    st.markdown("#### Funcionário avaliado (foto)")
    worker_photo = (
        (visit.get("worker") or {}).get("photo_path")
        if isinstance(visit.get("worker"), dict)
        else ""
    ) or visit.get("worker_photo") or draft.get("worker_photo") or ""
    worker_name = draft.get("worker_name") or _visit_worker_name(visit) or "Funcionário"

    if worker_photo and os.path.exists(worker_photo):
        st.image(worker_photo, caption=worker_name, width=180)
    else:
        st.caption("Sem fotografia do funcionário.")

    if not read_only:
        photo_key = f"worker_photo_input_{visit_id}"
        photo_bytes = photo_input(
            "Fotografia do funcionário",
            key=photo_key,
            default_camera="environment",
        )
        if photo_bytes is not None and st.button(
            "Salvar foto do funcionário",
            key=f"save_worker_photo_{visit_id}",
            width="stretch",
        ):
            success, path, message = save_worker_photo(
                visit_id, photo_bytes, "funcionario.jpg", validate_photo=True
            )
            if success:
                clear_photo_input(photo_key)
                draft["worker_photo"] = path
                record_sync()
                set_flash(message)
                st.rerun()
            else:
                st.error(message)
        if worker_photo and os.path.exists(worker_photo) and st.button(
            "Remover foto do funcionário",
            key=f"remove_worker_photo_{visit_id}",
            width="stretch",
        ):
            success, message = remove_worker_photo(visit_id)
            if success:
                draft["worker_photo"] = ""
                record_sync()
                set_flash(message)
                st.rerun()
            else:
                st.error(message)


def _render_caderno_step(visit_id: str, visit: dict, draft: dict):
    render_section_title(
        "Caderno de Avaliação de Agentes Químicos",
        "Etapa principal da avaliação. Preencha os blocos abaixo, salve e finalize ou continue a visita.",
        "📓",
    )

    clients = load_clients()
    client = clients.get(str(draft.get("client_id") or visit.get("client_id") or ""), {})
    caderno = draft.setdefault("caderno_avaliacao", get_caderno_avaliacao(visit))

    # Prefill a partir de dados existentes (sem sobrescrever)
    if not caderno.get("empresa_avaliada"):
        caderno["empresa_avaliada"] = client.get("name") or draft.get("client_name") or visit.get("client_name", "")
    if not caderno.get("funcionario"):
        caderno["funcionario"] = draft.get("worker_name") or _visit_worker_name(visit)
    if not caderno.get("avaliador"):
        caderno["avaliador"] = str(draft.get("technician") or visit.get("technician") or "")

    # Bloco A — Identificação da empresa
    with st.container(border=True):
        st.markdown("#### 1. Empresa")
        a1, a2, a3 = st.columns([2, 1, 1])
        with a1:
            st.text_input("Empresa Avaliada", value=str(caderno.get("empresa_avaliada") or ""),
                          key=_caderno_key(visit_id, "empresa_avaliada"), on_change=_autosave_caderno, args=(visit_id, "empresa_avaliada"),
                          help="Reutiliza a empresa selecionada na visita.")
        with a2:
            st.text_input("Unidade", value=str(caderno.get("unidade") or ""),
                          key=_caderno_key(visit_id, "unidade"), on_change=_autosave_caderno, args=(visit_id, "unidade"))
        with a3:
            st.text_input("Estado", value=str(caderno.get("estado") or ""),
                          key=_caderno_key(visit_id, "estado"), on_change=_autosave_caderno, args=(visit_id, "estado"))

    # Bloco B — Agente químico e amostragem
    with st.container(border=True):
        st.markdown("#### 2. Amostragem")
        b1, b2, b3 = st.columns(3)
        with b1:
            st.text_input("Agente Químico", value=str(caderno.get("agente_quimico") or ""),
                          key=_caderno_key(visit_id, "agente_quimico"), on_change=_autosave_caderno, args=(visit_id, "agente_quimico"))
            da_key = _caderno_key(visit_id, "data_amostragem")
            raw_da = caderno.get("data_amostragem") or ""
            if da_key not in st.session_state:
                parsed_da = _parse_date_safe(raw_da) or _parse_date_safe(draft.get("date_start"))
                st.session_state[da_key] = parsed_da  # date ou None (não força sobrescrita indevida)
            elif not isinstance(st.session_state.get(da_key), (date, type(None))) or isinstance(st.session_state.get(da_key), datetime):
                st.session_state[da_key] = _parse_date_safe(st.session_state.get(da_key))
            st.date_input(
                "Data de Amostragem",
                value=st.session_state.get(da_key) if isinstance(st.session_state.get(da_key), date) and not isinstance(st.session_state.get(da_key), datetime) else None,
                key=da_key,
            )
            st.text_input("Identificação da Amostra", value=str(caderno.get("identificacao_amostra") or ""),
                          key=_caderno_key(visit_id, "identificacao_amostra"), on_change=_autosave_caderno, args=(visit_id, "identificacao_amostra"))
        with b2:
            hi_key = _caderno_key(visit_id, "hora_inicial")
            hf_key = _caderno_key(visit_id, "hora_final")
            for tkey, raw in ((hi_key, caderno.get("hora_inicial")), (hf_key, caderno.get("hora_final"))):
                if tkey not in st.session_state:
                    st.session_state[tkey] = _parse_time_safe(raw)
                elif not isinstance(st.session_state.get(tkey), (time, type(None))) or isinstance(st.session_state.get(tkey), datetime):
                    st.session_state[tkey] = _parse_time_safe(st.session_state.get(tkey))
            st.time_input(
                "Hora Inicial",
                value=st.session_state.get(hi_key) if isinstance(st.session_state.get(hi_key), time) else None,
                key=hi_key,
            )
            st.time_input(
                "Hora Final",
                value=st.session_state.get(hf_key) if isinstance(st.session_state.get(hf_key), time) else None,
                key=hf_key,
            )
            st.text_input("Vazão (L/Min)", value=str(caderno.get("vazao_l_min") or ""),
                          key=_caderno_key(visit_id, "vazao_l_min"), on_change=_autosave_caderno, args=(visit_id, "vazao_l_min"))
        with b3:
            st.text_input("Temperatura (amostragem)", value=str(caderno.get("temperatura_amostragem") or ""),
                          key=_caderno_key(visit_id, "temperatura_amostragem"), on_change=_autosave_caderno, args=(visit_id, "temperatura_amostragem"),
                          help="Temperatura da amostragem química (diferente da temperatura meteorológica da visita).")

    # Bloco C — Identificação do trabalhador
    with st.container(border=True):
        st.markdown("#### 3. Funcionário")
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Setor", value=str(caderno.get("setor") or ""),
                          key=_caderno_key(visit_id, "setor"), on_change=_autosave_caderno, args=(visit_id, "setor"))
            st.text_input("Funcionário", value=str(caderno.get("funcionario") or draft.get("worker_name") or ""),
                          key=_caderno_key(visit_id, "funcionario"), on_change=_autosave_caderno, args=(visit_id, "funcionario"))
        with c2:
            st.text_input("Função", value=str(caderno.get("funcao") or ""),
                          key=_caderno_key(visit_id, "funcao"), on_change=_autosave_caderno, args=(visit_id, "funcao"))
            st.text_input("Matrícula", value=str(caderno.get("matricula") or ""),
                          key=_caderno_key(visit_id, "matricula"), on_change=_autosave_caderno, args=(visit_id, "matricula"),
                          help="Utilize a matrícula do cadastro existente quando disponível.")

    # Bloco D — Atividades desenvolvidas
    with st.container(border=True):
        st.markdown("#### 4. Atividades")
        st.text_area("Atividades desenvolvidas", value=str(caderno.get("atividades_desenvolvidas") or ""),
                     key=_caderno_key(visit_id, "atividades_desenvolvidas"), on_change=_autosave_caderno,
                     args=(visit_id, "atividades_desenvolvidas"), height=180,
                     placeholder="Descreva as atividades desenvolvidas pelo funcionário...")

    # Bloco E — EPI e EPC
    with st.container(border=True):
        st.markdown("#### 5. EPI e EPC")
        e1, e2 = st.columns(2)
        with e1:
            st.text_area("EPI", value=str(caderno.get("epi") or ""),
                         key=_caderno_key(visit_id, "epi"), on_change=_autosave_caderno, args=(visit_id, "epi"),
                         height=120, placeholder="Descreva os EPIs utilizados...")
        with e2:
            st.text_area("EPC", value=str(caderno.get("epc") or ""),
                         key=_caderno_key(visit_id, "epc"), on_change=_autosave_caderno, args=(visit_id, "epc"),
                         height=120, placeholder="Descreva os EPCs e medidas de proteção...")

    # Bloco F — Observações
    with st.container(border=True):
        st.markdown("#### 6. Observações")
        st.text_area("Obs.", value=str(caderno.get("obs") or ""),
                     key=_caderno_key(visit_id, "obs"), on_change=_autosave_caderno, args=(visit_id, "obs"),
                     height=140, placeholder="Observações complementares da avaliação...")

    # Bloco G — Responsáveis e avaliador
    with st.container(border=True):
        st.markdown("#### 7. Responsáveis e avaliador")
        g1, g2 = st.columns(2)
        with g1:
            st.text_input("Funcionário / Responsável",
                          value=str(caderno.get("responsavel_funcionario") or caderno.get("funcionario") or draft.get("worker_name") or ""),
                          key=_caderno_key(visit_id, "responsavel_funcionario"), on_change=_autosave_caderno, args=(visit_id, "responsavel_funcionario"))
            st.text_input("Nome", value=str(caderno.get("nome_responsavel") or ""),
                          key=_caderno_key(visit_id, "nome_responsavel"), on_change=_autosave_caderno, args=(visit_id, "nome_responsavel"))
        with g2:
            st.text_input("Avaliador", value=str(caderno.get("avaliador") or draft.get("technician") or ""),
                          key=_caderno_key(visit_id, "avaliador"), on_change=_autosave_caderno, args=(visit_id, "avaliador"))
            st.text_input("Nome do Avaliador",
                          value=str(caderno.get("nome_avaliador") or caderno.get("avaliador") or draft.get("technician") or ""),
                          key=_caderno_key(visit_id, "nome_avaliador"), on_change=_autosave_caderno, args=(visit_id, "nome_avaliador"))

    _sync_caderno_date_time_widgets(visit_id, draft, [("data_amostragem", "date"), ("hora_inicial", "time"), ("hora_final", "time")])

    # Seções preservadas
    st.markdown("---")
    with st.expander("Funcionário avaliado e fotografia (registro existente)", expanded=False):
        _render_worker_photo_block(visit_id, visit, draft, read_only=(visit.get("status") == "Finalizada"))

    with st.expander("Checklist técnico normativo (preservado)", expanded=False):
        st.caption("Formulário técnico existente preservado para compatibilidade.")
        for cat_key, cat_info in SECTIONS:
            answered, total = section_completion(cat_key, draft["forms"].get(cat_key, {}))
            with st.expander(f"{cat_info['title']} — {answered}/{total} obrigatórios", expanded=False):
                answers = draft["forms"].get(cat_key, {})
                for field in cat_info["fields"]:
                    _render_field(visit_id, cat_key, field, answers)

    with st.expander("Observações e conclusões gerais da visita (preservadas)", expanded=False):
        obs_key = _obs_key(visit_id)
        if obs_key not in st.session_state:
            st.text_area("Observações gerais da visita", value=draft.get("observations", ""), key=obs_key,
                         on_change=_autosave_text, args=(visit_id, "observations"))
        else:
            st.text_area("Observações gerais da visita", key=obs_key, on_change=_autosave_text, args=(visit_id, "observations"))
        conc_key = _conc_key(visit_id)
        if conc_key not in st.session_state:
            st.text_area("Conclusões e recomendações de segurança", value=draft.get("conclusions", ""), key=conc_key,
                         on_change=_autosave_text, args=(visit_id, "conclusions"))
        else:
            st.text_area("Conclusões e recomendações de segurança", key=conc_key, on_change=_autosave_text, args=(visit_id, "conclusions"))

    _render_signatures_section(visit_id, visit, read_only=(visit.get("status") == "Finalizada"))

    st.markdown("---")
    fresh_visit = load_visits().get(visit_id, visit)
    st.markdown(f"**Equipamentos selecionados:** {_equipment_summary(fresh_visit)}")

    current_status = visit.get("status", "Rascunho")
    if current_status != "Finalizada":
        status_key = _status_key(visit_id)
        options = ["Rascunho", "Em Andamento"]
        if status_key not in st.session_state:
            default = draft.get("status", "Em Andamento")
            index = options.index(default) if default in options else 1
            st.selectbox("Situação da visita", options, index=index, key=status_key,
                         on_change=_autosave_status, args=(visit_id,))
        else:
            st.selectbox("Situação da visita", options, key=status_key, on_change=_autosave_status, args=(visit_id,))

    action_cols = st.columns(3)
    with action_cols[0]:
        if st.button("💾 Salvar caderno", key=f"save_caderno_{visit_id}", type="primary", width="stretch"):
            _collect_widgets(visit_id, draft)
            _sync_caderno_date_time_widgets(visit_id, draft, [("data_amostragem", "date"), ("hora_inicial", "time"), ("hora_final", "time")])
            _persist_signatures(visit_id)
            if _persist_draft(visit_id, draft):
                set_flash("Caderno de avaliação salvo com sucesso.")
                st.rerun()
            else:
                st.error("Não foi possível salvar o caderno.")
    with action_cols[1]:
        if st.button("📷 Fotografias da visita", key=f"caderno_photos_{visit_id}", width="stretch"):
            _collect_widgets(visit_id, draft)
            _persist_draft(visit_id, draft)
            st.session_state["active_visit_id"] = visit_id
            st.session_state["photo_active_visit_id"] = visit_id
            navigate_to(PAGE_PHOTOS, photos_tab=PHOTOS_TAB_GALLERY)
    with action_cols[2]:
        if current_status != "Finalizada":
            if st.button("✅ Finalizar visita", key=f"finalize_caderno_{visit_id}", type="primary", width="stretch"):
                _collect_widgets(visit_id, draft)
                _sync_caderno_date_time_widgets(visit_id, draft, [("data_amostragem", "date"), ("hora_inicial", "time"), ("hora_final", "time")])
                _persist_signatures(visit_id)
                _persist_draft(visit_id, draft)
                pending = _validate_required(draft["forms"])
                fresh_visit2 = load_visits().get(visit_id, visit)
                # Validação compartilhada com o pacote modular de extensões.
                equipment_and_signatures_ok, extra_problems = finalize_visit_guard(fresh_visit2)
                problems = []
                if pending:
                    detail = "; ".join(f"{title}: {count} pendente(s)" for title, count in pending)
                    problems.append(f"Checklist técnico pendente: {detail}.")
                if not equipment_and_signatures_ok:
                    problems.extend(f"{problem}." for problem in extra_problems)
                if problems:
                    st.error(" ".join(problems))
                else:
                    st.session_state["finalize_pending"] = visit_id
        else:
            st.success("Esta visita está finalizada.")

    if st.session_state.get("finalize_pending") == visit_id and current_status != "Finalizada":
        st.warning("Confirmar a finalização desta visita? Depois de finalizada, ela ficará pronta para relatório.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Sim, finalizar", key=f"confirm_finalize_{visit_id}", type="primary", width="stretch"):
                _collect_widgets(visit_id, draft)
                _persist_signatures(visit_id)
                with st.spinner("Finalizando visita..."):
                    success = _persist_draft(visit_id, draft, status="Finalizada")
                st.session_state.pop("finalize_pending", None)
                if success:
                    st.session_state["draft_loaded_vid"] = None
                    set_flash("Visita finalizada com sucesso! Pronta para geração de relatório.")
                    st.rerun()
                else:
                    st.error("Não foi possível finalizar a visita. Tente novamente.")
        with c2:
            if st.button("Cancelar", key=f"cancel_finalize_{visit_id}", width="stretch"):
                st.session_state.pop("finalize_pending", None)
                st.rerun()


# ---------------------------------------------------------------------------
# Preenchimento em etapas (Identificação -> Equipamentos -> Caderno)
# ---------------------------------------------------------------------------
def _render_progress(visit_id: str, draft: dict, step: int):
    answered, total = visit_completion(draft["forms"])
    percent = (answered / total) if total else 0.0
    st.progress(percent, text=f"Checklist técnico: {answered} de {total} campos obrigatórios respondidos")
    st.caption(
        f"{FILL_STEP_TITLES.get(step, 'Etapa')} • Etapa {step + 1} de {FILL_TOTAL_STEPS} — "
        "os dados são salvos automaticamente."
    )


def _render_modular_resources(visit_id: str) -> None:
    """Exibe os blocos modulares em consulta, sem duplicar os campos editáveis.

    As etapas acima continuam sendo a única interface de edição. Este painel é
    carregado sob demanda e usa os mesmos serviços de armazenamento do fluxo
    principal, em modo somente leitura.
    """
    panel_key = f"show_visit_enhancements_{visit_id}"
    with st.expander("🔧 Recursos modulares da visita (consulta)", expanded=False):
        if not st.session_state.get(panel_key, False):
            st.caption(
                "Resumo, condições ambientais, equipamentos, assinaturas e fotografias "
                "reaproveitando os serviços existentes, em modo somente leitura."
            )
            if st.button(
                "Carregar recursos modulares",
                key=f"load_enhancements_{visit_id}",
                width="stretch",
            ):
                st.session_state[panel_key] = True
                st.rerun()
            return

        if st.button(
            "Ocultar recursos modulares",
            key=f"hide_enhancements_{visit_id}",
            width="stretch",
        ):
            st.session_state[panel_key] = False
            st.rerun()

        render_visit_enhancements_panel(
            visit_id,
            show_summary=True,
            show_blocks=True,
            read_only=True,
        )


def _render_fill_tab(visits: dict):
    render_section_title(
        "Preenchimento da visita",
        "Siga a sequência: Identificação da visita, Equipamentos utilizados e Caderno de Avaliação.",
        "✍️",
    )

    if not visits:
        render_empty_state("✍️", "Nenhuma visita para preencher", "Crie uma visita a partir de uma empresa na aba Visitas.")
        return

    visit_options = {}
    for v_id, v in visits.items():
        ident = visit_identification_label({**v, "id": v_id})
        visit_options[f"Visita #{v_id} — {ident}"] = v_id
    labels = list(visit_options.keys())
    ids = list(visit_options.values())

    desired_id = st.session_state.get("active_visit_id")
    already_synced = st.session_state.get("visit_select_active_synced")
    if desired_id in ids and desired_id != already_synced:
        st.session_state["visit_select"] = labels[ids.index(desired_id)]

    selected_label = st.selectbox("Selecione a visita", labels, key="visit_select")
    selected_id = visit_options[selected_label]
    st.session_state["active_visit_id"] = selected_id
    st.session_state["visit_select_active_synced"] = selected_id
    visit = visits[selected_id]

    if st.session_state.get("draft_loaded_vid") != selected_id:
        st.session_state["draft_loaded_vid"] = selected_id
        st.session_state[_draft_key(selected_id)] = _build_draft(visit)
        st.session_state.setdefault(_step_key(selected_id), _first_pending_step(visit))

    draft = st.session_state[_draft_key(selected_id)]
    _collect_widgets(selected_id, draft)

    step = int(st.session_state.get(_step_key(selected_id), FILL_STEP_IDENTIFICACAO))
    step = max(0, min(step, FILL_TOTAL_STEPS - 1))
    st.session_state[_step_key(selected_id)] = step

    status = _display_status(visit.get("status", "Rascunho"))
    st.markdown(
        f"**Identificação:** {visit_identification_label({**visit, **draft, 'id': selected_id})} &nbsp;|&nbsp; "
        f"**Técnico:** {visit.get('technician', '—')} &nbsp;|&nbsp; "
        f"**Situação:** {status_badge(status)}",
        unsafe_allow_html=True,
    )
    _render_progress(selected_id, draft, step)
    st.markdown("---")

    if step == FILL_STEP_IDENTIFICACAO:
        _render_identificacao_step(selected_id, visit, draft)
    elif step == FILL_STEP_EQUIPAMENTOS:
        _render_equipamentos_step(selected_id, visit)
    else:
        _render_caderno_step(selected_id, visit, draft)

    _render_modular_resources(selected_id)

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    nav_left, nav_center, nav_right = st.columns([1, 1.4, 1])
    with nav_left:
        if step > 0 and st.button("⬅️ Voltar", key=f"prev_{selected_id}", width="stretch"):
            _collect_widgets(selected_id, draft)
            _persist_draft(selected_id, draft)
            st.session_state[_step_key(selected_id)] = step - 1
            st.rerun()
    with nav_center:
        if st.button("💾 Salvar", key=f"save_{selected_id}", width="stretch"):
            _collect_widgets(selected_id, draft)
            _sync_caderno_date_time_widgets(selected_id, draft, [("data_amostragem", "date"), ("hora_inicial", "time"), ("hora_final", "time")])
            _persist_signatures(selected_id)
            if _persist_draft(selected_id, draft):
                st.success("Alterações salvas com sucesso.")
            else:
                st.error("Não foi possível salvar. Tente novamente.")
    with nav_right:
        if step < FILL_TOTAL_STEPS - 1:
            label = "Avançar ➡️" if step != FILL_STEP_EQUIPAMENTOS else "Abrir caderno ➡️"
            if st.button(label, key=f"next_{selected_id}", type="primary", width="stretch"):
                _collect_widgets(selected_id, draft)
                _persist_draft(selected_id, draft)
                st.session_state[_step_key(selected_id)] = step + 1
                st.rerun()


# ---------------------------------------------------------------------------
# Entrada da página
# ---------------------------------------------------------------------------
def render_visits_view():
    render_acnnorte_logo(size="medium", subtitle="Visitas e Caderno de Avaliação de Agentes Químicos")

    clients = load_clients()
    visits = load_visits()
    selected_tab = _select_visits_tab()

    if selected_tab == VISITS_TAB_NEW:
        _render_new_visit(clients)
    elif selected_tab == VISITS_TAB_FILL:
        _render_fill_tab(visits)
    else:
        _render_visits_overview(visits, clients)
