# Integração da aplicação com o Xano

A aplicação Streamlit continua funcionando com `data/*.json` até que a camada de
persistência seja trocada. Este documento mostra o caminho recomendado para fazer essa
troca sem reescrever as telas de uma vez.

## Arquitetura sugerida

```text
Streamlit (src/views/*)
        │
        ▼
XanoClient (src/services/xano_client.py)
        │  HTTPS + Bearer token
        ▼
Xano — API group ACNnorte
        │
        ├── users
        ├── clients
        ├── visits
        └── photos (storage)
```

As telas continuam chamando funções de alto nível (`list_clients`, `create_visit`,
`save_visit`, `upload_photo`). Essas funções passam a chamar o `XanoClient` em vez de
`storage_manager.py`. Assim, a migração pode ser feita tela por tela.

## Configuração

No `.env` (desenvolvimento) ou nos secrets do Streamlit (produção):

```dotenv
XANO_BASE_URL=https://SEU-INSTANCIA.xano.io/api:acnnorte
```

O token **não** deve ser fixo no `.env` em produção. Ele é obtido no login e guardado
em `st.session_state`.

```python
import os

import streamlit as st

XANO_BASE_URL = os.getenv("XANO_BASE_URL") or st.secrets["XANO_BASE_URL"]
```

## Cliente mínimo

Crie `src/services/xano_client.py` (e um `__init__.py` na pasta) com uma classe como a
abaixo. Ela concentra URL base, token, tratamento de erro e upload de arquivos.

```python
from __future__ import annotations

from typing import Any

import requests


class XanoError(Exception):
    """Erro retornado pela API do Xano."""

    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class XanoClient:
    def __init__(self, base_url: str, token: str | None = None, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.session = requests.Session()

    # ------------------------------------------------------------------ auth
    def login(self, email: str, password: str) -> dict:
        response = self.session.post(
            f"{self.base_url}/auth/login",
            json={"email": email, "password": password},
            timeout=self.timeout,
        )
        data = self._handle(response)
        self.token = data["authToken"]
        return data

    def logout(self) -> None:
        self.token = None

    # --------------------------------------------------------------- helpers
    @property
    def headers(self) -> dict[str, str]:
        if not self.token:
            raise XanoError(401, "Sessão expirada. Faça login novamente.")
        return {"Authorization": f"Bearer {self.token}"}

    def _handle(self, response: requests.Response) -> Any:
        if response.ok:
            return response.json() if response.content else None
        try:
            message = response.json().get("message", response.text)
        except ValueError:
            message = response.text
        raise XanoError(response.status_code, message)

    def get(self, path: str, params: dict | None = None) -> Any:
        response = self.session.get(
            f"{self.base_url}{path}",
            headers=self.headers,
            params=params,
            timeout=self.timeout,
        )
        return self._handle(response)

    def post(self, path: str, payload: dict | None = None) -> Any:
        response = self.session.post(
            f"{self.base_url}{path}",
            headers=self.headers,
            json=payload or {},
            timeout=self.timeout,
        )
        return self._handle(response)

    def patch(self, path: str, payload: dict | None = None) -> Any:
        response = self.session.patch(
            f"{self.base_url}{path}",
            headers=self.headers,
            json=payload or {},
            timeout=self.timeout,
        )
        return self._handle(response)

    def delete(self, path: str) -> Any:
        response = self.session.delete(
            f"{self.base_url}{path}",
            headers=self.headers,
            timeout=self.timeout,
        )
        return self._handle(response)

    # ---------------------------------------------------------------- photos
    def upload_photo(
        self,
        visit_id: int,
        file_bytes: bytes,
        filename: str,
        caption: str = "",
        display_order: int = 0,
    ) -> dict:
        response = self.session.post(
            f"{self.base_url}/photos",
            headers=self.headers,
            data={
                "visit_id": visit_id,
                "caption": caption,
                "display_order": display_order,
            },
            files={"image": (filename, file_bytes)},
            timeout=self.timeout,
        )
        return self._handle(response)

    def replace_photo(
        self,
        photo_id: int,
        file_bytes: bytes | None = None,
        filename: str | None = None,
        caption: str | None = None,
        display_order: int | None = None,
    ) -> dict:
        data = {}
        if caption is not None:
            data["caption"] = caption
        if display_order is not None:
            data["display_order"] = display_order

        files = None
        if file_bytes is not None:
            files = {"image": (filename or "foto.jpg", file_bytes)}

        response = self.session.patch(
            f"{self.base_url}/photos/{photo_id}",
            headers=self.headers,
            data=data,
            files=files,
            timeout=self.timeout,
        )
        return self._handle(response)
```

O `requests` já foi adicionado ao `requirements.txt` nesta entrega, embora a aplicação
ainda não o utilize em runtime:

```text
requests>=2.31.0
```

## Exemplos de uso

### Login e sessão

```python
client = XanoClient(XANO_BASE_URL)
auth = client.login("admin@acnnorte.com.br", "senha-forte")

st.session_state["xano_token"] = auth["authToken"]
st.session_state["user"] = auth["user"]

# Nas próximas execuções do Streamlit:
client = XanoClient(XANO_BASE_URL, token=st.session_state["xano_token"])
```

