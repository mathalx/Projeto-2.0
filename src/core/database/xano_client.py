"""Cliente HTTP mínimo para o API group ACNnorte no Xano.

O módulo não depende de Streamlit e pode ser usado pela aplicação, por scripts de
migração e por testes. A URL base é lida de ``XANO_BASE_URL`` no arquivo ``.env``
(ou do ambiente) e o token opcional de ``XANO_AUTH_TOKEN``.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

import requests

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependência opcional em runtime
    load_dotenv = None


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"
DEFAULT_SMOKE_PATH = "/auth/me"


class XanoError(Exception):
    """Erro retornado pela API ou pela configuração do cliente Xano."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        payload: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload


class XanoConfigurationError(XanoError):
    """Configuração ausente ou inválida (por exemplo, URL base vazia)."""


class XanoConnectionError(XanoError):
    """Falha de rede, DNS, TLS ou timeout ao alcançar o Xano."""


@dataclass(frozen=True)
class SmokeTestResult:
    """Resultado da validação de conexão com o API group."""

    ok: bool
    authenticated: bool
    status_code: int | None
    message: str
    url: str
    latency_ms: int


def _load_env_file() -> None:
    """Carrega o .env do projeto sem sobrescrever variáveis já definidas."""
    if load_dotenv is not None and ENV_FILE.exists():
        load_dotenv(ENV_FILE, override=False)


