import base64
import os
import json
import uuid
from datetime import datetime


def _try_xano_sync_client(client: dict) -> dict:
    """Sincroniza um cliente com o Xano (best-effort), sem bloquear o fluxo local."""
    try:
        from src.xano_sync import sync_client, sync_enabled

        if sync_enabled():
            return sync_client(dict(client))
    except Exception:
        pass
    return client


def _try_xano_sync_visit(visit: dict, visits: dict = None) -> dict:
    """Sincroniza uma visita com o Xano (best-effort), sem bloquear o fluxo local."""
    try:
        from src.xano_sync import sync_visit, sync_enabled

        if sync_enabled():
            clients = load_clients()
            synced = sync_visit(dict(visit), local_clients=clients)
            # Persiste possíveis mapeamentos de cliente atualizados.
            try:
                save_clients(clients)
            except Exception:
                pass
            return synced
    except Exception:
        pass
    return visit

from src.equipment_catalog import (
    DEFAULT_CATEGORY,
    equipment_by_code,
    equipment_label,
    normalize_equipment_codes,
)

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
CLIENTS_FILE = os.path.join(DATA_DIR, "clients.json")
VISITS_FILE = os.path.join(DATA_DIR, "visits.json")
PHOTOS_DIR = os.path.join(DATA_DIR, "photos")

SIGNATURE_ROLES = ("technical", "evaluator")
SIGNATURE_LABELS = {
    "technical": "Responsável Técnico",
    "evaluator": "Avaliador",
}
SIGNATURE_MAX_BYTES = 2 * 1024 * 1024  # 2 MB por assinatura

EQUIPMENT_CATEGORY = DEFAULT_CATEGORY


def get_worker_photos_dir() -> str:
    """Retorna e cria o diretório de fotografias dos funcionários."""
    path = os.path.join(PHOTOS_DIR, "workers")
    os.makedirs(path, exist_ok=True)
    return path


def get_signatures_dir() -> str:
    """Retorna e cria o diretório das assinaturas digitais."""
    path = os.path.join(PHOTOS_DIR, "signatures")
    os.makedirs(path, exist_ok=True)
    return path


def _empty_signature() -> dict:
    return {"name": "", "path": "", "filename": "", "signed_at": ""}


def _ensure_signatures(visit: dict) -> dict:
    signatures = visit.get("signatures")
    if not isinstance(signatures, dict):
        signatures = {}
    for role in SIGNATURE_ROLES:
        current = signatures.get(role)
        if not isinstance(current, dict):
            current = {}
        signatures[role] = {**_empty_signature(), **current}
    visit["signatures"] = signatures
    return signatures


