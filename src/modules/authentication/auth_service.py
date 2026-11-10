"""Autenticação via Xano para a tela de login do ACNnorte.

A validação de campos acontece antes de qualquer chamada HTTP. Assim, o formulário
vazio não dispara requisição e o usuário recebe uma mensagem amigável no Streamlit.

O fluxo local de usuários sem ``@`` continua disponível na tela de login para não
quebrar as contas legadas criadas pelas CHANGES anteriores. Contas identificadas por
e-mail são autenticadas no endpoint ``POST /auth/login`` do Xano.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from src.core.database.xano_client import (
    XanoClient,
    XanoConfigurationError,
    XanoConnectionError,
    XanoError,
)


class LoginValidationError(ValueError):
    """Campos obrigatórios ausentes no formulário de login."""


class AuthenticationError(Exception):
    """Falha amigável de autenticação para ser exibida ao usuário."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class XanoSession:
    """Dados de sessão retornados pelo login do Xano."""

    token: str
    role: str
    user: dict[str, Any]

    @property
    def is_admin(self) -> bool:
        return self.role == "administrador"


def validate_login_fields(email: str, password: str) -> None:
    """Valida os campos antes de criar o cliente Xano ou disparar HTTP."""
    if not email or not email.strip():
        raise LoginValidationError("Informe o e-mail para continuar.")
    if not password or not password.strip():
        raise LoginValidationError("Informe a senha para continuar.")


def authenticate_with_xano(email: str, password: str) -> XanoSession:
    """Autentica e-mail/senha no endpoint ``/auth/login`` do Xano.

    A validação ocorre antes da instanciação do ``XanoClient``. O token é criado
    sem reaproveitar ``XANO_AUTH_TOKEN`` do ambiente, pois o login é justamente o
    momento de obter um novo token.
    """
    validate_login_fields(email, password)
    normalized_email = email.strip().lower()

    try:
        with XanoClient(token="") as client:
            data = client.post(
                "/auth/login",
                {"email": normalized_email, "password": password},
            )
    except XanoError as exc:
        raise AuthenticationError(
            _friendly_xano_error(exc),
            status_code=exc.status_code,
        ) from exc
    except Exception as exc:  # pragma: no cover - proteção contra falhas inesperadas
        raise AuthenticationError(
            "Não foi possível realizar o login. Tente novamente."
        ) from exc

    if not isinstance(data, Mapping):
        raise AuthenticationError("O servidor retornou uma resposta de login inválida.")

    user = data.get("user")
    user_data = dict(user) if isinstance(user, Mapping) else {}
    role = str(data.get("role") or user_data.get("role") or "usuario").strip()
    token = data.get("authToken")

    if not role:
        role = "usuario"
    if not isinstance(token, str) or not token.strip():
        raise AuthenticationError(
            "O servidor não retornou um token de acesso válido. Tente novamente."
        )

    return XanoSession(token=token.strip(), role=role, user=user_data)


def _friendly_xano_error(exc: XanoError) -> str:
    """Converte erros técnicos do cliente em mensagens adequadas ao login."""
    if isinstance(exc, XanoConfigurationError):
        return "O servidor de autenticação não está configurado. Procure o administrador."
    if isinstance(exc, XanoConnectionError):
        return "Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente."

    if exc.status_code in {400, 401, 403}:
        return "E-mail ou senha incorretos. Verifique os dados e tente novamente."
    if exc.status_code == 404:
        return "O serviço de autenticação não foi encontrado. Verifique a configuração do servidor."
    if exc.status_code is not None and exc.status_code >= 500:
        return "O servidor de autenticação está indisponível no momento. Tente novamente em instantes."

    return "Não foi possível realizar o login. Tente novamente."


__all__ = [
    "AuthenticationError",
    "LoginValidationError",
    "XanoSession",
    "authenticate_with_xano",
    "validate_login_fields",
]
