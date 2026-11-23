"""Integração e sincronização das visitas do ACNnorte com o backend Xano.

Este módulo reaproveita os endpoints e tabelas existentes do API group
``ACNnorte`` (``/clients``, ``/visits``, ``/photos``) sem criar estruturas
duplicadas. Os dados estendidos do aplicativo (datas de início/término,
funcionário, equipamentos/medições, formulário completo, clima, assinaturas e
metadados de fotografias) são persistidos de forma aditiva em campos JSON/texto
já existentes:

- ``visits.general_observations``: envelope JSON versionado com todos os dados
  estendidos da visita (``_acn_ext_v1``) e a observação textual legível.
- ``visits.checklist_*``: espelho das seções do formulário para compatibilidade
  com o schema atual do Xano.
- ``photos.caption``: envelope JSON com legenda e metadados estendidos da foto.

Cada registro local recebe o identificador remoto em ``xano_id`` (e mapeamentos
auxiliares) para evitar duplicação e permitir consulta/atualização/recuperação.
A sincronização é tolerante a falhas: na ausência de configuração, rede ou
token, o armazenamento local continua funcional.
"""

from __future__ import annotations

import copy
import json
import os
import re
import tempfile
from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from src.core.database.xano_client import XanoClient, XanoError

EXT_KEY = "_acn_ext_v1"
OBS_KEY = "_acn_obs"
CAPTION_KEY = "_acn_cap"
PHOTO_META_KEY = "_acn_meta"
XANO_PAGE_SIZE = 100

CHECKLIST_FIELDS = (
    "checklist_epi",
    "checklist_condicoes_gerais",
    "checklist_incendio",
    "checklist_maquinas",
    "checklist_documentacao",
)

# Mapeamento das seções locais do formulário técnico para os checklists do Xano.
FORM_TO_CHECKLIST = {
    "epi": "checklist_epi",
    "condicoes_gerais": "checklist_condicoes_gerais",
    "incendio": "checklist_incendio",
    "maquinas": "checklist_maquinas",
    "documentacao": "checklist_documentacao",
}

LOCAL_TO_XANO_STATUS = {
    "rascunho": "rascunho",
    "em andamento": "rascunho",
    "em_andamento": "rascunho",
    "draft": "rascunho",
    "finalizada": "finalizado",
    "finalizado": "finalizado",
    "concluida": "finalizado",
    "concluída": "finalizado",
}
XANO_TO_LOCAL_STATUS = {
    "rascunho": "Em Andamento",
    "finalizado": "Finalizada",
}


def _log(message: str) -> None:
    try:
        print(f"[xano_sync] {message}")
    except Exception:
        pass


def _session_token() -> str:
    """Obtém o token do Xano da sessão Streamlit (quando disponível)."""
    try:
        import streamlit as st  # type: ignore

        token = st.session_state.get("xano_token")
        return str(token).strip() if token else ""
    except Exception:
        return ""


def _session_user_id() -> int | None:
    try:
        import streamlit as st  # type: ignore

        user = st.session_state.get("xano_user") or {}
        if isinstance(user, Mapping) and user.get("id") is not None:
            return int(user["id"])
    except Exception:
        return None
    return None


def sync_enabled(token: str | None = None) -> bool:
    """Indica se há configuração mínima para sincronizar com o Xano."""
    base_url = (os.getenv("XANO_BASE_URL", "") or "").strip()
    resolved = (token or _session_token() or "").strip()
    return bool(base_url and resolved)


def _client(token: str | None = None) -> XanoClient:
    resolved = (token or _session_token() or "").strip() or None
    return XanoClient(token=resolved)


