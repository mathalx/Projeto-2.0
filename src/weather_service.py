"""Captura automática de temperatura e umidade via OpenWeather.

As coordenadas vêm do GPS do dispositivo (componente de geolocalização) e a
leitura é feita no servidor com a chave ``OPENWEATHER_API_KEY``. O módulo
também aceita coordenadas informadas manualmente, útil quando o navegador
bloqueia a geolocalização.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
DEFAULT_TIMEOUT = 10

# Descrições amigáveis dos códigos WMO retornados pela Open-Meteo.
_WMO_DESCRIPTIONS = {
    0: "Céu limpo",
    1: "Predominantemente limpo",
    2: "Parcialmente nublado",
    3: "Nublado",
    45: "Neblina",
    48: "Neblina com geada",
    51: "Garoa leve",
    53: "Garoa moderada",
    55: "Garoa intensa",
    61: "Chuva leve",
    63: "Chuva moderada",
    65: "Chuva forte",
    71: "Neve leve",
    73: "Neve moderada",
    75: "Neve forte",
    80: "Pancadas de chuva leves",
    81: "Pancadas de chuva moderadas",
    82: "Pancadas de chuva fortes",
    95: "Tempestade",
    96: "Tempestade com granizo",
    99: "Tempestade forte com granizo",
}


class WeatherError(RuntimeError):
    """Erro amigável de configuração ou comunicação com a OpenWeather."""


@dataclass
class WeatherReading:
    temperatura: float
    umidade: float
    descricao: str
    cidade: str
    latitude: float
    longitude: float
    capturado_em: str

    def to_dict(self) -> dict:
        return asdict(self)


def get_api_key(api_key: str | None = None) -> str:
    key = (api_key or os.environ.get("OPENWEATHER_API_KEY", "")).strip()
    if not key:
        try:
            import streamlit as st

            key = str(
                st.secrets.get("OPENWEATHER_API_KEY", "")  # type: ignore[attr-defined]
            ).strip()
        except Exception:
            key = ""
    return key


def is_configured(api_key: str | None = None) -> bool:
    return bool(get_api_key(api_key))


def capture_weather(
    latitude: float,
    longitude: float,
    api_key: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> WeatherReading:
    """Consulta a OpenWeather e retorna temperatura (°C) e umidade (%)."""
    key = get_api_key(api_key)
    if not key:
        raise WeatherError(
            "Chave da OpenWeather não configurada. Defina OPENWEATHER_API_KEY no arquivo .env."
        )

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError) as exc:
        raise WeatherError("Coordenadas de GPS inválidas.") from exc

    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise WeatherError("Coordenadas de GPS fora do intervalo permitido.")

    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": key,
        "units": "metric",
        "lang": "pt_br",
    }

    try:
        response = requests.get(OPENWEATHER_URL, params=params, timeout=timeout)
    except requests.RequestException as exc:
        raise WeatherError(
            "Não foi possível consultar o clima agora. Verifique a conexão e tente novamente."
        ) from exc

    if response.status_code in (401, 403):
        raise WeatherError(
            "A chave da OpenWeather foi recusada. Confira OPENWEATHER_API_KEY."
        )
    if response.status_code == 429:
        raise WeatherError(
            "Limite de consultas da OpenWeather atingido. Tente novamente em alguns minutos."
        )
    if response.status_code >= 400:
        raise WeatherError("A OpenWeather não retornou dados para esta localização.")

    try:
        payload = response.json()
        temperatura = float(payload["main"]["temp"])
        umidade = float(payload["main"]["humidity"])
    except (ValueError, KeyError, TypeError) as exc:
        raise WeatherError("Resposta inesperada da OpenWeather.") from exc

    weather_list = payload.get("weather") or [{}]
    descricao = str(weather_list[0].get("description") or "").capitalize()
    cidade = str(payload.get("name") or "")

    return WeatherReading(
        temperatura=round(temperatura, 1),
        umidade=round(umidade, 1),
        descricao=descricao,
        cidade=cidade,
        latitude=latitude,
        longitude=longitude,
        capturado_em=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


def capture_weather_auto(
    latitude: float,
    longitude: float,
    api_key: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> WeatherReading:
    """Captura o clima automaticamente, com fallback sem chave de API.

    A OpenWeather continua sendo a fonte prioritária quando
    ``OPENWEATHER_API_KEY`` está configurada. Se a chave não existir ou a
    consulta falhar, a Open-Meteo é usada como alternativa gratuita para que a
    captura por GPS funcione mesmo em uma instalação nova.
    """
    errors: list[str] = []

    if is_configured(api_key):
        try:
            return capture_weather(latitude, longitude, api_key=api_key, timeout=timeout)
        except WeatherError as exc:
            errors.append(str(exc))

    try:
        return capture_open_meteo(latitude, longitude, timeout=timeout)
    except WeatherError as exc:
        errors.append(str(exc))

    raise WeatherError(
        errors[-1]
        if errors
        else "Não foi possível capturar a temperatura e a umidade agora."
    )


def capture_open_meteo(
    latitude: float,
    longitude: float,
    timeout: int = DEFAULT_TIMEOUT,
) -> WeatherReading:
    """Consulta a Open-Meteo (sem chave) para temperatura e umidade atuais."""
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError) as exc:
        raise WeatherError("Coordenadas de GPS inválidas.") from exc

    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise WeatherError("Coordenadas de GPS fora do intervalo permitido.")

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,weather_code",
        "timezone": "auto",
    }

    try:
        response = requests.get(OPEN_METEO_URL, params=params, timeout=timeout)
    except requests.RequestException as exc:
        raise WeatherError(
            "Não foi possível consultar o clima agora. Verifique a conexão e tente novamente."
        ) from exc

    if response.status_code == 429:
        raise WeatherError(
            "Limite de consultas meteorológicas atingido. Tente novamente em alguns minutos."
        )
    if response.status_code >= 400:
        raise WeatherError("O serviço meteorológico não retornou dados para esta localização.")

    try:
        payload = response.json()
        current = payload["current"]
        temperatura = float(current["temperature_2m"])
        umidade = float(current["relative_humidity_2m"])
    except (ValueError, KeyError, TypeError) as exc:
        raise WeatherError("Resposta inesperada do serviço meteorológico.") from exc

    code = current.get("weather_code")
    try:
        descricao = _WMO_DESCRIPTIONS.get(int(code), "Condição não informada")
    except (TypeError, ValueError):
        descricao = "Condição não informada"

    return WeatherReading(
        temperatura=round(temperatura, 1),
        umidade=round(umidade, 1),
        descricao=descricao,
        cidade="",
        latitude=latitude,
        longitude=longitude,
        capturado_em=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


def format_temperature(value) -> str:
    try:
        return f"{float(value):.1f} °C".replace(".", ",")
    except (TypeError, ValueError):
        return "Não capturada"


def format_humidity(value) -> str:
    try:
        return f"{float(value):.0f}%"
    except (TypeError, ValueError):
        return "Não capturada"
