"""Testes do serviço de autenticação Xano, sem chamadas de rede reais."""

from __future__ import annotations

import pytest

import src.modules.authentication.auth_service as auth_service
from src.core.database.xano_client import (
    XanoConfigurationError,
    XanoConnectionError,
    XanoError,
)


class FakeXanoClient:
    """Substitui o cliente real e registra a chamada de login."""

    instances: list["FakeXanoClient"] = []
    response: dict | Exception = {}
    token_arg: str | None = "não-informado"

    def __init__(self, token=None, **_kwargs):
        self.token = token
        self.post_calls: list[tuple[str, dict]] = []
        type(self).instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def post(self, path, payload=None):
        self.post_calls.append((path, payload))
        if isinstance(type(self).response, Exception):
            raise type(self).response
        return type(self).response


@pytest.fixture(autouse=True)
def reset_fake_client():
    FakeXanoClient.instances = []
    FakeXanoClient.response = {}
    FakeXanoClient.token_arg = "não-informado"
    yield
    FakeXanoClient.instances = []


def test_validate_login_fields_rejects_empty_email():
    with pytest.raises(auth_service.LoginValidationError) as exc_info:
        auth_service.validate_login_fields("   ", "senha")

    assert "e-mail" in str(exc_info.value).lower()


def test_validate_login_fields_rejects_empty_password():
    with pytest.raises(auth_service.LoginValidationError) as exc_info:
        auth_service.validate_login_fields("admin@acnnorte.com.br", "")

    assert "senha" in str(exc_info.value).lower()


def test_empty_fields_do_not_instantiate_xano_client(monkeypatch):
    monkeypatch.setattr(auth_service, "XanoClient", FakeXanoClient)

    with pytest.raises(auth_service.LoginValidationError):
        auth_service.authenticate_with_xano("", "")

    assert FakeXanoClient.instances == []


def test_login_calls_auth_login_endpoint_without_environment_token(monkeypatch):
    FakeXanoClient.response = {
        "authToken": "token-jwt",
        "role": "administrador",
        "user": {
            "id": 1,
            "name": "Ana Norte",
            "email": "admin@acnnorte.com.br",
            "role": "administrador",
            "status": "ativo",
        },
    }
    monkeypatch.setattr(auth_service, "XanoClient", FakeXanoClient)

    session = auth_service.authenticate_with_xano(
        "  Admin@ACNNORTE.com.br  ", "senha-forte"
    )

    client = FakeXanoClient.instances[0]
    assert client.token == ""
    assert client.post_calls == [
        (
            "/auth/login",
            {
                "email": "admin@acnnorte.com.br",
                "password": "senha-forte",
            },
        )
    ]
    assert session.token == "token-jwt"
    assert session.role == "administrador"
    assert session.is_admin is True
    assert session.user["name"] == "Ana Norte"


def test_login_uses_user_role_when_top_level_role_is_absent(monkeypatch):
    FakeXanoClient.response = {
        "authToken": "token-jwt",
        "user": {
            "name": "Usuário Comum",
            "email": "usuario@acnnorte.com.br",
            "role": "usuario",
        },
    }
    monkeypatch.setattr(auth_service, "XanoClient", FakeXanoClient)

    session = auth_service.authenticate_with_xano(
        "usuario@acnnorte.com.br", "senha"
    )

    assert session.role == "usuario"
    assert session.is_admin is False


def test_login_rejects_response_without_token(monkeypatch):
    FakeXanoClient.response = {"user": {"email": "admin@acnnorte.com.br"}}
    monkeypatch.setattr(auth_service, "XanoClient", FakeXanoClient)

    with pytest.raises(auth_service.AuthenticationError) as exc_info:
        auth_service.authenticate_with_xano("admin@acnnorte.com.br", "senha")

    assert "token" in str(exc_info.value).lower()


def test_invalid_credentials_are_converted_to_friendly_error(monkeypatch):
    FakeXanoClient.response = XanoError("Credenciais inválidas.", status_code=403)
    monkeypatch.setattr(auth_service, "XanoClient", FakeXanoClient)

    with pytest.raises(auth_service.AuthenticationError) as exc_info:
        auth_service.authenticate_with_xano("admin@acnnorte.com.br", "errada")

    assert exc_info.value.status_code == 403
    assert "e-mail ou senha incorretos" in str(exc_info.value).lower()


def test_connection_error_is_converted_to_friendly_error(monkeypatch):
    FakeXanoClient.response = XanoConnectionError("sem rede")
    monkeypatch.setattr(auth_service, "XanoClient", FakeXanoClient)

    with pytest.raises(auth_service.AuthenticationError) as exc_info:
        auth_service.authenticate_with_xano("admin@acnnorte.com.br", "senha")

    assert "não foi possível conectar" in str(exc_info.value).lower()


def test_configuration_error_is_converted_to_friendly_error(monkeypatch):
    FakeXanoClient.response = XanoConfigurationError("XANO_BASE_URL ausente")
    monkeypatch.setattr(auth_service, "XanoClient", FakeXanoClient)

    with pytest.raises(auth_service.AuthenticationError) as exc_info:
        auth_service.authenticate_with_xano("admin@acnnorte.com.br", "senha")

    assert "não está configurado" in str(exc_info.value).lower()


def test_non_mapping_response_is_rejected(monkeypatch):
    FakeXanoClient.response = ["resposta", "inesperada"]
    monkeypatch.setattr(auth_service, "XanoClient", FakeXanoClient)

    with pytest.raises(auth_service.AuthenticationError) as exc_info:
        auth_service.authenticate_with_xano("admin@acnnorte.com.br", "senha")

    assert "inválida" in str(exc_info.value).lower()