> O Streamlit reexecuta o script a cada interação. Recrie o `XanoClient` a partir do
> token salvo em `st.session_state`; não faça login em toda rerun.

### Clientes

```python
# Listar (busca opcional)
page = client.get("/clients", params={"name": "norte", "page": 1, "per_page": 50})
clientes = page.get("items", page)

# Criar
novo = client.post("/clients", {
    "name": "Indústria Norte Ltda",
    "cnpj": "00000000000100",
    "responsible_person": "Carlos Alberto",
    "phone": "(92) 99999-9999",
    "email": "contato@norte.com.br",
    "address": "Av. Industrial, 1000 — Manaus/AM",
})

# Detalhe + histórico
detalhe = client.get(f"/clients/{novo['id']}")

# Editar
client.patch(f"/clients/{novo['id']}", {"phone": "(92) 98888-8888"})

# Desativar
client.delete(f"/clients/{novo['id']}")
```

### Visitas e autosave

```python
visita = client.post("/visits", {
    "client_id": novo["id"],
    "visit_date": "2026-11-08",
})

# Autosave de uma seção
client.patch(f"/visits/{visita['id']}", {
    "current_step": 2,
    "checklist_epi": {
        "epi_fornecimento": "Sim",
        "epi_uso": "Parcial",
        "epi_conservacao": "Sim",
        "epi_ca": "Sim",
        "epi_obs": "Reposição pendente.",
    },
})

# Salvar observações
client.patch(f"/visits/{visita['id']}", {
    "general_observations": "Recomendada revisão da iluminação no setor B."
})

# Finalizar
client.post(f"/visits/{visita['id']}/finalize")
```

### Fotografias

```python
with open("foto.jpg", "rb") as arquivo:
    foto = client.upload_photo(
        visit_id=visita["id"],
        file_bytes=arquivo.read(),
        filename="foto.jpg",
        caption="Extintor do setor A",
        display_order=1,
    )

# Substituir apenas a legenda
client.replace_photo(foto["id"], caption="Extintor do setor A — atualizado")

# Substituir o arquivo
with open("foto-nova.jpg", "rb") as arquivo:
    client.replace_photo(foto["id"], file_bytes=arquivo.read(), filename="foto-nova.jpg")

# Excluir
client.delete(f"/photos/{foto['id']}")
```

## Mapeamento das funções atuais

| Função em `storage_manager.py` | Equivalente no Xano |
| --- | --- |
| `load_clients()` | `GET /clients` |
| `add_client(...)` | `POST /clients` |
| `update_client(...)` | `PATCH /clients/{id}` |
| `delete_client(...)` | `DELETE /clients/{id}` (soft delete) |
| `load_visits()` | `GET /visits` (com filtros) |
| `add_visit(...)` | `POST /visits` |
| `update_visit(...)` | `PATCH /visits/{id}` + `POST /visits/{id}/finalize` |
| `load photos` (array na visita) | `GET /photos?visit_id=` |
| `add_photo_to_visit(...)` | `POST /photos` (multipart) |
| `replace_photo_in_visit(...)` | `PATCH /photos/{id}` (multipart) |
| `remove_photo_from_visit(...)` | `DELETE /photos/{id}` |

## Passos de migração recomendados

1. **Crie o backend e o administrador** seguindo o `README.md`.
2. **Valide a API isoladamente** com os `curl` do README antes de mexer no app.
3. **Adicione o `XanoClient`** e um teste unitário com `responses` ou `unittest.mock`
   para não depender da rede.
4. **Troque o login** (`auth_manager.authenticate_user`) por `client.login(...)`.
   Guarde `authToken` e o perfil em `st.session_state`.
5. **Troque clientes** primeiro: são poucos campos e validam o padrão de listagem,
   criação e edição.
6. **Troque visitas** mantendo o autosave atual; cada alteração de campo pode chamar
   `PATCH /visits/{id}` com apenas a seção modificada.
7. **Troque fotografias** por último, usando `multipart/form-data`.
8. **Migre os dados** com um script único (veja `schema.md`) ou comece com o banco vazio
   e recadastre os clientes.
9. **Remova o JSON** somente depois de validar todos os fluxos em um ambiente de teste.

## Cuidados

- **Token expirado:** o Xano retorna `401`. Capture `XanoError` com `status_code == 401`,
  limpe a sessão e peça login novamente.
- **Uploads grandes:** o limite depende do plano/instância do Xano. Comprima as imagens
  antes de enviar para manter a galeria rápida.
- **Datas:** envie `YYYY-MM-DD` em `visit_date`, `date_from` e `date_to`.
- **CNPJ:** normalize para somente dígitos antes de enviar. O índice unique é textual.
- **Concorrência:** o autosave envia apenas os campos alterados; evite enviar o objeto
  inteiro para não sobrescrever alterações de outro usuário.
- **Exclusão de cliente:** o endpoint é lógico. Se precisar de exclusão definitiva, crie
  um endpoint administrativo separado e trate as visitas vinculadas.
