"""Serviços do fluxo de inspeção de campo (v2).

Esta camada concentra a orquestração do formulário: seleção/criação da
inspeção, persistência do cabeçalho, clima, funcionário, equipamentos,
checklist, assinaturas e validação de finalização.

Os dados continuam sendo gravados pela camada central ``src.storage_manager``
no formato já existente em ``data/visits.json``. Nenhuma regra de negócio
anterior é substituída: as funções apenas organizam as chamadas do novo fluxo.
"""

from __future__ import annotations

from datetime import date, datetime

import streamlit as st

from src import storage_manager
from src.form_template import (
    TECHNICAL_FORM_SECTIONS,
    UNANSWERED_LABEL,
    visit_completion,
)
from src.ui_components import record_sync
from src.weather_service import WeatherReading, capture_weather_auto

SECTIONS = list(TECHNICAL_FORM_SECTIONS.items())

ACTIVE_INSPECTION_KEY = "field_inspection_id"
PENDING_INSPECTION_KEY = "field_inspection_select_pending"
SELECTOR_KEY = "field_inspection_select"


# ---------------------------------------------------------------------------
# Chaves de widgets isoladas por inspeção
# ---------------------------------------------------------------------------
def scoped_key(inspection_id: str, name: str) -> str:
    """Cria uma chave de estado exclusiva da inspeção (prefixo ``fi_``)."""
    return f"fi_{name}_{inspection_id}"


def answer_key(inspection_id: str, category: str, field_id: str) -> str:
    return scoped_key(inspection_id, f"answer_{category}_{field_id}")


# ---------------------------------------------------------------------------
# Datas e rótulos
# ---------------------------------------------------------------------------
def as_date(value, fallback: date | None = None) -> date:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return fallback or date.today()


def inspection_label(inspection: dict) -> str:
    empresa = (
        inspection.get("empresa_nome")
        or inspection.get("client_name")
        or "Nova avaliação"
    )
    when = inspection.get("data_avaliacao") or inspection.get("date") or "sem data"
    status = inspection.get("status", "Rascunho")
    identifier = inspection.get("id") or ""
    suffix = f" • #{identifier}" if identifier else ""
    return f"{empresa} — {when} • {status}{suffix}"


def inspection_period(inspection: dict) -> str:
    start = inspection.get("data_avaliacao") or inspection.get("date") or ""
    end = inspection.get("data_avaliacao_fim") or start
    if start and end and end != start:
        return f"{format_date(start)} a {format_date(end)}"
    return format_date(start) if start else "Data não informada"


def format_date(value) -> str:
    try:
        return date.fromisoformat(str(value)).strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return str(value or "—")


# ---------------------------------------------------------------------------
# Criação, seleção e recarga da inspeção
# ---------------------------------------------------------------------------
def create_inspection_draft(username: str | None = None) -> str:
    """Cria uma nova inspeção em rascunho e a define como ativa."""
    today = date.today().isoformat()
    success, inspection_id, _message = storage_manager.create_inspection(
        "",
        today,
        today,
        username or st.session_state.get("username", "Avaliador ACNnorte"),
    )
    if not success:
        return ""
    st.session_state[ACTIVE_INSPECTION_KEY] = inspection_id
    st.session_state[PENDING_INSPECTION_KEY] = inspection_id
    return inspection_id


def reload_inspection(inspection_id: str) -> dict:
    return storage_manager.get_inspection(inspection_id) or {}


