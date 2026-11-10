"""Cabeçalho da inspeção: empresa, período e clima automático."""

from __future__ import annotations

import streamlit as st

from src.ui_components import (
    render_section_title,
    set_flash,
    status_badge,
)
from src.weather_service import (
    WeatherError,
    format_humidity,
    format_temperature,
    is_configured,
)

from .geolocation import auto_geolocation, geolocation_state
from .services import (
    fetch_weather,
    init_header_widgets,
    reload_inspection,
    save_header,
    save_weather_manual,
    save_weather_reading,
    scoped_key,
)


def _location_label(climate: dict) -> str:
    city = climate.get("cidade")
    if city:
        return str(city)
    latitude = climate.get("latitude")
    longitude = climate.get("longitude")
    try:
        return f"{float(latitude):.4f}, {float(longitude):.4f}"
    except (TypeError, ValueError):
        return "Localização do dispositivo"


def _render_climate_metrics(inspection: dict) -> None:
    temperature = inspection.get("temperatura_capturada")
    humidity = inspection.get("umidade_capturada")
    climate = inspection.get("clima") or {}

    col_temp, col_hum, col_place, col_status = st.columns([1, 1, 1.4, 1.2])
    with col_temp:
        st.metric("🌡️ Temperatura", format_temperature(temperature))
    with col_hum:
        st.metric("💧 Umidade relativa", format_humidity(humidity))
    with col_place:
        st.metric("📍 Local", _location_label(climate))
    with col_status:
        captured = climate.get("capturado_em")
        st.metric("🔄 Atualização", "Automática" if captured else "Pendente")
        if captured:
            st.caption(f"Capturado em {captured}")

    if climate.get("descricao"):
        st.caption(f"Condição observada: {climate['descricao']}.")


def _auto_capture(inspection_id: str, inspection: dict) -> None:
    """Executa a captura automática quando o GPS entrega novas coordenadas."""
    geo_key = scoped_key(inspection_id, "auto_geo")
    result = auto_geolocation(key=geo_key)
    state = geolocation_state(geo_key, result)

    latitude = state.get("latitude")
    longitude = state.get("longitude")
    if latitude is None or longitude is None:
        if state.get("error"):
            st.caption(f"GPS: {state['error']} Informe as coordenadas manualmente abaixo.")
        return

    location_token = f"{float(latitude):.5f},{float(longitude):.5f}"
    attempt_key = scoped_key(inspection_id, "weather_attempt")
    if st.session_state.get(attempt_key) == location_token:
        return

    with st.spinner("Capturando temperatura e umidade no local..."):
        try:
            reading = fetch_weather(float(latitude), float(longitude))
        except Exception:  # mensagem amigável para falhas externas
            st.session_state[attempt_key] = location_token
            st.warning(
                "GPS capturado, mas não foi possível consultar o clima agora. "
                "Use o ajuste manual abaixo."
            )
            return

    st.session_state[attempt_key] = location_token
    save_weather_reading(inspection_id, reading)
    set_flash(
        "Clima capturado automaticamente: "
        f"{format_temperature(reading.temperatura)} e "
        f"{format_humidity(reading.umidade)}."
    )
    st.rerun()


def _render_manual_climate(inspection_id: str, inspection: dict) -> None:
    temperature = inspection.get("temperatura_capturada")
    humidity = inspection.get("umidade_capturada")
    climate = inspection.get("clima") or {}

    with st.expander("Ajustar clima ou informar coordenadas manualmente"):
        st.caption(
            "Use esta opção quando o navegador bloquear o GPS ou quando a "
            "consulta automática estiver indisponível."
        )
        manual_lat = st.text_input(
            "Latitude",
            value=str(climate.get("latitude") or ""),
            key=scoped_key(inspection_id, "manual_lat"),
            placeholder="-23.5505",
        )
        manual_lon = st.text_input(
            "Longitude",
            value=str(climate.get("longitude") or ""),
            key=scoped_key(inspection_id, "manual_lon"),
            placeholder="-46.6333",
        )

        if st.button(
            "Capturar clima com estas coordenadas",
            key=scoped_key(inspection_id, "manual_weather"),
        ):
            try:
                latitude = float(str(manual_lat).replace(",", "."))
                longitude = float(str(manual_lon).replace(",", "."))
            except ValueError:
                st.error("Informe latitude e longitude válidas.")
            else:
                try:
                    reading = fetch_weather(latitude, longitude)
                except WeatherError as exc:
                    st.error(str(exc))
                except Exception:
                    st.error(
                        "Não foi possível consultar o clima agora. "
                        "Verifique a conexão e tente novamente."
                    )
                else:
                    save_weather_reading(inspection_id, reading)
                    set_flash(
                        f"Clima capturado: {format_temperature(reading.temperatura)} e "
                        f"{format_humidity(reading.umidade)}."
                    )
                    st.rerun()

        st.markdown("**Ajuste manual da temperatura e umidade**")
        manual_temp = st.number_input(
            "Temperatura (°C)",
            min_value=-20.0,
            max_value=70.0,
            value=float(temperature) if temperature is not None else 24.0,
            step=0.1,
            key=scoped_key(inspection_id, "manual_temp"),
        )
        manual_hum = st.number_input(
            "Umidade (%)",
            min_value=0.0,
            max_value=100.0,
            value=float(humidity) if humidity is not None else 60.0,
            step=1.0,
            key=scoped_key(inspection_id, "manual_hum"),
        )
        if st.button(
            "Salvar clima manual",
            key=scoped_key(inspection_id, "manual_save"),
        ):
            save_weather_manual(
                inspection_id,
                float(manual_temp),
                float(manual_hum),
                climate=climate,
            )
            set_flash("Temperatura e umidade salvas.")
            st.rerun()


def render_header(inspection_id: str, inspection: dict) -> dict:
    """Renderiza o cabeçalho e devolve a inspeção recarregada."""
    render_section_title(
        "Dados da inspeção",
        "Identifique a empresa, o período da avaliação e confirme o clima do local.",
        "📝",
    )
    init_header_widgets(inspection_id, inspection)

    with st.container(border=True):
        col_company, col_start, col_end = st.columns([2.1, 1, 1])
        with col_company:
            st.text_input(
                "Nome da empresa *",
                key=scoped_key(inspection_id, "empresa"),
                placeholder="Razão social ou nome fantasia",
                on_change=save_header,
                args=(inspection_id,),
            )
        with col_start:
            st.date_input(
                "Data de avaliação *",
                key=scoped_key(inspection_id, "data_inicio"),
                on_change=save_header,
                args=(inspection_id,),
            )
        with col_end:
            st.date_input(
                "Data final da avaliação",
                key=scoped_key(inspection_id, "data_fim"),
                on_change=save_header,
                args=(inspection_id,),
            )

        st.markdown(
            f"**Situação:** {status_badge(inspection.get('status', 'Rascunho'))}",
            unsafe_allow_html=True,
        )

    st.markdown("#### 🌡️ Clima no local da avaliação")
    st.caption(
        "A localização do dispositivo é solicitada automaticamente e usada "
        "somente para consultar a temperatura e a umidade. "
        + (
            "Fonte principal: OpenWeather."
            if is_configured()
            else "Sem chave da OpenWeather: será usada a Open-Meteo automaticamente."
        )
    )
    _render_climate_metrics(inspection)
    _auto_capture(inspection_id, inspection)
    _render_manual_climate(inspection_id, inspection)
    return reload_inspection(inspection_id)
