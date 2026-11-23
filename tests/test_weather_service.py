"""Testes da captura automática de temperatura (CHANGE 03)."""

import pytest

import src.weather_service as weather


class _FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


def test_capture_open_meteo_returns_temperature_and_humidity(monkeypatch):
    captured = {}

    def fake_get(url, params=None, timeout=None):
        captured["url"] = url
        captured["params"] = params
        return _FakeResponse(
            {
                "current": {
                    "temperature_2m": 27.34,
                    "relative_humidity_2m": 61,
                    "weather_code": 2,
                }
            }
        )

    monkeypatch.setattr(weather.requests, "get", fake_get)

    reading = weather.capture_open_meteo(-23.5505, -46.6333)

    assert captured["url"] == weather.OPEN_METEO_URL
    assert captured["params"]["latitude"] == -23.5505
    assert reading.temperatura == 27.3
    assert reading.umidade == 61.0
    assert reading.descricao == "Parcialmente nublado"
    assert reading.fonte == weather.SOURCE_OPEN_METEO
    assert reading.capturado_em


def test_capture_open_meteo_rejects_invalid_coordinates():
    with pytest.raises(weather.WeatherError):
        weather.capture_open_meteo(200, 10)


def test_capture_weather_uses_openweather_when_key_is_configured(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        assert url == weather.OPENWEATHER_URL
        assert params["appid"] == "fake-key"
        return _FakeResponse(
            {
                "main": {"temp": 19.86, "humidity": 72},
                "weather": [{"description": "chuva leve"}],
                "name": "São Paulo",
            }
        )

    monkeypatch.setattr(weather.requests, "get", fake_get)

    reading = weather.capture_weather(-23.55, -46.63, api_key="fake-key")

    assert reading.temperatura == 19.9
    assert reading.umidade == 72.0
    assert reading.descricao == "Chuva leve"
    assert reading.cidade == "São Paulo"
    assert reading.fonte == weather.SOURCE_OPENWEATHER


def test_capture_weather_auto_falls_back_to_open_meteo(monkeypatch):
    monkeypatch.delenv("OPENWEATHER_API_KEY", raising=False)
    monkeypatch.setattr(weather, "is_configured", lambda api_key=None: False)

    def fake_get(url, params=None, timeout=None):
        assert url == weather.OPEN_METEO_URL
        return _FakeResponse(
            {
                "current": {
                    "temperature_2m": 30.0,
                    "relative_humidity_2m": 40,
                    "weather_code": 0,
                }
            }
        )

    monkeypatch.setattr(weather.requests, "get", fake_get)

    reading = weather.capture_weather_auto(-23.55, -46.63)

    assert reading.temperatura == 30.0
    assert reading.fonte == weather.SOURCE_OPEN_METEO


def test_network_error_returns_friendly_message(monkeypatch):
    def fake_get(*args, **kwargs):
        raise weather.requests.RequestException("sem internet")

    monkeypatch.setattr(weather.requests, "get", fake_get)

    with pytest.raises(weather.WeatherError) as exc:
        weather.capture_open_meteo(-23.55, -46.63)

    assert "conexão" in str(exc.value).lower()


def test_format_helpers():
    assert weather.format_temperature(24.56) == "24,6 °C"
    assert weather.format_humidity(61.4) == "61%"
    assert weather.format_temperature(None) == "Não capturada"
    assert weather.format_humidity("") == "Não capturada"