def select_inspection(visits: dict) -> str:
    """Renderiza o seletor de avaliação e devolve a inspeção ativa."""
    options: dict[str, str] = {
        inspection_label(inspection): inspection_id
        for inspection_id, inspection in visits.items()
    }
    options["➕ Nova avaliação"] = "__new__"

    current_id = st.session_state.get(ACTIVE_INSPECTION_KEY)
    desired_id = st.session_state.pop(PENDING_INSPECTION_KEY, None)
    if desired_id in visits:
        current_id = desired_id

    if current_id not in visits:
        # Prioriza rascunhos e, depois, a avaliação atualizada mais recentemente.
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
        st.session_state[SELECTOR_KEY] = labels[ids.index(desired_id)]
    elif (
        SELECTOR_KEY not in st.session_state
        and current_id in ids
    ):
        st.session_state[SELECTOR_KEY] = labels[ids.index(current_id)]

    selected_label = st.selectbox(
        "Avaliação em andamento",
        labels,
        key=SELECTOR_KEY,
        help=(
            "O aplicativo abre direto no formulário. Escolha uma avaliação "
            "existente ou crie outra."
        ),
    )
    selected_id = options[selected_label]
    if selected_id == "__new__":
        return create_inspection_draft()

    st.session_state[ACTIVE_INSPECTION_KEY] = selected_id
    return selected_id


# ---------------------------------------------------------------------------
# Cabeçalho: empresa e datas
# ---------------------------------------------------------------------------
def init_header_widgets(inspection_id: str, inspection: dict) -> None:
    empresa_key = scoped_key(inspection_id, "empresa")
    if empresa_key not in st.session_state:
        st.session_state[empresa_key] = (
            inspection.get("empresa_nome") or inspection.get("client_name") or ""
        )

    start_key = scoped_key(inspection_id, "data_inicio")
    if start_key not in st.session_state:
        st.session_state[start_key] = as_date(
            inspection.get("data_avaliacao") or inspection.get("date")
        )

    end_key = scoped_key(inspection_id, "data_fim")
    if end_key not in st.session_state:
        st.session_state[end_key] = as_date(
            inspection.get("data_avaliacao_fim")
            or inspection.get("data_avaliacao")
            or inspection.get("date")
        )


def save_header(inspection_id: str) -> None:
    start = st.session_state.get(
        scoped_key(inspection_id, "data_inicio"), date.today()
    )
    end = st.session_state.get(scoped_key(inspection_id, "data_fim"), start)
    storage_manager.update_inspection(
        inspection_id,
        empresa_nome=st.session_state.get(scoped_key(inspection_id, "empresa"), ""),
        data_avaliacao=str(start),
        data_avaliacao_fim=str(end),
    )
    record_sync()


# ---------------------------------------------------------------------------
# Clima automático e manual
# ---------------------------------------------------------------------------
def save_weather_reading(inspection_id: str, reading: WeatherReading) -> None:
    storage_manager.save_inspection_weather(
        inspection_id,
        reading.temperatura,
        reading.umidade,
        reading.to_dict(),
    )
    record_sync()