def init_storage():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PHOTOS_DIR, exist_ok=True)
    get_worker_photos_dir()
    get_signatures_dir()
    if not os.path.exists(CLIENTS_FILE):
        with open(CLIENTS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
    if not os.path.exists(VISITS_FILE):
        with open(VISITS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=4)

def load_clients() -> dict:
    init_storage()
    try:
        with open(CLIENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_clients(clients: dict):
    with open(CLIENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(clients, f, ensure_ascii=False, indent=4)

def load_visits() -> dict:
    init_storage()
    try:
        with open(VISITS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_visits(visits: dict):
    with open(VISITS_FILE, "w", encoding="utf-8") as f:
        json.dump(visits, f, ensure_ascii=False, indent=4)

def add_client(name: str, cnpj: str, address: str, responsible: str, phone: str, email: str):
    clients = load_clients()
    client_id = str(uuid.uuid4())[:8]
    client = {
        "id": client_id,
        "name": name.strip(),
        "cnpj": cnpj.strip(),
        "address": address.strip(),
        "responsible": responsible.strip(),
        "phone": phone.strip(),
        "email": email.strip(),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    client = _try_xano_sync_client(client)
    clients[client_id] = client
    save_clients(clients)
    return True, client_id, "Cliente cadastrado com sucesso."

def update_client(client_id: str, name: str, cnpj: str, address: str, responsible: str, phone: str, email: str):
    clients = load_clients()
    if client_id not in clients:
        return False, "Cliente não encontrado."
    clients[client_id].update({
        "name": name.strip(),
        "cnpj": cnpj.strip(),
        "address": address.strip(),
        "responsible": responsible.strip(),
        "phone": phone.strip(),
        "email": email.strip()
    })
    clients[client_id] = _try_xano_sync_client(clients[client_id])
    save_clients(clients)
    return True, "Cliente atualizado com sucesso."

def delete_client(client_id: str):
    clients = load_clients()
    if client_id not in clients:
        return False, "Cliente não encontrado."
    del clients[client_id]
    save_clients(clients)
    return True, "Cliente removido com sucesso."

def _default_caderno_avaliacao() -> dict:
    """Estrutura padrão do Caderno de Avaliação de Agentes Químicos."""
    return {
        # Bloco A — Identificação da empresa
        "empresa_avaliada": "",
        "unidade": "",
        "estado": "",
        # Bloco B — Agente químico e amostragem
        "agente_quimico": "",
        "data_amostragem": "",
        "identificacao_amostra": "",
        "hora_inicial": "",
        "hora_final": "",
        "vazao_l_min": "",
        "temperatura_amostragem": "",
        # Bloco C — Identificação do trabalhador
        "setor": "",
        "funcionario": "",
        "funcao": "",
        "matricula": "",
        # Bloco D — Atividades desenvolvidas
        "atividades_desenvolvidas": "",
        # Bloco E — Equipamentos de proteção
        "epi": "",
        "epc": "",
        # Bloco F — Observações
        "obs": "",
        # Bloco G — Responsáveis e avaliador
        "responsavel_funcionario": "",
        "nome_responsavel": "",
        "avaliador": "",
        "nome_avaliador": "",
    }


def get_caderno_avaliacao(visit: dict) -> dict:
    """Retorna o caderno de avaliação mesclado aos padrões (compatível com visitas antigas)."""
    if not isinstance(visit, dict):
        return _default_caderno_avaliacao()
    caderno = visit.get("caderno_avaliacao")
    if not isinstance(caderno, dict):
        caderno = {}
    merged = _default_caderno_avaliacao()
    merged.update(caderno)
    return merged


def add_visit(
    client_id: str,
    technician: str,
    date: str,
    status: str = "Rascunho",
    worker_name: str = "",
    date_start: str = "",
    date_end: str = "",
    horario: str = "",
):
    clients = load_clients()
    if client_id not in clients:
        return False, None, "Cliente não encontrado."

    visits = load_visits()
    visit_id = str(uuid.uuid4())[:8]
    client_name = clients[client_id]["name"]
    clean_worker = worker_name.strip()
    start = str(date_start or date or "").strip()
    end = str(date_end or start or "").strip()
    clean_horario = str(horario or "").strip()

    visit = {
        "id": visit_id,
        "client_id": client_id,
        "client_name": client_name,
        # Campo legado: mantém a data principal da visita.
        "date": start or str(date or ""),
        "date_start": start,
        "date_end": end,
        "horario": clean_horario,
        "technician": technician,
        "status": status,  # "Rascunho", "Em Andamento", "Finalizada"
        "worker": {
            "name": clean_worker,
            "photo_path": "",
            "photo_filename": "",
        },
        "worker_name": clean_worker,
        "worker_photo": "",
        "forms": {},
        "observations": "",
        "conclusions": "",
        "caderno_avaliacao": _default_caderno_avaliacao(),
        "weather": {
            # Temperatura externa (clima) capturada pela localização.
            "temperature_c": None,
            # Temperatura interna medida com termômetro na empresa (opcional).
            "internal_temperature_c": None,
            "humidity_pct": None,
            "description": "",
            "city": "",
            "latitude": None,
            "longitude": None,
            "source": "",
            "captured_at": "",
        },
        "signatures": {
            role: _empty_signature() for role in SIGNATURE_ROLES
        },
        "equipment": {
            "category": EQUIPMENT_CATEGORY,
            "selected": [],
        },
        "measurements": [],
        "photos": [],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    visit = _try_xano_sync_visit(visit)
    visits[visit_id] = visit
    save_visits(visits)
    return True, visit_id, "Visita iniciada com sucesso."

def update_visit(
    visit_id: str,
    forms: dict,
    observations: str,
    conclusions: str,
    status: str,
    worker: dict = None,
    *,
    client_id: str = None,
    technician: str = None,
    date: str = None,
    date_start: str = None,
    date_end: str = None,
    horario: str = None,
    caderno_avaliacao: dict = None,
):
    visits = load_visits()
    if visit_id not in visits:
        return False, "Visita não encontrada."

    visits[visit_id]["forms"] = forms
    visits[visit_id]["observations"] = observations
    visits[visit_id]["conclusions"] = conclusions
    visits[visit_id]["status"] = status
    if worker is not None:
        if not isinstance(visits[visit_id].get("worker"), dict):
            visits[visit_id]["worker"] = {}
        visits[visit_id]["worker"].update(worker)
        if "name" in worker:
            visits[visit_id]["worker_name"] = str(worker["name"]).strip()
        if "photo_path" in worker:
            visits[visit_id]["worker_photo"] = worker["photo_path"]

    if client_id is not None:
        clients = load_clients()
        client = clients.get(str(client_id))
        if client is None:
            return False, "Cliente não encontrado."
        visits[visit_id]["client_id"] = str(client_id)
        visits[visit_id]["client_name"] = client.get("name", "")

    if technician is not None:
        visits[visit_id]["technician"] = str(technician).strip()

    if date_start is not None or date is not None:
        start = str(date_start if date_start is not None else date or "").strip()
        if start:
            visits[visit_id]["date_start"] = start
            visits[visit_id]["date"] = start
    if date_end is not None:
        visits[visit_id]["date_end"] = str(date_end or "").strip()

    if horario is not None:
        visits[visit_id]["horario"] = str(horario or "").strip()

    if caderno_avaliacao is not None:
        current = visits[visit_id].get("caderno_avaliacao")
        if not isinstance(current, dict):
            current = _default_caderno_avaliacao()
        if isinstance(caderno_avaliacao, dict):
            current.update(caderno_avaliacao)
        visits[visit_id]["caderno_avaliacao"] = current

    visits[visit_id]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    visits[visit_id] = _try_xano_sync_visit(visits[visit_id], visits)
    save_visits(visits)
    return True, "Visita salva com sucesso."


def save_visit_weather(
    visit_id: str,
    temperature_c,
    humidity_pct=None,
    *,
    internal_temperature_c=None,
    description: str = "",
    city: str = "",
    latitude=None,
    longitude=None,
    source: str = "Manual",
    captured_at: str = None,
) -> tuple[bool, str]:
    """Salva a temperatura externa/interna, a umidade e a origem do dado."""
    visits = load_visits()
    if visit_id not in visits:
        return False, "Visita não encontrada."

    def _to_float(value, digits=1):
        if value is None or value == "":
            return None
        try:
            return round(float(value), digits)
        except (TypeError, ValueError):
            return None

    def _to_coord(value):
        if value is None or value == "":
            return None
        try:
            return round(float(value), 6)
        except (TypeError, ValueError):
            return None

    weather = visits[visit_id].get("weather")
    if not isinstance(weather, dict):
        weather = {}

    weather.update(
        {
            "temperature_c": _to_float(temperature_c),
            "internal_temperature_c": _to_float(internal_temperature_c),
            "humidity_pct": _to_float(humidity_pct),
            "description": str(description or "").strip(),
            "city": str(city or "").strip(),
            "latitude": _to_coord(latitude),
            "longitude": _to_coord(longitude),
            "source": str(source or "Manual").strip(),
            "captured_at": captured_at
            or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    visits[visit_id]["weather"] = weather
    visits[visit_id]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    visits[visit_id] = _try_xano_sync_visit(visits[visit_id])
    save_visits(visits)
    return True, "Temperatura e umidade salvas com sucesso."


# ---------------------------------------------------------------------------
# Equipamentos de Dosimetria de Ruído e medições vinculadas
# ---------------------------------------------------------------------------
def _measurement_for_equipment(item: dict, created_at: str = "") -> dict:
    """Cria o registro de medição correspondente a um equipamento."""
    code = str(item.get("codigo") or "").strip()
    identification = str(item.get("identificacao") or "")
    brand = str(item.get("marca") or "")
    label = f"{brand} {identification}".strip() or identification
    return {
        "id": f"meas_{code}" if code else "",
        "category": str(item.get("categoria") or EQUIPMENT_CATEGORY),
        "equipment_code": code,
        "equipment_brand": brand,
        "equipment_model": str(item.get("modelo") or ""),
        "equipment_identification": identification,
        "horario": str(item.get("horario") or ""),
        "identificacao_registro": str(item.get("identificacao_registro") or label),
        "created_at": created_at,
    }


def _normalise_identification(value) -> str:
    """Normaliza identificações antigas para comparação (ex.: 03440 -> 3440)."""
    text = str(value or "").strip().upper()
    if text.isdigit():
        return text.lstrip("0") or "0"
    return text


def _ensure_equipment(visit: dict) -> dict:
    equipment = visit.get("equipment")
    if not isinstance(equipment, dict):
        equipment = {}
    selected = equipment.get("selected")
    if not isinstance(selected, list):
        selected = []
    equipment["category"] = str(equipment.get("category") or EQUIPMENT_CATEGORY)
    equipment["selected"] = [
        dict(item) for item in selected if isinstance(item, dict)
    ]
    visit["equipment"] = equipment
    return equipment


def _ensure_measurements(visit: dict) -> list[dict]:
    measurements = visit.get("measurements")
    if not isinstance(measurements, list):
        measurements = []
    visit["measurements"] = [
        dict(item) for item in measurements if isinstance(item, dict)
    ]
    return visit["measurements"]


def get_visit_equipment(visit: dict) -> list[dict]:
    """Retorna os equipamentos selecionados na visita.

    O campo aditivo ``equipment.selected`` é a fonte de verdade. Visitas antigas
    que ainda usam ``devices`` são lidas como compatibilidade, sem alterar o
    registro até que o técnico salve uma nova seleção.
    """
    if not isinstance(visit, dict):
        return []

    equipment = visit.get("equipment")
    if isinstance(equipment, dict) and isinstance(equipment.get("selected"), list):
        return [
            dict(item)
            for item in equipment["selected"]
            if isinstance(item, dict)
        ]

    devices = visit.get("devices")
    if not isinstance(devices, list):
        return []

    by_code = equipment_by_code()
    by_identification = {
        _normalise_identification(item["identificacao"]): item
        for item in by_code.values()
    }
    result: list[dict] = []
    seen: set[str] = set()
    for device in devices:
        if not isinstance(device, dict):
            continue
        match = by_code.get(str(device.get("codigo") or ""))
        if match is None:
            for key in ("identificacao", "num_equipamento", "num_serie"):
                match = by_identification.get(
                    _normalise_identification(device.get(key))
                )
                if match:
                    break
        if match and match["codigo"] not in seen:
            result.append(dict(match))
            seen.add(match["codigo"])

    catalog_order = {code: index for index, code in enumerate(by_code)}
    result.sort(key=lambda item: catalog_order.get(item["codigo"], len(by_code)))
    return result


def get_visit_measurements(visit: dict) -> list[dict]:
    """Retorna as medições vinculadas aos equipamentos da visita."""
    if not isinstance(visit, dict):
        return []

    measurements = visit.get("measurements")
    if isinstance(measurements, list):
        return [dict(item) for item in measurements if isinstance(item, dict)]

    return [
        _measurement_for_equipment(item, str(item.get("created_at") or ""))
        for item in get_visit_equipment(visit)
    ]


def save_visit_equipment(visit_id: str, codes) -> tuple[bool, str]:
    """Salva a seleção de equipamentos e sincroniza as medições vinculadas.

    ``codes`` aceita uma lista de códigos internos ou de registros de
    equipamento. Códigos fora do catálogo são rejeitados para que nenhuma
    opção não fornecida pela equipe seja gravada.
    """
    visits = load_visits()
    if visit_id not in visits:
        return False, "Visita não encontrada."

    raw_codes = []
    for code in codes or []:
        if isinstance(code, dict):
            raw_codes.append(code.get("codigo"))
        else:
            raw_codes.append(code)

    try:
        selected_items = normalize_equipment_codes(raw_codes)
    except ValueError as exc:
        return False, str(exc)

    visit = visits[visit_id]
    equipment = _ensure_equipment(visit)
    measurements = _ensure_measurements(visit)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    existing = {
        str(measurement.get("equipment_code")): measurement
        for measurement in measurements
        if measurement.get("equipment_code")
    }

    selected_records = []
    synced_measurements = []
    for item in selected_items:
        code = item["codigo"]
        measurement = existing.get(code)
        if measurement is None:
            measurement = _measurement_for_equipment(item, now)
        else:
            measurement = dict(measurement)
            measurement.update(
                {
                    "category": item["categoria"],
                    "equipment_brand": item["marca"],
                    "equipment_model": item["modelo"],
                    "equipment_identification": item["identificacao"],
                }
            )
            measurement.setdefault(
                "identificacao_registro",
                _measurement_for_equipment(item).get("identificacao_registro", ""),
            )
        measurement.setdefault("id", f"meas_{code}")
        measurement.setdefault("created_at", now)
        measurement.setdefault("horario", "")
        synced_measurements.append(measurement)
        selected_records.append(
            {
                **item,
                "horario": str(measurement.get("horario") or ""),
                "identificacao_registro": str(
                    measurement.get("identificacao_registro") or ""
                ),
                "measurement_id": measurement["id"],
            }
        )

    equipment["category"] = EQUIPMENT_CATEGORY
    equipment["selected"] = selected_records
    visit["equipment"] = equipment
    visit["measurements"] = synced_measurements
    visit["updated_at"] = now
    save_visits(visits)
    return True, "Equipamentos da visita atualizados com sucesso."


def visit_equipment_labels(visit: dict) -> list[str]:
    """Rótulos dos equipamentos selecionados, na ordem do catálogo."""
    return [equipment_label(item) for item in get_visit_equipment(visit)]


def visit_measurement_labels(visit: dict) -> list[str]:
    """Identificadores legíveis das medições vinculadas."""
    labels = []
    for measurement in get_visit_measurements(visit):
        label = str(
            measurement.get("identificacao_registro")
            or measurement.get("id")
            or ""
        ).strip()
        if label:
            labels.append(label)
    return labels


def update_visit_measurement(visit_id: str, equipment_code: str, **fields) -> tuple[bool, str]:
    """Atualiza campos de uma medição vinculada a um equipamento."""
    visits = load_visits()
    if visit_id not in visits:
        return False, "Visita não encontrada."

    visit = visits[visit_id]
    equipment = _ensure_equipment(visit)
    measurements = _ensure_measurements(visit)
    found = False
    for measurement in measurements:
        if str(measurement.get("equipment_code")) != str(equipment_code):
            continue
        found = True
        for key, value in fields.items():
            if value is None:
                continue
            measurement[key] = value
        horario = str(measurement.get("horario") or "").strip()
        brand = str(measurement.get("equipment_brand") or "").strip()
        ident = str(measurement.get("equipment_identification") or "").strip()
        base = f"{brand} {ident}".strip() or ident
        if horario:
            measurement["identificacao_registro"] = f"{horario} — {base}"
        else:
            measurement["identificacao_registro"] = base
        break

    if not found:
        return False, "Medição não encontrada para o equipamento informado."

    # Sincroniza horário/identificação nos itens selecionados.
    by_code = {
        str(measurement.get("equipment_code")): measurement
        for measurement in measurements
    }
    selected = []
    for item in equipment.get("selected", []):
        code = str(item.get("codigo") or "")
        measurement = by_code.get(code)
        if measurement:
            item = dict(item)
            item["horario"] = measurement.get("horario", "")
            item["identificacao_registro"] = measurement.get(
                "identificacao_registro", ""
            )
        selected.append(item)
    equipment["selected"] = selected
    visit["measurements"] = measurements
    visit["equipment"] = equipment
    visit["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_visits(visits)
    return True, "Medição atualizada com sucesso."


def missing_equipment(visit: dict) -> list[str]:
    """Lista pendências de equipamentos obrigatórios para finalizar."""
    if get_visit_equipment(visit):
        return []
    return ["Pelo menos um equipamento de Dosimetria de Ruído"]


def _decode_png_data_url(data_url: str) -> bytes:
    """Decodifica um data URL PNG e valida o tamanho máximo aceito."""
    prefix = "data:image/png;base64,"
    if not isinstance(data_url, str) or not data_url.startswith(prefix):
        raise ValueError("Formato de assinatura inválido.")
    encoded = data_url[len(prefix):]
    if not encoded:
        raise ValueError("Assinatura vazia.")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise ValueError("Não foi possível decodificar a assinatura.") from exc
    if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("O arquivo da assinatura não é um PNG válido.")
    if len(raw) > SIGNATURE_MAX_BYTES:
        raise ValueError("A assinatura excede o tamanho máximo permitido.")
    return raw


def save_visit_signature(
    visit_id: str,
    role: str,
    *,
    data_url: str = None,
    name: str = None,
) -> tuple[bool, str]:
    """Salva o nome e/ou a imagem da assinatura vinculada à visita.

    ``data_url`` vazio remove a assinatura (usado pelo botão "Limpar").
    ``name`` pode ser atualizado separadamente, preservando a imagem.
    """
    if role not in SIGNATURE_ROLES:
        return False, "Tipo de assinatura inválido."

    visits = load_visits()
    if visit_id not in visits:
        return False, "Visita não encontrada."

    visit = visits[visit_id]
    signatures = _ensure_signatures(visit)
    signature = signatures[role]
    changed = False

    if name is not None:
        clean_name = str(name).strip()
        if signature.get("name") != clean_name:
            signature["name"] = clean_name
            changed = True

    if data_url is not None:
        old_path = signature.get("path")
        if not data_url:
            preserved_name = (
                str(name).strip()
                if name is not None
                else str(signature.get("name") or "").strip()
            )
            signature.update(_empty_signature())
            signature["name"] = preserved_name
            if old_path and os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except Exception:
                    pass
            changed = True
        else:
            try:
                raw = _decode_png_data_url(data_url)
            except ValueError as exc:
                return False, str(exc)

            signatures_dir = get_signatures_dir()
            filename = f"{visit_id}_{role}.png"
            saved_path = os.path.join(signatures_dir, filename)
            try:
                with open(saved_path, "wb") as file:
                    file.write(raw)
            except Exception as exc:
                return False, f"Erro ao salvar assinatura: {exc}"

            signature.update(
                {
                    "path": saved_path,
                    "filename": filename,
                    "signed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
            changed = True

    if changed:
        visit["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_visits(visits)
    return True, "Assinatura salva com sucesso."


def remove_visit_signature(visit_id: str, role: str) -> tuple[bool, str]:
    """Remove a imagem da assinatura, mantendo o nome informado."""
    if role not in SIGNATURE_ROLES:
        return False, "Tipo de assinatura inválido."

    visits = load_visits()
    if visit_id not in visits:
        return False, "Visita não encontrada."

    signatures = _ensure_signatures(visits[visit_id])
    signature = signatures[role]
    old_path = signature.get("path")
    preserved_name = str(signature.get("name") or "").strip()
    signature.update(_empty_signature())
    signature["name"] = preserved_name
    if old_path and os.path.exists(old_path):
        try:
            os.remove(old_path)
        except Exception:
            pass
    visits[visit_id]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    visits[visit_id] = _try_xano_sync_visit(visits[visit_id])
    save_visits(visits)
    return True, "Assinatura removida com sucesso."


def visit_has_signature(visit: dict, role: str) -> bool:
    """Informa se a assinatura tem nome e arquivo de imagem existente."""
    signatures = visit.get("signatures") if isinstance(visit, dict) else None
    if not isinstance(signatures, dict):
        return False
    signature = signatures.get(role)
    if not isinstance(signature, dict):
        return False
    name = str(signature.get("name") or "").strip()
    path = signature.get("path")
    return bool(name and path and os.path.exists(path))


def missing_signatures(visit: dict) -> list[str]:
    """Lista os rótulos das assinaturas obrigatórias ainda pendentes."""
    return [
        SIGNATURE_LABELS[role]
        for role in SIGNATURE_ROLES
        if not visit_has_signature(visit, role)
    ]


def _prepare_photo_bytes(
    file_bytes: bytes,
    filename: str,
    *,
    validate_photo: bool = False,
) -> tuple[bytes, str]:
    """Normaliza uma foto para JPEG e corrige a orientação EXIF.

    A validação estrita é usada pelos campos novos de captura. Sem ela, o
    comportamento legado é preservado para chamadas antigas que gravam bytes
    arbitrários (importações e testes históricos).
    """
    try:
        from src.components.photo_capture.photo_capture import (
            PhotoValidationError,
            normalize_photo_bytes,
        )
    except Exception as exc:
        if validate_photo:
            raise ValueError(
                "Não foi possível carregar o validador de imagens."
            ) from exc
        return file_bytes, filename

    try:
        normalized = normalize_photo_bytes(file_bytes)
    except PhotoValidationError as exc:
        if validate_photo:
            raise ValueError(str(exc)) from exc
        return file_bytes, filename
    except Exception as exc:
        if validate_photo:
            raise ValueError(
                "Não foi possível validar a imagem enviada. Tente novamente."
            ) from exc
        return file_bytes, filename

    base = os.path.splitext(str(filename or "foto"))[0].strip() or "foto"
    return normalized, f"{base}.jpg"


def save_worker_photo(
    visit_id: str,
    file_bytes: bytes,
    filename: str,
    *,
    validate_photo: bool = False,
) -> tuple[bool, str, str]:
    """Salva ou substitui a fotografia do funcionário associada à visita.

    Quando ``validate_photo`` é verdadeiro, a imagem precisa ser JPG, PNG ou
    WEBP válida, com até 10 MB, e é convertida para JPEG antes da gravação.
    """
    visits = load_visits()
    if visit_id not in visits:
        return False, "", "Visita não encontrada."

    try:
        file_bytes, filename = _prepare_photo_bytes(
            file_bytes, filename, validate_photo=validate_photo
        )
    except ValueError as exc:
        return False, "", str(exc)

    workers_dir = get_worker_photos_dir()
    ext = os.path.splitext(filename)[1].lower() or ".jpg"
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        ext = ".jpg"

    saved_filename = f"worker_{visit_id}_{str(uuid.uuid4())[:8]}{ext}"
    saved_path = os.path.join(workers_dir, saved_filename)

    worker_data = visits[visit_id].get("worker")
    old_path = worker_data.get("photo_path") if isinstance(worker_data, dict) else None
    if not old_path and visits[visit_id].get("worker_photo"):
        old_path = visits[visit_id].get("worker_photo")

    try:
        with open(saved_path, "wb") as f:
            f.write(file_bytes)
    except Exception as e:
        return False, "", f"Erro ao salvar fotografia: {e}"

    if old_path and os.path.exists(old_path) and old_path != saved_path:
        try:
            os.remove(old_path)
        except Exception:
            pass

    if not isinstance(visits[visit_id].get("worker"), dict):
        visits[visit_id]["worker"] = {}

    visits[visit_id]["worker"]["photo_path"] = saved_path
    visits[visit_id]["worker"]["photo_filename"] = saved_filename
    visits[visit_id]["worker_photo"] = saved_path
    visits[visit_id]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    visits[visit_id] = _try_xano_sync_visit(visits[visit_id])
    save_visits(visits)
    return True, saved_path, "Foto do funcionário salva com sucesso."


def remove_worker_photo(visit_id: str) -> tuple[bool, str]:
    """Remove a fotografia do funcionário da visita e do disco."""
    visits = load_visits()
    if visit_id not in visits:
        return False, "Visita não encontrada."

    worker_data = visits[visit_id].get("worker")
    old_path = worker_data.get("photo_path") if isinstance(worker_data, dict) else None
    if not old_path and visits[visit_id].get("worker_photo"):
        old_path = visits[visit_id].get("worker_photo")

    if old_path and os.path.exists(old_path):
        try:
            os.remove(old_path)
        except Exception:
            pass

    if isinstance(visits[visit_id].get("worker"), dict):
        visits[visit_id]["worker"]["photo_path"] = ""
        visits[visit_id]["worker"]["photo_filename"] = ""
    visits[visit_id]["worker_photo"] = ""
    visits[visit_id]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    visits[visit_id] = _try_xano_sync_visit(visits[visit_id])
    save_visits(visits)
    return True, "Foto do funcionário removida com sucesso."


def update_worker_info(visit_id: str, name: str) -> tuple[bool, str]:
    """Atualiza a identificação do funcionário responsável na visita."""
    visits = load_visits()
    if visit_id not in visits:
        return False, "Visita não encontrada."

    if not isinstance(visits[visit_id].get("worker"), dict):
        visits[visit_id]["worker"] = {}

    clean_name = name.strip()
    visits[visit_id]["worker"]["name"] = clean_name
    visits[visit_id]["worker_name"] = clean_name
    visits[visit_id]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    visits[visit_id] = _try_xano_sync_visit(visits[visit_id])
    save_visits(visits)
    return True, "Identificação do funcionário atualizada com sucesso."

def _photo_registro(horario: str, equipment_label: str, identificacao_registro: str = "") -> str:
    horario = str(horario or "").strip()
    equipment_label = str(equipment_label or "").strip()
    if horario and equipment_label:
        return f"{horario} — {equipment_label}"
    if horario and identificacao_registro:
        # tenta preservar identificação existente se já vier no padrão
        return str(identificacao_registro).strip() or horario
    if equipment_label:
        return equipment_label
    return str(identificacao_registro or "").strip()


def add_photo_to_visit(
    visit_id: str,
    file_bytes: bytes,
    filename: str,
    description: str,
    *,
    equipment_code: str = "",
    identificacao_registro: str = "",
    horario: str = "",
    equipment_label: str = "",
    observations: str = "",
    validate_photo: bool = False,
):
    visits = load_visits()
    if visit_id not in visits:
        return False, "Visita não encontrada."

    try:
        file_bytes, filename = _prepare_photo_bytes(
            file_bytes, filename, validate_photo=validate_photo
        )
    except ValueError as exc:
        return False, str(exc)

    photo_id = str(uuid.uuid4())[:8]
    ext = os.path.splitext(filename)[1] or ".jpg"
    saved_filename = f"{visit_id}_{photo_id}{ext}"
    saved_path = os.path.join(PHOTOS_DIR, saved_filename)

    with open(saved_path, "wb") as f:
        f.write(file_bytes)

    registro = _photo_registro(horario, equipment_label, identificacao_registro)
    photo_record = {
        "id": photo_id,
        "filename": filename,
        "path": saved_path,
        "saved_filename": saved_filename,
        "description": str(description or "").strip(),
        "observations": str(observations or "").strip(),
        "horario": str(horario or "").strip(),
        "equipment_code": str(equipment_code or ""),
        "equipment_label": str(equipment_label or "").strip(),
        "identificacao_registro": registro,
        "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    visits[visit_id].setdefault("photos", []).append(photo_record)
    visits[visit_id]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    visits[visit_id] = _try_xano_sync_visit(visits[visit_id])
    save_visits(visits)
    return True, "Fotografia anexada com sucesso."

def replace_photo_in_visit(
    visit_id: str,
    photo_id: str,
    file_bytes: bytes,
    filename: str,
    description: str,
    *,
    equipment_code: str = None,
    identificacao_registro: str = None,
    horario: str = None,
    equipment_label: str = None,
    observations: str = None,
    validate_photo: bool = False,
):
    """Substitui uma fotografia existente, mantendo o histórico da visita."""
    visits = load_visits()
    if visit_id not in visits:
        return False, "Visita não encontrada."

    photos = visits[visit_id].get("photos", [])
    target = next((p for p in photos if p["id"] == photo_id), None)
    if target is None:
        return False, "Fotografia não encontrada."

    try:
        file_bytes, filename = _prepare_photo_bytes(
            file_bytes, filename, validate_photo=validate_photo
        )
    except ValueError as exc:
        return False, str(exc)

    new_photo_id = str(uuid.uuid4())[:8]
    ext = os.path.splitext(filename)[1] or ".jpg"
    saved_filename = f"{visit_id}_{new_photo_id}{ext}"
    saved_path = os.path.join(PHOTOS_DIR, saved_filename)

    with open(saved_path, "wb") as f:
        f.write(file_bytes)

    old_path = target.get("path")
    target.update(
        {
            "id": new_photo_id,
            "filename": filename,
            "path": saved_path,
            "saved_filename": saved_filename,
            "description": str(description or "").strip(),
            "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    if observations is not None:
        target["observations"] = str(observations or "").strip()
    if equipment_code is not None:
        target["equipment_code"] = str(equipment_code or "")
    if horario is not None:
        target["horario"] = str(horario or "").strip()
    if equipment_label is not None:
        target["equipment_label"] = str(equipment_label or "").strip()
    if identificacao_registro is not None or horario is not None or equipment_label is not None:
        target["identificacao_registro"] = _photo_registro(
            target.get("horario", ""),
            target.get("equipment_label", ""),
            identificacao_registro if identificacao_registro is not None else target.get("identificacao_registro", ""),
        )

    visits[visit_id]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    visits[visit_id] = _try_xano_sync_visit(visits[visit_id])
    save_visits(visits)

    if old_path and os.path.exists(old_path):
        try:
            os.remove(old_path)
        except Exception:
            pass

    return True, "Fotografia substituída com sucesso."


def update_photo_in_visit(
    visit_id: str,
    photo_id: str,
    *,
    description: str = None,
    observations: str = None,
    horario: str = None,
    equipment_code: str = None,
    equipment_label: str = None,
    identificacao_registro: str = None,
):
    """Atualiza legenda, observações e identificação de uma fotografia."""
    visits = load_visits()
    if visit_id not in visits:
        return False, "Visita não encontrada."

    photos = visits[visit_id].get("photos", [])
    target = next((p for p in photos if p["id"] == photo_id), None)
    if target is None:
        return False, "Fotografia não encontrada."

    if description is not None:
        target["description"] = str(description or "").strip()
    if observations is not None:
        target["observations"] = str(observations or "").strip()
    if equipment_code is not None:
        target["equipment_code"] = str(equipment_code or "")
    if horario is not None:
        target["horario"] = str(horario or "").strip()
    if equipment_label is not None:
        target["equipment_label"] = str(equipment_label or "").strip()
    if (
        identificacao_registro is not None
        or horario is not None
        or equipment_label is not None
    ):
        target["identificacao_registro"] = _photo_registro(
            target.get("horario", ""),
            target.get("equipment_label", ""),
            identificacao_registro if identificacao_registro is not None else target.get("identificacao_registro", ""),
        )

    visits[visit_id]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    visits[visit_id] = _try_xano_sync_visit(visits[visit_id])
    save_visits(visits)
    return True, "Fotografia atualizada com sucesso."


def remove_photo_from_visit(visit_id: str, photo_id: str):
    visits = load_visits()
    if visit_id not in visits:
        return False, "Visita não encontrada."

    photos = visits[visit_id].get("photos", [])
    updated_photos = []
    for p in photos:
        if p["id"] == photo_id:
            try:
                if os.path.exists(p.get("path", "")):
                    os.remove(p["path"])
            except Exception:
                pass
        else:
            updated_photos.append(p)

    visits[visit_id]["photos"] = updated_photos
    visits[visit_id]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    visits[visit_id] = _try_xano_sync_visit(visits[visit_id])
    save_visits(visits)
    return True, "Fotografia removida com sucesso."
