"""Testes unitários do cliente Xano, sem chamadas de rede reais."""

from __future__ import annotations

import json

import pytest
import requests

from src.core.database.xano_client import (
    XanoClient,
    XanoConfigurationError,
    XanoConnectionError,
    XanoError,
    smoke_test,
)


class FakeResponse:
    def __init__(self, status_code: int = 200, payload=None):
        self.status_code = status_code
        self._payload = payload
        if payload is None:
            self.content = b""
            self.text = ""
        else:
            self.content = json.dumps(payload).encode("utf-8")
            self.text = self.content.decode("utf-8")

    def json(self):
        if self._payload is None:
            raise ValueError("Resposta sem JSON")
        return self._payload


class FakeSession:
    def __init__(self, response: FakeResponse | None = None, error: Exception | None = None):
        self.response = response
        self.error = error
        self.calls: list[dict] = []
        self.closed = False

    def request(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.response

    def close(self):
        self.closed = True


def _client(response: FakeResponse | None = None, **kwargs) -> tuple[XanoClient, FakeSession]:
    session = FakeSession(response=response)
    kwargs.setdefault("token", "")
    client = XanoClient(
        base_url="https://exemplo.xano.io/api:teste",
        session=session,
        **kwargs,
    )
    return client, session


def test_get_returns_json_and_uses_bearer_token():
    client, session = _client(FakeResponse(200, {"items": [1, 2]}), token="token-123")

    result = client.get("/clients", params={"page": 1})

    assert result == {"items": [1, 2]}
    call = session.calls[0]
    assert call["method"] == "GET"
    assert call["url"] == "https://exemplo.xano.io/api:teste/clients"
    assert call["params"] == {"page": 1}
    assert call["headers"]["Authorization"] == "Bearer token-123"


def test_post_sends_json_payload():
    client, session = _client(FakeResponse(200, {"id": 10}))

    result = client.post("/clients", {"name": "Empresa A", "cnpj": "123"})

    assert result == {"id": 10}
    call = session.calls[0]
    assert call["method"] == "POST"
    assert call["json"] == {"name": "Empresa A", "cnpj": "123"}
    assert "Authorization" not in call["headers"]


def test_error_response_raises_xano_error():
    client, _ = _client(FakeResponse(400, {"message": "CNPJ já cadastrado."}))

    with pytest.raises(XanoError) as exc_info:
        client.post("/clients", {"cnpj": "123"})

    assert exc_info.value.status_code == 400
    assert "CNPJ" in exc_info.value.message


def test_smoke_test_accepts_401_as_reachable():
    client, _ = _client(FakeResponse(401, {"message": "Unauthorized"}))

    result = client.smoke_test()

    assert result.ok is True
    assert result.authenticated is False
    assert result.status_code == 401
    assert "autenticação" in result.message.lower()


def test_smoke_test_warns_when_configured_token_is_rejected():
    client, _ = _client(
        FakeResponse(401, {"message": "Unauthorized"}),
        token="token-invalido",
    )

    result = client.smoke_test()

    assert result.ok is True
    assert result.authenticated is False
    assert "token" in result.message.lower()


def test_smoke_test_reports_missing_endpoint():
    client, _ = _client(FakeResponse(404, {"message": "Not Found"}))

    result = client.smoke_test()

    assert result.ok is False
    assert result.status_code == 404
    assert "não foi encontrado" in result.message


def test_smoke_test_reports_connection_failure():
    session = FakeSession(error=requests.ConnectionError("sem rede"))
    client = XanoClient(
        base_url="https://exemplo.xano.io/api:teste",
        session=session,
    )

    result = client.smoke_test()

    assert result.ok is False
    assert result.status_code is None
    assert "não foi possível conectar" in result.message.lower()


def test_missing_or_invalid_base_url_raises_configuration_error():
    with pytest.raises(XanoConfigurationError):
        XanoClient(base_url="")

    with pytest.raises(XanoConfigurationError):
        XanoClient(base_url="exemplo-sem-protocolo")


def test_smoke_test_helper_handles_configuration_error():
    result = smoke_test(base_url="")

    assert result.ok is False
    assert "XANO_BASE_URL" in result.message


def test_get_wraps_network_errors():
    session = FakeSession(error=requests.Timeout("timeout"))
    client = XanoClient(
        base_url="https://exemplo.xano.io/api:teste",
        session=session,
    )

    with pytest.raises(XanoConnectionError):
        client.get("/clients")