def save_weather_manual(
    inspection_id: str,
    temperatura: float,
    umidade: float,
    climate: dict | None = None,
) -> None:
    storage_manager.update_inspection(
        inspection_id,
        temperatura_capturada=temperatura,
        umidade_capturada=umidade,
        clima={
            **(climate or {}),
            "temperatura": temperatura,
            "umidade": umidade,
            "origem": "manual",
            "capturado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    )
    record_sync()


def fetch_weather(latitude: float, longitude: float) -> WeatherReading:
    """Captura o clima com OpenWeather e fallback automático para Open-Meteo."""
    return capture_weather_auto(latitude, longitude)


# ---------------------------------------------------------------------------
# Funcionário, equipamentos e formulários
# ---------------------------------------------------------------------------
def save_worker(
    inspection_id: str,
    name: str,
    role: str,
    sector: str,
    photo_bytes: bytes | None,
    photo_filename: str | None,
):
    return storage_manager.save_inspection_worker(
        inspection_id,
        name,
        role,
        sector,
        photo_bytes=photo_bytes,
        photo_filename=photo_filename,
    )


def set_devices(inspection_id: str, devices: list[dict]) -> None:
    storage_manager.set_inspection_devices(inspection_id, devices)
    record_sync()


def update_calibration_and_refresh(inspection_id: str, codigo: str, new_date) -> dict | None:
    from src.equipment_catalog import find_equipment, update_calibration_date

    update_calibration_date(codigo, new_date)
    refreshed = find_equipment(codigo=codigo)
    if refreshed:
        inspection = reload_inspection(inspection_id)
        devices = [
            refreshed if item.get("codigo") == codigo else item
            for item in (inspection.get("devices") or [])
        ]
        storage_manager.set_inspection_devices(inspection_id, devices)
        record_sync()
    return refreshed


def save_answer(inspection_id: str, category: str, field_id: str) -> None:
    key = answer_key(inspection_id, category, field_id)
    value = st.session_state.get(key, "")
    if value == UNANSWERED_LABEL:
        value = ""
    inspection = reload_inspection(inspection_id)
    forms = {
        name: dict(data or {}) for name, data in (inspection.get("forms") or {}).items()
    }
    forms.setdefault(category, {})[field_id] = value
    storage_manager.update_inspection(inspection_id, forms=forms)
    record_sync()


def apply_epi_answers(inspection_id: str, answers: dict) -> None:
    inspection = reload_inspection(inspection_id)
    forms = {
        name: dict(data or {}) for name, data in (inspection.get("forms") or {}).items()
    }
    forms.setdefault("epi", {}).update(answers)
    for field_id, value in answers.items():
        st.session_state[answer_key(inspection_id, "epi", field_id)] = value
    storage_manager.update_inspection(inspection_id, forms=forms)
    record_sync()


def save_notes(inspection_id: str, field: str) -> None:
    storage_manager.update_inspection(
        inspection_id, **{field: st.session_state.get(scoped_key(inspection_id, field), "")}
    )
    record_sync()


def persist_all_answers(inspection_id: str) -> dict:
    """Persiste todos os widgets de checklist/observações antes de finalizar."""
    inspection = reload_inspection(inspection_id)
    forms = {
        name: dict(data or {}) for name, data in (inspection.get("forms") or {}).items()
    }
    for category, category_info in SECTIONS:
        for field in category_info["fields"]:
            key = answer_key(inspection_id, category, field["id"])
            if key in st.session_state:
                value = st.session_state[key]
                if value == UNANSWERED_LABEL:
                    value = ""
                forms.setdefault(category, {})[field["id"]] = value
    storage_manager.update_inspection(
        inspection_id,
        forms=forms,
        observations=st.session_state.get(scoped_key(inspection_id, "observations"), ""),
        conclusions=st.session_state.get(scoped_key(inspection_id, "conclusions"), ""),
    )
    record_sync()
    return forms


def save_signatures(inspection_id: str, technical: str, evaluator: str):
    return storage_manager.save_inspection_signatures(
        inspection_id, technical, evaluator
    )


# ---------------------------------------------------------------------------
# Validação e finalização
# ---------------------------------------------------------------------------
def validate_for_finalize(
    inspection: dict, forms: dict, technical_signature: str, evaluator_signature: str
) -> list[str]:
    """Lista pendências sem alterar as regras de finalização existentes."""
    pending: list[str] = []
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

    if not technical_signature:
        pending.append("Assinatura do responsável técnico")
    if not evaluator_signature:
        pending.append("Assinatura do avaliador")
    return pending


def finalize_inspection(
    inspection_id: str, forms: dict, technical_signature: str, evaluator_signature: str
) -> list[str]:
    """Finaliza quando não houver pendências e devolve a lista de bloqueios."""
    save_signatures(inspection_id, technical_signature, evaluator_signature)
    fresh = reload_inspection(inspection_id)
    pending = validate_for_finalize(
        fresh, forms, technical_signature, evaluator_signature
    )
    if pending:
        return pending

    storage_manager.update_inspection(inspection_id, status="Finalizada")
    record_sync()
    return []