def _safe_json_loads(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return json.loads(text)
        except Exception:
            return None
    return None


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _normalize_cnpj(value: str) -> str:
    return re.sub(r"\D", "", str(value or ""))


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _to_date(value: Any) -> str:
    text = _as_text(value).strip()
    if not text:
        return ""
    # Aceita "YYYY-MM-DD" ou "YYYY-MM-DD HH:MM:SS"
    if " " in text:
        text = text.split(" ", 1)[0]
    if "T" in text:
        text = text.split("T", 1)[0]
    return text


def _xano_status(local_status: Any) -> str:
    key = _as_text(local_status).strip().lower()
    return LOCAL_TO_XANO_STATUS.get(key, "rascunho")


def _local_status(xano_status: Any, ext: Mapping[str, Any] | None = None) -> str:
    if isinstance(ext, Mapping):
        stored = ext.get("status_local")
        if stored:
            return str(stored)
    key = _as_text(xano_status).strip().lower()
    return XANO_TO_LOCAL_STATUS.get(key, "Em Andamento")


def _checklist_payload(value: Any) -> dict:
    if isinstance(value, dict):
        return value
    parsed = _safe_json_loads(value)
    if isinstance(parsed, dict):
        return parsed
    return {}


def _pack_observations(observations: Any, ext: Mapping[str, Any]) -> str:
    # Sempre grava envelope quando há dados estendidos, preservando texto.
    payload = {OBS_KEY: _as_text(observations), EXT_KEY: dict(ext)}
    return _json_dumps(payload)


def _unpack_observations(value: Any) -> tuple[str, dict[str, Any]]:
    parsed = _safe_json_loads(value)
    if isinstance(parsed, dict) and EXT_KEY in parsed:
        obs = parsed.get(OBS_KEY, "")
        ext = parsed.get(EXT_KEY)
        return _as_text(obs), (dict(ext) if isinstance(ext, Mapping) else {})
    # Texto simples legado
    if isinstance(value, str):
        return value, {}
    return _as_text(value), {}


def _build_ext_payload(visit: Mapping[str, Any]) -> dict[str, Any]:
    """Extrai todos os dados estendidos da visita para persistência no Xano."""
    forms = visit.get("forms") if isinstance(visit.get("forms"), dict) else {}
    worker = visit.get("worker") if isinstance(visit.get("worker"), dict) else {}
    weather = visit.get("weather") if isinstance(visit.get("weather"), dict) else {}
    signatures = visit.get("signatures") if isinstance(visit.get("signatures"), dict) else {}
    equipment = visit.get("equipment") if isinstance(visit.get("equipment"), dict) else {}
    measurements = visit.get("measurements") if isinstance(visit.get("measurements"), list) else []
    photos = visit.get("photos") if isinstance(visit.get("photos"), list) else []

    # Metadados de assinaturas (nome/data/arquivo local) sem mover arquivos binários
    # para o campo de texto; os PNGs permanecem no armazenamento local.
    sig_meta: dict[str, Any] = {}
    for role, info in signatures.items():
        if not isinstance(info, dict):
            continue
        sig_meta[str(role)] = {
            "name": _as_text(info.get("name")).strip(),
            "filename": _as_text(info.get("filename")).strip(),
            "signed_at": _as_text(info.get("signed_at")).strip(),
            "local_path": _as_text(info.get("path")).strip(),
            "has_image": bool(info.get("path")),
        }

    # Mapa local_photo_id -> metadados/xano para recuperação sem duplicar upload.
    photos_meta = []
    for photo in photos:
        if not isinstance(photo, dict):
            continue
        photos_meta.append(
            {
                "local_id": _as_text(photo.get("id")),
                "xano_id": photo.get("xano_id"),
                "description": _as_text(photo.get("description")),
                "observations": _as_text(photo.get("observations")),
                "horario": _as_text(photo.get("horario")),
                "equipment_code": _as_text(photo.get("equipment_code")),
                "equipment_label": _as_text(photo.get("equipment_label")),
                "identificacao_registro": _as_text(photo.get("identificacao_registro")),
                "uploaded_at": _as_text(photo.get("uploaded_at")),
                "local_path": _as_text(photo.get("path")),
                "filename": _as_text(photo.get("filename")),
            }
        )

    ext = {
        "version": 1,
        "local_id": _as_text(visit.get("id")),
        "status_local": _as_text(visit.get("status")),
        "date": _to_date(visit.get("date")),
        "date_start": _to_date(visit.get("date_start") or visit.get("date")),
        "date_end": _to_date(visit.get("date_end") or visit.get("date_start") or visit.get("date")),
        "horario": _as_text(visit.get("horario")).strip(),
        "technician": _as_text(visit.get("technician")).strip(),
        "client_name": _as_text(visit.get("client_name")).strip(),
        "worker": {
            "name": _as_text(worker.get("name") or visit.get("worker_name")).strip(),
            "photo_path": _as_text(worker.get("photo_path") or visit.get("worker_photo")).strip(),
            "photo_filename": _as_text(worker.get("photo_filename")).strip(),
        },
        "equipment": equipment,
        "measurements": measurements,
        "weather": weather,
        "signatures": sig_meta,
        "forms": forms,
        "caderno_avaliacao": visit.get("caderno_avaliacao") if isinstance(visit.get("caderno_avaliacao"), dict) else {},
        "conclusions": _as_text(visit.get("conclusions")),
        "observations": _as_text(visit.get("observations")),
        "photos": photos_meta,
        "local_updated_at": _as_text(visit.get("updated_at")),
        "synced_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    return ext


def _build_checklists(visit: Mapping[str, Any]) -> dict[str, dict]:
    forms = visit.get("forms") if isinstance(visit.get("forms"), dict) else {}
    result: dict[str, dict] = {}
    for local_key, checklist_field in FORM_TO_CHECKLIST.items():
        section = forms.get(local_key)
        result[checklist_field] = _checklist_payload(section)
    # Garante presença de todos os campos esperados pelo Xano.
    for field in CHECKLIST_FIELDS:
        result.setdefault(field, {})
    return result


# ---------------------------------------------------------------------------
# Paginação / busca
# ---------------------------------------------------------------------------

def _iter_pages(client: XanoClient, path: str, params: dict[str, Any]) -> Iterable[list[dict]]:
    page = 1
    while True:
        query = dict(params)
        query["page"] = page
        query["per_page"] = XANO_PAGE_SIZE
        data = client.get(path, params=query)
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            items = [item for item in data["items"] if isinstance(item, dict)]
            yield items
            next_page = data.get("nextPage")
            if next_page:
                page = int(next_page)
                continue
            cur = data.get("curPage") or data.get("page") or page
            page_total = data.get("pageTotal") or data.get("total_pages")
            if page_total and int(cur) < int(page_total):
                page = int(cur) + 1
                continue
            if len(items) >= XANO_PAGE_SIZE and not page_total:
                page += 1
                continue
            return
        if isinstance(data, list):
            items = [item for item in data if isinstance(item, dict)]
            yield items
            if len(items) >= XANO_PAGE_SIZE:
                page += 1
                continue
            return
        return


def _list_all(client: XanoClient, path: str, params: dict[str, Any] | None = None) -> list[dict]:
    items: list[dict] = []
    for chunk in _iter_pages(client, path, dict(params or {})):
        items.extend(chunk)
    return items


# ---------------------------------------------------------------------------
# Clientes
# ---------------------------------------------------------------------------

def _client_payload(local: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "name": _as_text(local.get("name")).strip(),
        "cnpj": _as_text(local.get("cnpj")).strip(),
        "responsible_person": _as_text(local.get("responsible")).strip(),
        "phone": _as_text(local.get("phone")).strip(),
        "email": _as_text(local.get("email")).strip(),
        "address": _as_text(local.get("address")).strip(),
    }


def find_remote_client(client: XanoClient, local: Mapping[str, Any]) -> dict | None:
    """Localiza cliente remoto por xano_id ou por CNPJ/nome para evitar duplicatas."""
    xano_id = local.get("xano_id")
    if xano_id:
        try:
            data = client.get(f"/clients/{int(xano_id)}")
            if isinstance(data, dict):
                # GET /clients/{id} retorna {client, visits}
                if isinstance(data.get("client"), dict):
                    return data["client"]
                if data.get("id") is not None:
                    return data
        except XanoError:
            pass

    target_cnpj = _normalize_cnpj(local.get("cnpj"))
    target_name = _as_text(local.get("name")).strip().lower()
    try:
        remotes = _list_all(client, "/clients")
    except XanoError:
        return None
    for remote in remotes:
        r_cnpj = _normalize_cnpj(remote.get("cnpj"))
        r_name = _as_text(remote.get("name")).strip().lower()
        if target_cnpj and r_cnpj and target_cnpj == r_cnpj:
            return remote
        if target_name and r_name and target_name == r_name and (not target_cnpj or not r_cnpj):
            return remote
    return None


def sync_client(local_client: dict, client: XanoClient | None = None, token: str | None = None) -> dict:
    """Cria/atualiza o cliente no Xano e devolve o registro local atualizado."""
    owns = client is None
    if owns:
        if not sync_enabled(token):
            return local_client
        client = _client(token)
    assert client is not None
    try:
        payload = _client_payload(local_client)
        existing = find_remote_client(client, local_client)
        if existing and existing.get("id") is not None:
            remote = client.patch(f"/clients/{int(existing['id'])}", payload)
            if isinstance(remote, dict) and isinstance(remote.get("client"), dict):
                remote = remote["client"]
        else:
            remote = client.post("/clients", payload)
        if isinstance(remote, dict) and remote.get("id") is not None:
            local_client["xano_id"] = int(remote["id"])
            local_client["xano_synced_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    except Exception as exc:
        _log(f"falha ao sincronizar cliente {local_client.get('id')}: {exc}")
    finally:
        if owns:
            try:
                client.close()
            except Exception:
                pass
    return local_client


# ---------------------------------------------------------------------------
# Visitas
# ---------------------------------------------------------------------------

def _visit_create_payload(local: Mapping[str, Any], xano_client_id: int, xano_user_id: int | None) -> dict[str, Any]:
    visit_date = _to_date(local.get("date_start") or local.get("date")) or datetime.now().strftime("%Y-%m-%d")
    payload: dict[str, Any] = {
        "client_id": int(xano_client_id),
        "visit_date": visit_date,
    }
    if xano_user_id is not None:
        payload["user_id"] = int(xano_user_id)
    return payload


def _visit_patch_payload(local: Mapping[str, Any]) -> dict[str, Any]:
    ext = _build_ext_payload(local)
    observations = local.get("observations", "")
    payload: dict[str, Any] = {
        "general_observations": _pack_observations(observations, ext),
        "visit_date": _to_date(local.get("date_start") or local.get("date")) or datetime.now().strftime("%Y-%m-%d"),
    }
    # current_step 1-6 (Xano); mapeia progresso local de forma conservadora.
    status = _xano_status(local.get("status"))
    payload["current_step"] = 6 if status == "finalizado" else max(1, min(6, int(local.get("xano_step") or 1)))
    payload.update(_build_checklists(local))
    return payload


def _is_finalized_remote(remote: Mapping[str, Any] | None) -> bool:
    if not isinstance(remote, Mapping):
        return False
    return _as_text(remote.get("status")).strip().lower() == "finalizado"


def sync_visit(local_visit: dict, client: XanoClient | None = None, token: str | None = None,
               local_clients: dict | None = None) -> dict:
    """Cria/atualiza a visita no Xano (dados e metadados) sem duplicar registros."""
    owns = client is None
    if owns:
        if not sync_enabled(token):
            return local_visit
        client = _client(token)
    assert client is not None
    try:
        # Garante cliente vinculado no Xano.
        client_id_local = _as_text(local_visit.get("client_id"))
        if local_clients is not None and client_id_local in local_clients:
            local_clients[client_id_local] = sync_client(local_clients[client_id_local], client=client)
            xano_client_id = local_clients[client_id_local].get("xano_id")
        else:
            xano_client_id = local_visit.get("xano_client_id")

        if not xano_client_id:
            # Tenta resolver pelo nome salvo na visita.
            try:
                remotes = _list_all(client, "/clients")
                target_name = _as_text(local_visit.get("client_name")).strip().lower()
                for remote in remotes:
                    if _as_text(remote.get("name")).strip().lower() == target_name:
                        xano_client_id = remote.get("id")
                        break
            except Exception:
                xano_client_id = None

        if not xano_client_id:
            _log(f"visita {local_visit.get('id')}: cliente Xano não resolvido; sincronização adiada")
            return local_visit

        xano_visit_id = local_visit.get("xano_id")
        remote: dict | None = None
        if xano_visit_id:
            try:
                data = client.get(f"/visits/{int(xano_visit_id)}")
                if isinstance(data, dict):
                    remote = data.get("visit") if isinstance(data.get("visit"), dict) else data
            except XanoError:
                remote = None

        if not remote or remote.get("id") is None:
            create_payload = _visit_create_payload(local_visit, int(xano_client_id), _session_user_id())
            created = client.post("/visits", create_payload)
            if isinstance(created, dict):
                remote = created.get("visit") if isinstance(created.get("visit"), dict) else created
                if remote.get("id") is not None:
                    local_visit["xano_id"] = int(remote["id"])
                    xano_visit_id = local_visit["xano_id"]

        if not xano_visit_id or not remote:
            return local_visit

        local_visit["xano_client_id"] = int(xano_client_id)

        # Atualiza dados (PATCH bloqueado se finalizada no Xano; preserva remoto).
        if not _is_finalized_remote(remote):
            try:
                patched = client.patch(f"/visits/{int(xano_visit_id)}", _visit_patch_payload(local_visit))
                if isinstance(patched, dict):
                    remote = patched.get("visit") if isinstance(patched.get("visit"), dict) else patched
            except XanoError as exc:
                _log(f"PATCH visita {xano_visit_id} falhou: {exc}")

        local_visit["xano_status"] = _as_text((remote or {}).get("status"))
        local_visit["xano_synced_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Sincroniza fotografias vinculadas.
        sync_visit_photos(local_visit, client=client)
    except Exception as exc:
        _log(f"falha ao sincronizar visita {local_visit.get('id')}: {exc}")
    finally:
        if owns:
            try:
                client.close()
            except Exception:
                pass
    return local_visit


# ---------------------------------------------------------------------------
# Fotos
# ---------------------------------------------------------------------------

def _photo_caption(description: Any, meta: Mapping[str, Any]) -> str:
    payload = {CAPTION_KEY: _as_text(description), PHOTO_META_KEY: dict(meta)}
    return _json_dumps(payload)


def _unpack_caption(value: Any) -> tuple[str, dict[str, Any]]:
    parsed = _safe_json_loads(value)
    if isinstance(parsed, dict) and PHOTO_META_KEY in parsed:
        return _as_text(parsed.get(CAPTION_KEY)), dict(parsed.get(PHOTO_META_KEY) or {})
    if isinstance(value, str):
        return value, {}
    return _as_text(value), {}


def _photo_meta(local_photo: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "local_id": _as_text(local_photo.get("id")),
        "horario": _as_text(local_photo.get("horario")),
        "equipment_code": _as_text(local_photo.get("equipment_code")),
        "equipment_label": _as_text(local_photo.get("equipment_label")),
        "identificacao_registro": _as_text(local_photo.get("identificacao_registro")),
        "observations": _as_text(local_photo.get("observations")),
        "uploaded_at": _as_text(local_photo.get("uploaded_at")),
        "filename": _as_text(local_photo.get("filename") or local_photo.get("saved_filename")),
    }


def sync_visit_photos(local_visit: dict, client: XanoClient) -> None:
    """Garante que cada foto local da visita exista no Xano (upload idempotente)."""
    xano_visit_id = local_visit.get("xano_id")
    if not xano_visit_id:
        return
    photos = local_visit.get("photos")
    if not isinstance(photos, list):
        return

    # Índice remoto por id para evitar duplicatas.
    remote_by_id: dict[int, dict] = {}
    try:
        for item in _list_all(client, "/photos", {"visit_id": int(xano_visit_id)}):
            if item.get("id") is not None:
                remote_by_id[int(item["id"])] = item
    except Exception as exc:
        _log(f"não foi possível listar fotos remotas da visita {xano_visit_id}: {exc}")

    for photo in photos:
        if not isinstance(photo, dict):
            continue
        local_path = _as_text(photo.get("path"))
        if not local_path or not os.path.exists(local_path):
            # Sem arquivo local não há upload possível; mantém metadados.
            continue

        caption = _photo_caption(photo.get("description"), _photo_meta(photo))
        xano_photo_id = photo.get("xano_id")
        try:
            if xano_photo_id and int(xano_photo_id) in remote_by_id:
                # Atualiza metadados se necessário.
                client.patch(
                    f"/photos/{int(xano_photo_id)}",
                    data={"caption": caption, "display_order": str(photo.get("display_order", 0) or 0)},
                )
                continue

            with open(local_path, "rb") as fh:
                filename = _as_text(photo.get("filename") or os.path.basename(local_path)) or "foto.jpg"
                files = {"image": (filename, fh, "application/octet-stream")}
                data = {
                    "visit_id": str(int(xano_visit_id)),
                    "caption": caption,
                    "display_order": str(photo.get("display_order", 0) or 0),
                }
                created = client.post("/photos", data=data, files=files)
            if isinstance(created, dict) and created.get("id") is not None:
                photo["xano_id"] = int(created["id"])
                if isinstance(created.get("image"), dict):
                    photo["xano_image"] = created["image"]
                photo["xano_synced_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        except Exception as exc:
            _log(f"falha ao sincronizar foto {photo.get('id')} da visita {xano_visit_id}: {exc}")

# ---------------------------------------------------------------------------
# Recuperação (Xano -> local)
# ---------------------------------------------------------------------------

def _remote_visit_to_local(remote: Mapping[str, Any], existing: dict | None = None) -> dict:
    visit_data = remote.get("visit") if isinstance(remote.get("visit"), dict) else remote
    photos_remote = remote.get("photos") if isinstance(remote.get("photos"), list) else []
    observations_text, ext = _unpack_observations(visit_data.get("general_observations"))

    local = copy.deepcopy(existing) if isinstance(existing, dict) else {}
    local_id = ext.get("local_id") or local.get("id") or f"xano_{visit_data.get('id')}"
    local["id"] = str(local_id)
    local["xano_id"] = visit_data.get("id")
    local["xano_client_id"] = visit_data.get("client_id")
    local["xano_status"] = _as_text(visit_data.get("status"))
    local["client_id"] = _as_text(local.get("client_id") or ext.get("client_id") or "")
    local["client_name"] = _as_text(ext.get("client_name") or local.get("client_name") or "")
    local["date"] = _to_date(ext.get("date") or visit_data.get("visit_date"))
    local["date_start"] = _to_date(ext.get("date_start") or local["date"])
    local["date_end"] = _to_date(ext.get("date_end") or local["date_start"])
    local["horario"] = _as_text(ext.get("horario") or local.get("horario") or "")
    local["technician"] = _as_text(ext.get("technician") or local.get("technician") or "")
    local["status"] = _local_status(visit_data.get("status"), ext)
    local["worker"] = ext.get("worker") or local.get("worker") or {"name": "", "photo_path": "", "photo_filename": ""}
    local["worker_name"] = _as_text((local.get("worker") or {}).get("name") or local.get("worker_name") or "")
    local["forms"] = ext.get("forms") or local.get("forms") or {}
    # Se não houver forms estendidos, tenta reconstruir dos checklists.
    if not local["forms"]:
        rebuilt = {}
        for local_key, checklist_field in FORM_TO_CHECKLIST.items():
            value = visit_data.get(checklist_field)
            if isinstance(value, dict) and value:
                rebuilt[local_key] = value
        if rebuilt:
            local["forms"] = rebuilt
    ext_caderno = ext.get("caderno_avaliacao")
    if isinstance(ext_caderno, dict) and ext_caderno:
        current_caderno = local.get("caderno_avaliacao") if isinstance(local.get("caderno_avaliacao"), dict) else {}
        merged_caderno = dict(current_caderno)
        merged_caderno.update(ext_caderno)
        local["caderno_avaliacao"] = merged_caderno
    elif "caderno_avaliacao" not in local or not isinstance(local.get("caderno_avaliacao"), dict):
        local["caderno_avaliacao"] = {}
    local["observations"] = observations_text if observations_text else _as_text(ext.get("observations") or "")
    local["conclusions"] = _as_text(ext.get("conclusions") or local.get("conclusions") or "")
    local["equipment"] = ext.get("equipment") or local.get("equipment") or {"category": "", "selected": []}
    local["measurements"] = ext.get("measurements") or local.get("measurements") or []
    local["weather"] = ext.get("weather") or local.get("weather") or {}
    # Assinaturas: recupera metadados (nome/horário) do envelope; arquivo local preservado se existir.
    ext_sigs = ext.get("signatures") if isinstance(ext.get("signatures"), dict) else {}
    sigs = local.get("signatures") if isinstance(local.get("signatures"), dict) else {}
    for role, meta in ext_sigs.items():
        if not isinstance(meta, dict):
            continue
        cur = sigs.get(role) if isinstance(sigs.get(role), dict) else {}
        cur = dict(cur)
        cur["name"] = _as_text(meta.get("name") or cur.get("name") or "")
        if meta.get("signed_at") and not cur.get("signed_at"):
            cur["signed_at"] = _as_text(meta.get("signed_at"))
        sigs[role] = cur
    local["signatures"] = sigs

    # Fotos: preserva locais e mescla metadados remotos.
    local_photos = local.get("photos") if isinstance(local.get("photos"), list) else []
    by_xano = {int(p.get("xano_id")): p for p in local_photos if isinstance(p, dict) and p.get("xano_id")}
    for rp in photos_remote:
        if not isinstance(rp, dict) or rp.get("id") is None:
            continue
        rid = int(rp["id"])
        desc, meta = _unpack_caption(rp.get("caption"))
        target = by_xano.get(rid)
        if not target:
            # Foto conhecida apenas no Xano: registra referência remota.
            target = {"id": meta.get("local_id") or f"xano_photo_{rid}", "path": ""}
            local_photos.append(target)
            by_xano[rid] = target
        target["xano_id"] = rid
        if isinstance(rp.get("image"), dict):
            target["xano_image"] = rp["image"]
        if desc and not target.get("description"):
            target["description"] = desc
        for k in ("horario", "equipment_code", "equipment_label", "identificacao_registro", "observations", "uploaded_at", "filename"):
            if meta.get(k) and not target.get(k):
                target[k] = meta.get(k)
    local["photos"] = local_photos
    local["xano_synced_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    local.setdefault("created_at", _as_text(visit_data.get("created_at")))
    local["updated_at"] = _as_text(visit_data.get("updated_at") or local.get("updated_at") or "")
    return local


def fetch_visit(xano_visit_id: int, client: XanoClient | None = None, token: str | None = None) -> dict | None:
    """Recupera uma visita do Xano (GET /visits/{id}) com suas fotos."""
    owns = client is None
    if owns:
        if not sync_enabled(token):
            return None
        client = _client(token)
    assert client is not None
    try:
        data = client.get(f"/visits/{int(xano_visit_id)}")
        if isinstance(data, dict):
            return data
        return None
    except Exception as exc:
        _log(f"falha ao recuperar visita {xano_visit_id}: {exc}")
        return None
    finally:
        if owns:
            try:
                client.close()
            except Exception:
                pass


def pull_visits(token: str | None = None) -> list[dict]:
    """Consulta visitas no Xano e retorna representações locais recuperadas."""
    if not sync_enabled(token):
        return []
    result: list[dict] = []
    with _client(token) as client:
        try:
            summaries = _list_all(client, "/visits")
        except Exception as exc:
            _log(f"falha ao listar visitas no Xano: {exc}")
            return []
        for summary in summaries:
            vid = summary.get("id") if isinstance(summary, dict) else None
            if vid is None:
                continue
            try:
                detail = client.get(f"/visits/{int(vid)}")
                if isinstance(detail, dict):
                    result.append(_remote_visit_to_local(detail))
            except Exception as exc:
                _log(f"falha ao recuperar visita {vid}: {exc}")
    return result


def test_persistence(token: str | None = None) -> dict[str, Any]:
    """Executa criação, consulta, atualização e recuperação reais no Xano.

    Requer credenciais válidas (token). Retorna um relatório com evidências de
    que os registros foram efetivamente persistidos no banco de dados.
    """
    if not sync_enabled(token):
        return {
            "ok": False,
            "reason": "Xano não configurado ou token ausente.",
            "steps": {},
        }

    steps: dict[str, Any] = {}
    ok = True
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    with _client(token) as client:
        # 1) Criar cliente
        try:
            created_client = client.post(
                "/clients",
                {
                    "name": f"ACN Sync Test {stamp}",
                    "cnpj": f"{stamp[-8:]}000190",
                    "responsible_person": "Teste Integração",
                    "phone": "000",
                    "email": f"sync{stamp}@example.invalid",
                    "address": "Endereço Teste",
                },
            )
            cid = int(created_client["id"])
            steps["create_client"] = {"ok": True, "id": cid}
        except Exception as exc:
            steps["create_client"] = {"ok": False, "error": str(exc)}
            return {"ok": False, "steps": steps}

        # 2) Criar visita
        try:
            visit_date = datetime.now().strftime("%Y-%m-%d")
            created_visit = client.post(
                "/visits",
                {"client_id": cid, "visit_date": visit_date},
            )
            vid = int(created_visit["id"])
            steps["create_visit"] = {"ok": True, "id": vid}
        except Exception as exc:
            steps["create_visit"] = {"ok": False, "error": str(exc)}
            ok = False
            vid = None

        # 3) Atualizar visita (PATCH) com envelope estendido
        if vid:
            try:
                ext = {
                    EXT_KEY: {
                        "version": 1,
                        "local_id": f"test_{stamp}",
                        "status_local": "Em Andamento",
                        "date_start": visit_date,
                        "date_end": visit_date,
                        "technician": "Técnico Teste",
                        "equipment": {"category": "Dosimetria de Ruído", "selected": [{"codigo": "CHR-2386", "identificacao": "2386"}]},
                        "measurements": [{"id": "meas_CHR-2386", "equipment_code": "CHR-2386", "horario": "08:30", "identificacao_registro": "08:30 — Chrompack 2386"}],
                        "weather": {"temperature_c": 25.0, "source": "Manual"},
                        "worker": {"name": "Funcionário Teste"},
                        "forms": {"epi": {"ok": True}},
                        "conclusions": "Conclusão teste",
                        "synced_at": stamp,
                    },
                    OBS_KEY: "Observação teste",
                }
                patched = client.patch(
                    f"/visits/{vid}",
                    {
                        "general_observations": _json_dumps(ext),
                        "checklist_epi": {"ok": True},
                        "checklist_condicoes_gerais": {"ok": True},
                        "checklist_incendio": {"ok": True},
                        "checklist_maquinas": {"ok": True},
                        "checklist_documentacao": {"ok": True},
                        "current_step": 2,
                    },
                )
                steps["update_visit"] = {"ok": True, "updated_at": (patched or {}).get("updated_at")}
            except Exception as exc:
                steps["update_visit"] = {"ok": False, "error": str(exc)}
                ok = False

        # 4) Consultar/recuperar visita (GET) e confirmar persistência do envelope
        if vid:
            try:
                fetched = client.get(f"/visits/{vid}")
                visit_obj = fetched.get("visit") if isinstance(fetched, dict) and isinstance(fetched.get("visit"), dict) else fetched
                raw = (visit_obj or {}).get("general_observations")
                _, ext_back = _unpack_observations(raw)
                persisted = bool(ext_back) and ext_back.get("technician") == "Técnico Teste"
                steps["fetch_visit"] = {
                    "ok": bool(persisted),
                    "id": vid,
                    "has_ext": bool(ext_back),
                    "technician": ext_back.get("technician"),
                    "equipment_persisted": bool((ext_back.get("equipment") or {}).get("selected")),
                }
                if not persisted:
                    ok = False
            except Exception as exc:
                steps["fetch_visit"] = {"ok": False, "error": str(exc)}
                ok = False

        # 5) Consultar listagem
        try:
            listing = client.get("/visits", params={"client_id": cid, "page": 1, "per_page": 10})
            items = listing.get("items") if isinstance(listing, dict) else listing
            found = any(isinstance(it, dict) and int(it.get("id", -1)) == int(vid or -1) for it in (items or []))
            steps["query_visits"] = {"ok": found, "found": found}
            if not found:
                ok = False
        except Exception as exc:
            steps["query_visits"] = {"ok": False, "error": str(exc)}
            ok = False

        # 6) Upload/consulta de foto (se possível)
        if vid:
            try:
                from PIL import Image

                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp_path = tmp.name
                try:
                    Image.new("RGB", (2, 2), (10, 120, 60)).save(tmp_path, format="PNG")
                    caption = _photo_caption("Foto teste", {"local_id": "p_test", "horario": "08:30", "equipment_label": "Chrompack 2386"})
                    with open(tmp_path, "rb") as fh:
                        created_photo = client.post(
                            "/photos",
                            data={"visit_id": str(vid), "caption": caption, "display_order": "0"},
                            files={"image": ("teste.png", fh, "image/png")},
                        )
                    pid = int(created_photo["id"])
                    fetched_photos = client.get("/photos", params={"visit_id": vid})
                    pitems = fetched_photos.get("items") if isinstance(fetched_photos, dict) else fetched_photos
                    pfound = any(isinstance(it, dict) and int(it.get("id", -1)) == pid for it in (pitems or []))
                    steps["photo_upload_and_query"] = {"ok": pfound, "photo_id": pid, "found": pfound}
                    if not pfound:
                        ok = False
                finally:
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass
            except Exception as exc:
                steps["photo_upload_and_query"] = {"ok": False, "error": str(exc)}
                ok = False

    return {"ok": ok, "steps": steps, "client_id": locals().get("cid"), "visit_id": locals().get("vid")}


__all__ = [
    "EXT_KEY",
    "fetch_visit",
    "pull_visits",
    "sync_client",
    "sync_enabled",
    "sync_visit",
    "test_persistence",
]
