"""Seletor de equipamentos de Dosimetria de Ru?do (CHANGE 05).

Reaproveita ``src.equipment_catalog`` e ``src.storage_manager``.
Cat?logo configur?vel; n?o inventa novos equipamentos.
"""

from __future__ import annotations

import streamlit as st

from src.equipment_catalog import DEFAULT_CATEGORY as EQUIPMENT_CATEGORY
from src.equipment_catalog import equipment_grouped, equipment_label
from src.storage_manager import (
    get_visit_equipment,
    get_visit_measurements,
    missing_equipment,
    save_visit_equipment,
    update_visit_measurement,
)
from src.ui_components import record_sync


def validate_equipment_for_completion(visit: dict) -> list[str]:
    return missing_equipment(visit)


def render_equipment_block(
    visit_id: str,
    visit: dict,
    *,
    key_prefix: str = "ve_eq",
    read_only: bool = False,
) -> dict:
    """Renderiza sele??o m?ltipla por bot?es destac?veis e v?nculos de medi??o."""
    st.markdown("#### Equipamentos ? Dosimetria de Ru?do")
    st.caption(
        "Selecione os equipamentos utilizados (Chrompack: 2386, 3440, 2319, 3558, 5981; Instrutherm: DOS-100X). "
        "Cada equipamento selecionado fica associado ? visita e ? sua medi??o."
    )

    selected = get_visit_equipment(visit)
    selected_codes = {str(item.get("codigo")) for item in selected if item.get("codigo")}

    if not read_only:
        grouped = equipment_grouped()
        for category, brands in grouped.items():
            st.markdown(f"**{category}**")
            for brand, items in brands.items():
                st.markdown(f"*{brand}*")
                cols = st.columns(min(3, len(items)) or 1)
                for i, item in enumerate(items):
                    code = item["codigo"]
                    with cols[i % len(cols)]:
                        if st.button(
                            item["identificacao"],
                            key=f"{key_prefix}_{visit_id}_{code}",
                            type="primary" if code in selected_codes else "secondary",
                            width="stretch",
                            help=equipment_label(item),
                        ):
                            codes = set(selected_codes)
                            if code in codes:
                                codes.remove(code)
                            else:
                                codes.add(code)
                            ok, msg = save_visit_equipment(visit_id, list(codes))
                            if ok:
                                record_sync()
                                st.rerun()
                            else:
                                st.error(msg)

    measurements = {str(m.get("equipment_code")): m for m in get_visit_measurements(visit)}
    if not selected:
        st.info("Nenhum equipamento selecionado. Selecione pelo menos um para finalizar a visita.")
    else:
        st.markdown("**Equipamentos selecionados e medi??es vinculadas**")
        for index, item in enumerate(selected, start=1):
            code = str(item.get("codigo"))
            measurement = measurements.get(code, {})
            base_label = equipment_label(item)
            with st.container(border=True):
                st.markdown(f"**{index}. {base_label}**")
                if read_only:
                    registro = measurement.get("identificacao_registro") or base_label
                    st.markdown(f"Identifica??o: {registro}")
                    st.caption(f"Medi??o: {measurement.get('id', '?')}")
                else:
                    time_key = f"{key_prefix}_{visit_id}_{code}_time"
                    current_time = str(measurement.get("horario") or item.get("horario") or "")
                    if time_key not in st.session_state:
                        st.session_state[time_key] = current_time
                    st.text_input(
                        "Hor?rio (HH:MM)", key=time_key, placeholder="08:30",
                        help="Padr?o de identifica??o: hor?rio + equipamento.",
                    )
                    horario = str(st.session_state.get(time_key, "") or "").strip()
                    if st.button("Salvar hor?rio", key=f"{key_prefix}_{visit_id}_{code}_save_time"):
                        ok, msg = update_visit_measurement(visit_id, code, horario=horario)
                        if ok:
                            record_sync()
                            st.rerun()
                        else:
                            st.error(msg)
                    registro = f"{horario} ? {base_label}" if horario else base_label
                    st.caption(f"Identifica??o do registro: **{registro}** | Medi??o: {measurement.get('id', '?')}")

    return {"selected": selected, "pending": validate_equipment_for_completion(visit)}