class XanoClient:
    """Acesso HTTP ao backend Xano com tratamento de erros e token opcional."""

    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        timeout: float = 15.0,
        session: requests.Session | None = None,
    ) -> None:
        _load_env_file()
        if base_url is None:
            base_url = os.getenv("XANO_BASE_URL", "")

        resolved_url = (base_url or "").strip().rstrip("/")
        if not resolved_url:
            raise XanoConfigurationError(
                "XANO_BASE_URL não configurada. Defina a URL do API group no arquivo .env."
            )

        parsed = urlparse(resolved_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise XanoConfigurationError(
                f"XANO_BASE_URL inválida: {resolved_url!r}. Informe a URL completa do API group."
            )

        if token is None:
            token = (os.getenv("XANO_AUTH_TOKEN", "") or "").strip() or None

        self.base_url = resolved_url
        self.token = token
        self.timeout = timeout
        self.session = session or requests.Session()

    def close(self) -> None:
        """Fecha a sessão HTTP subjacente."""
        self.session.close()

    def __enter__(self) -> "XanoClient":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    @property
    def headers(self) -> dict[str, str]:
        """Cabeçalhos padrão, incluindo o Bearer token quando configurado."""
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _build_url(self, path: str) -> str:
        if not path:
            return self.base_url
        return f"{self.base_url}/{path.lstrip('/')}"

    def _request_raw(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        data: Any = None,
        files: Any = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
        allow_statuses: tuple[int, ...] = (),
    ) -> requests.Response:
        url = self._build_url(path)
        request_headers = self.headers
        if headers:
            request_headers.update(headers)

        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                params=params,
                json=json,
                data=data,
                files=files,
                headers=request_headers,
                timeout=self.timeout if timeout is None else timeout,
            )
        except requests.RequestException as exc:
            raise XanoConnectionError(
                f"Não foi possível conectar ao Xano em {url}. "
                "Verifique a URL, a internet e o status do workspace."
            ) from exc

        if response.status_code >= 400 and response.status_code not in allow_statuses:
            raise self._error_from_response(response)
        return response

    @staticmethod
    def _decode(response: requests.Response) -> Any:
        if not response.content:
            return None
        try:
            return response.json()
        except ValueError:
            return response.text

    @staticmethod
    def _error_from_response(response: requests.Response) -> XanoError:
        payload: Any = None
        message = ""
        try:
            payload = response.json()
        except ValueError:
            payload = None

        if isinstance(payload, dict):
            message = str(
                payload.get("message")
                or payload.get("error")
                or payload.get("code")
                or ""
            ).strip()
        elif isinstance(payload, str):
            message = payload.strip()

        if not message:
            message = f"O Xano retornou HTTP {response.status_code}."

        return XanoError(message, status_code=response.status_code, payload=payload)

    def get(
        self,
        path: str,
        params: Mapping[str, Any] | None = None,
        *,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Executa um GET e retorna o JSON decodificado (ou texto puro)."""
        response = self._request_raw(
            "GET",
            path,
            params=params,
            headers=headers,
            timeout=timeout,
        )
        return self._decode(response)

    def post(
        self,
        path: str,
        json: Any = None,
        *,
        data: Any = None,
        files: Any = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Executa um POST JSON ou multipart/form-data."""
        response = self._request_raw(
            "POST",
            path,
            json=json,
            data=data,
            files=files,
            params=params,
            headers=headers,
            timeout=timeout,
        )
        return self._decode(response)

    def patch(
        self,
        path: str,
        json: Any = None,
        *,
        data: Any = None,
        files: Any = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Executa um PATCH JSON ou multipart/form-data."""
        response = self._request_raw(
            "PATCH",
            path,
            json=json,
            data=data,
            files=files,
            params=params,
            headers=headers,
            timeout=timeout,
        )
        return self._decode(response)

    def delete(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Executa um DELETE e retorna o JSON decodificado."""
        response = self._request_raw(
            "DELETE",
            path,
            params=params,
            headers=headers,
            timeout=timeout,
        )
        return self._decode(response)

    def smoke_test(self, path: str = DEFAULT_SMOKE_PATH) -> SmokeTestResult:
        """Valida a URL do API group sem exigir um token válido.

        Um retorno 401/403 é considerado sucesso de conectividade: significa que o
        Xano respondeu e aplicou a camada de autenticação. Um 404 indica que a URL
        respondeu, mas o endpoint de verificação não existe no grupo importado.
        """
        started = time.perf_counter()
        url = self._build_url(path)

        try:
            response = self._request_raw(
                "GET",
                path,
                timeout=min(self.timeout, 10.0),
                allow_statuses=(401, 403),
            )
        except XanoConnectionError as exc:
            return SmokeTestResult(
                ok=False,
                authenticated=False,
                status_code=None,
                message=str(exc),
                url=url,
                latency_ms=self._elapsed_ms(started),
            )
        except XanoError as exc:
            if exc.status_code == 404:
                message = (
                    f"A URL do Xano respondeu, mas o endpoint {path} não foi encontrado. "
                    "Confirme se o API group ACNnorte foi importado."
                )
            else:
                message = (
                    f"O Xano respondeu com erro HTTP {exc.status_code}: {exc.message}"
                )
            return SmokeTestResult(
                ok=False,
                authenticated=False,
                status_code=exc.status_code,
                message=message,
                url=url,
                latency_ms=self._elapsed_ms(started),
            )

        latency = self._elapsed_ms(started)
        if 200 <= response.status_code < 300:
            return SmokeTestResult(
                ok=True,
                authenticated=True,
                status_code=response.status_code,
                message=f"Conexão com o Xano validada em {latency} ms.",
                url=url,
                latency_ms=latency,
            )

        if self.token:
            message = (
                "Conexão com o Xano validada, mas o token configurado foi recusado. "
                "Faça login novamente para renovar o token."
            )
        else:
            message = (
                f"Conexão com o Xano validada em {latency} ms "
                "(autenticação necessária para acessar os dados)."
            )

        return SmokeTestResult(
            ok=True,
            authenticated=False,
            status_code=response.status_code,
            message=message,
            url=url,
            latency_ms=latency,
        )

    @staticmethod
    def _elapsed_ms(started: float) -> int:
        return max(0, int((time.perf_counter() - started) * 1000))


def smoke_test(
    base_url: str | None = None,
    token: str | None = None,
    timeout: float = 15.0,
) -> SmokeTestResult:
    """Atalho para validar a conexão usando a configuração do ambiente."""
    try:
        with XanoClient(base_url=base_url, token=token, timeout=timeout) as client:
            return client.smoke_test()
    except XanoError as exc:
        configured_url = base_url if base_url is not None else os.getenv("XANO_BASE_URL", "")
        resolved_url = (configured_url or "").rstrip("/")
        return SmokeTestResult(
            ok=False,
            authenticated=False,
            status_code=exc.status_code,
            message=str(exc),
            url=f"{resolved_url}{DEFAULT_SMOKE_PATH}" if resolved_url else "",
            latency_ms=0,
        )


__all__ = [
    "DEFAULT_SMOKE_PATH",
    "SmokeTestResult",
    "XanoClient",
    "XanoConfigurationError",
    "XanoConnectionError",
    "XanoError",
    "smoke_test",
]
