"""Botoeira dinâmica de equipamentos do catálogo oficial ACN Norte.

A seleção principal usa chips (``st.pills``) por categoria. Cada chip carrega
a identificação oficial do aparelho, que também é usada na nomenclatura
automática dos arquivos e na tabela técnica do laudo.
"""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from src.equipment_catalog import (
    EQUIPMENT_CATEGORIES,
    build_photo_filename,
    calibration_label,
    equipment_label,
    load_equipments,
)
from src.ui_components import render_section_title, set_flash

from .services import (
    as_date,
    reload_inspection,
    scoped_key,
    set_devices,
    update_calibration_and_refresh,
)


def _quick_label(item: dict) -> str:
    model = item.get("modelo") or item.get("marca") or "Equipamento"
    identifier = (
        item.get("certificado")
        or item.get("identificacao")
        or item.get("num_equipamento")
        or item.get("num_serie")
        or item.get("codigo")
    )
    return f"{model} · {identifier}"


def _technical_label(item: dict) -> str:
    return equipment_label(item)


def _selected_state(inspection_id: str, inspection: dict) -> tuple[str, dict]:
    state_key = scoped_key(inspection_id, "devices")
    if state_key not in st.session_state:
        st.session_state[state_key] = {
            item.get("codigo"): item for item in (inspection.get("devices") or [])
        }
    return state_key, dict(st.session_state[state_key])


def _sync_pills_widget(widget_key: str, options: list[str], defaults: list[str]) -> None:
    """Mantém o estado do widget alinhado ao catálogo atual."""
    current = st.session_state.get(widget_key)
    if not isinstance(current, list):
        st.session_state[widget_key] = list(defaults)
        return
    st.session_state[widget_key] = [label for label in current if label in options]


def _render_selected_cards(
    inspection_id: str,
    selected: dict,
    state_key: str,
) -> None:
    if not selected:
        st.info(
            "Nenhum equipamento selecionado. Use os chips acima para montar "
            "a botoeira da inspeção."
        )
        return

    st.markdown("#### ✅ Equipamentos da inspeção")
    st.caption(
        f"{len(selected)} equipamento(s) selecionado(s). Confira a calibração "
        "antes de iniciar as medições."
    )

    for item in selected.values():
        with st.container(border=True):
            col_info, col_cal = st.columns([2.1, 1])
            with col_info:
                st.markdown(f"**{equipment_label(item)}**")
                st.caption(
                    f"ID/identificação: `{item.get('identificacao') or '—'}` • "
                    f"Série/equipamento: {item.get('num_serie') or item.get('num_equipamento') or '—'}"
                )
                if item.get("certificado"):
                    st.caption(f"Certificado: {item['certificado']}")
            with col_cal:
                st.metric("Última calibração", calibration_label(item))

    first_device = next(iter(selected.values()))
    preview = build_photo_filename(
        datetime.now(), first_device, "EPI_ProtetorAuditivo"
    )
    st.caption(
        "Padrão dos arquivos: `[Horário]_[IdentificaçãoAparelho]_[TagEPI].jpg` — "
        f"exemplo agora: `{preview}`"
    )

    with st.expander("🗓️ Atualizar data de calibração"):
        labels = {_technical_label(item): item for item in selected.values()}
        chosen_label = st.selectbox(
            "Equipamento",
            list(labels.keys()),
            key=scoped_key(inspection_id, "calibration_select"),
        )
        chosen = labels[chosen_label]
        new_date = st.date_input(
            "Nova data da última calibração",
            value=as_date(chosen.get("data_ultima_calibracao")),
            key=scoped_key(inspection_id, "calibration_date"),
        )
        if st.button(
            "Registrar calibração",
            key=scoped_key(inspection_id, "calibration_save"),
        ):
            refreshed = update_calibration_and_refresh(
                inspection_id, chosen["codigo"], new_date
            )
            if refreshed:
                selected[chosen["codigo"]] = refreshed
                st.session_state[state_key] = dict(selected)
            set_flash("Data de calibração atualizada.")
            st.rerun()


def render_equipment(inspection_id: str, inspection: dict) -> dict:
    render_section_title(
        "Botoeira dinâmica de equipamentos — ACN Norte",
        "Toque nos chips para selecionar os aparelhos usados. A calibração e "
        "o nome dos arquivos são preenchidos automaticamente.",
        "🧰",
    )
    equipments = load_equipments()
    by_code = {item["codigo"]: item for item in equipments}
    state_key, selected = _selected_state(inspection_id, inspection)

    with st.container(border=True):
        st.caption(
            "Catálogo oficial da planilha **equipamentos ACN NORTE.xlsx**. "
            "Os IDs abaixo são usados nos laudos e nos nomes das fotografias."
        )
        for category in EQUIPMENT_CATEGORIES:
            category_items = [
                item for item in equipments if item.get("categoria") == category
            ]
            if not category_items:
                continue

            label_to_code = {_quick_label(item): item["codigo"] for item in category_items}
            options = list(label_to_code.keys())
            code_to_label = {code: label for label, code in label_to_code.items()}
            persisted = [
                code_to_label[code]
                for code in selected
                if code in code_to_label
            ]

            widget_key = scoped_key(
                inspection_id,
                f"pills_{category.lower().replace(' ', '_').replace('/', '_')}",
            )
            _sync_pills_widget(widget_key, options, persisted)
            chosen = st.pills(
                category,
                options,
                selection_mode="multi",
                key=widget_key,
                help=f"Seleção rápida — {category}",
            )
            chosen = list(chosen or [])

            # A categoria é a fonte da verdade para os chips exibidos.
            for code in [item["codigo"] for item in category_items]:
                selected.pop(code, None)
            for label in chosen:
                code = label_to_code.get(label)
                if code:
                    selected[code] = by_code[code]

    st.session_state[state_key] = selected

    # Ordena conforme o catálogo oficial para manter previsibilidade.
    ordered = [
        selected[item["codigo"]]
        for item in equipments
        if item.get("codigo") in selected
    ]
    current_snapshot = list(ordered)
    if current_snapshot != (inspection.get("devices") or []):
        set_devices(inspection_id, current_snapshot)

    _render_selected_cards(inspection_id, selected, state_key)
    return reload_inspection(inspection_id)
