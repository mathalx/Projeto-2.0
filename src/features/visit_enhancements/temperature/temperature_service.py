"""Servi?o/bloco de temperatura (CHANGE 03).

Reaproveita os m?dulos existentes ``src.weather_service``, ``src.geolocation`` e
``src.storage_manager`` sem duplicar regras de captura ou persist?ncia.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.geolocation import geolocation
from src.storage_manager import save_visit_weather
from src.ui_components import record_sync, set_flash
from src.weather_service import (
    SOURCE_MANUAL,
    WeatherError,
    capture_weather_auto,
    format_humidity,
    format_temperature,
)


def _weather_of(visit: dict) -> dict:
    weather = visit.get("weather") if isinstance(visit, dict) else None
    return weather if isinstance(weather, dict) else {}


def capture_and_save_external_weather(
    visit_id: str,
    latitude,
    longitude,
    *,
    internal_temperature_c=None,
    fallback_manual_lat=None,
    fallback_manual_lon=None,
    existing_weather: dict | None = None,
) -> tuple[bool, str, dict | None]:
    """Captura clima externo por coordenadas e persiste na visita."""
    weather = existing_weather or {}
    lat, lon = latitude, longitude
    if lat is None or lon is None:
        if fallback_manual_lat not in (None, "") and fallback_manual_lon not in (None, ""):
            try:
                lat = float(str(fallback_manual_lat).replace(",", "."))
                lon = float(str(fallback_manual_lon).replace(",", "."))
            except (TypeError, ValueError):
                lat = lon = None
        elif weather.get("latitude") is not None and weather.get("longitude") is not None:
            lat, lon = weather.get("latitude"), weather.get("longitude")

    if lat is None or lon is None:
        return (
            False,
            "N?o foi poss?vel obter a localiza??o. Autorize o GPS ou informe latitude e longitude.",
            None,
        )

    try:
        reading = capture_weather_auto(lat, lon)
    except WeatherError as exc:
        return False, str(exc), None
    except Exception:
        return (
            False,
            "N?o foi poss?vel consultar o clima agora. Verifique a conex?o e tente informar manualmente.",
            None,
        )

    success, message = save_visit_weather(
        visit_id,
        reading.temperatura,
        reading.umidade,
        internal_temperature_c=internal_temperature_c,
        description=reading.descricao,
        city=reading.cidade,
        latitude=reading.latitude,
        longitude=reading.longitude,
        source=reading.fonte,
        captured_at=reading.capturado_em,
    )
    if success:
        record_sync()
    return success, message, reading.to_dict() if success else None


def save_manual_weather(
    visit_id: str,
    *,
    temperature_c,
    humidity_pct,
    internal_temperature_c=None,
    latitude=None,
    longitude=None,
    source: str = SOURCE_MANUAL,
    description: str = "",
    city: str = "",
    captured_at: str | None = None,
) -> tuple[bool, str]:
    """Salva valores informados/editados manualmente (ou preservando metadados)."""
    success, message = save_visit_weather(
        visit_id,
        temperature_c,
        humidity_pct,
        internal_temperature_c=internal_temperature_c,
        description=description,
        city=city,
        latitude=latitude,
        longitude=longitude,
        source=source,
        captured_at=captured_at,
    )
    if success:
        record_sync()
    return success, message


def render_temperature_block(
    visit_id: str,
    visit: dict,
    *,
    key_prefix: str = "ve_temp",
    read_only: bool = False,
) -> dict[str, Any]:
    """Renderiza bloco de condi??es ambientais reutiliz?vel."""
    weather = _weather_of(visit)
    geo_key = f"{key_prefix}_{visit_id}_geo"
    # Em modo somente leitura não há motivo para pedir a localização ao
    # dispositivo; o botão continua disponível para uma captura manual.
    geo_state = geolocation(key=geo_key, auto_request=not read_only)
    gps_lat = geo_state.get("latitude")
    gps_lon = geo_state.get("longitude")

    st.markdown("#### Condi??es ambientais")
    st.caption(
        "Temperatura externa obtida pelo clima da localiza??o (n?o substitui medi??o interna com term?metro)."
    )

    if read_only:
        st.markdown(f"**Temperatura externa:** {format_temperature(weather.get('temperature_c'))}")
        internal = weather.get("internal_temperature_c")
        st.markdown(
            f"**Temperatura interna:** {format_temperature(internal) if internal is not None else 'N?o informada'}"
        )
        st.markdown(f"**Umidade:** {format_humidity(weather.get('humidity_pct'))}")
        st.markdown(f"**Origem:** {weather.get('source') or 'N?o informada'}")
        st.markdown(f"**Local:** {weather.get('city') or 'N?o identificado'}")
        st.markdown(f"**Consulta:** {weather.get('captured_at') or '?'}")
        return {"geo": geo_state, "weather": weather, "read_only": True}

    result: dict[str, Any] = {"geo": geo_state, "weather": weather}
    action_col, hint_col = st.columns([1, 2])
    with action_col:
        capture_clicked = st.button(
            "Obter temperatura",
            key=f"{key_prefix}_{visit_id}_get",
            type="primary",
            width="stretch",
        )
    with hint_col:
        if gps_lat is not None and gps_lon is not None:
            st.caption(f"GPS dispon?vel: {float(gps_lat):.5f}, {float(gps_lon):.5f}.")
        elif geo_state.get("error"):
            st.caption(str(geo_state["error"]))
        else:
            st.caption("Aguardando autoriza??o de localiza??o do dispositivo.")

    with st.expander("Informar coordenadas manualmente", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            manual_lat = st.text_input(
                "Latitude", value=str(weather.get("latitude") or ""),
                key=f"{key_prefix}_{visit_id}_manual_lat", placeholder="-23.5505",
            )
        with c2:
            manual_lon = st.text_input(
                "Longitude", value=str(weather.get("longitude") or ""),
                key=f"{key_prefix}_{visit_id}_manual_lon", placeholder="-46.6333",
            )

    if capture_clicked:
        has_internal = st.session_state.get(f"{key_prefix}_{visit_id}_has_internal", False)
        internal = st.session_state.get(f"{key_prefix}_{visit_id}_internal") if has_internal else None
        ok, msg, reading = capture_and_save_external_weather(
            visit_id, gps_lat, gps_lon,
            internal_temperature_c=internal,
            fallback_manual_lat=manual_lat,
            fallback_manual_lon=manual_lon,
            existing_weather=weather,
        )
        result.update({"captured": ok, "message": msg, "reading": reading})
        if ok and reading:
            set_flash(
                f"Temperatura externa capturada ({reading.get('fonte')}): "
                f"{format_temperature(reading.get('temperatura'))} e umidade "
                f"{format_humidity(reading.get('umidade'))}."
            )
            st.rerun()
        elif not ok:
            st.error(msg)

    has_internal_key = f"{key_prefix}_{visit_id}_has_internal"
    st.session_state.setdefault(has_internal_key, weather.get("internal_temperature_c") is not None)
    has_internal = st.checkbox(
        "Registrar temperatura interna medida na empresa (opcional)", key=has_internal_key,
    )

    ext_key = f"{key_prefix}_{visit_id}_external"
    hum_key = f"{key_prefix}_{visit_id}_humidity"
    int_key = f"{key_prefix}_{visit_id}_internal"
    if ext_key not in st.session_state:
        st.session_state[ext_key] = weather.get("temperature_c")
    if hum_key not in st.session_state:
        st.session_state[hum_key] = weather.get("humidity_pct")
    if int_key not in st.session_state:
        st.session_state[int_key] = weather.get("internal_temperature_c")

    if has_internal:
        c1, c2, c3 = st.columns(3)
    else:
        c1, c3 = st.columns(2)
        c2 = None
    with c1:
        st.number_input("Temperatura externa (?C)", min_value=-20.0, max_value=70.0, value=None, step=0.1, key=ext_key)
    if c2 is not None:
        with c2:
            st.number_input("Temperatura interna medida (?C)", min_value=-20.0, max_value=70.0, value=None, step=0.1, key=int_key)
    with c3:
        st.number_input("Umidade relativa (%)", min_value=0.0, max_value=100.0, value=None, step=1.0, key=hum_key)

    if weather.get("captured_at"):
        st.caption(
            f"Origem: {weather.get('source') or '?'} | Local: {weather.get('city') or 'N?o identificado'} | "
            f"Consulta: {weather.get('captured_at')}"
        )

    if st.button("Salvar temperaturas", key=f"{key_prefix}_{visit_id}_save", width="stretch"):
        ext = st.session_state.get(ext_key)
        hum = st.session_state.get(hum_key)
        if ext is None or hum is None:
            st.error("Informe temperatura externa e umidade, ou use 'Obter temperatura'.")
        else:
            internal_val = st.session_state.get(int_key) if has_internal else None
            ok, msg = save_manual_weather(
                visit_id,
                temperature_c=float(ext),
                humidity_pct=float(hum),
                internal_temperature_c=float(internal_val) if internal_val is not None else None,
                latitude=manual_lat or weather.get("latitude"),
                longitude=manual_lon or weather.get("longitude"),
                source=weather.get("source") or SOURCE_MANUAL,
                description=weather.get("description", ""),
                city=weather.get("city", ""),
                captured_at=weather.get("captured_at"),
            )
            if ok:
                set_flash("Temperaturas e umidade salvas.")
                st.rerun()
            else:
                st.error(msg)

    return result
