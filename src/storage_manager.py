import os
import json
import uuid
from datetime import datetime

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
CLIENTS_FILE = os.path.join(DATA_DIR, "clients.json")
VISITS_FILE = os.path.join(DATA_DIR, "visits.json")
PHOTOS_DIR = os.path.join(DATA_DIR, "photos")
WORKER_PHOTOS_DIR = os.path.join(PHOTOS_DIR, "workers")

# A tabela lógica ``inspections`` é persistida em ``visits.json`` para manter
# compatibilidade com o histórico, o painel e os relatórios já existentes.
INSPECTIONS_FILE = VISITS_FILE


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def init_storage():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PHOTOS_DIR, exist_ok=True)
    os.makedirs(WORKER_PHOTOS_DIR, exist_ok=True)
    if not os.path.exists(CLIENTS_FILE):
        with open(CLIENTS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
    if not os.path.exists(VISITS_FILE):
        with open(VISITS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
    try:
        from src.equipment_catalog import load_equipments

        load_equipments()
    except Exception:
        # O catálogo é opcional para a inicialização do armazenamento.
        pass

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
    clients[client_id] = {
        "id": client_id,
        "name": name.strip(),
        "cnpj": cnpj.strip(),
        "address": address.strip(),
        "responsible": responsible.strip(),
        "phone": phone.strip(),
        "email": email.strip(),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
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
    save_clients(clients)
    return True, "Cliente atualizado com sucesso."

def delete_client(client_id: str):
    clients = load_clients()
    if client_id not in clients:
        return False, "Cliente não encontrado."
    del clients[client_id]
    save_clients(clients)
    return True, "Cliente removido com sucesso."

def add_visit(client_id: str, technician: str, date: str, status: str = "Rascunho"):
    clients = load_clients()
    if client_id not in clients:
        return False, None, "Cliente não encontrado."
    
    visits = load_visits()
    visit_id = str(uuid.uuid4())[:8]
    client_name = clients[client_id]["name"]
    
    visits[visit_id] = {
        "id": visit_id,
        "client_id": client_id,
        "client_name": client_name,
        "date": date,
        "technician": technician,
        "status": status, # "Rascunho", "Em Andamento", "Finalizada"
        "forms": {},
        "observations": "",
        "conclusions": "",
        "photos": [],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_visits(visits)
    return True, visit_id, "Visita iniciada com sucesso."

def update_visit(visit_id: str, forms: dict, observations: str, conclusions: str, status: str):
    visits = load_visits()
    if visit_id not in visits:
        return False, "Visita não encontrada."
    
    visits[visit_id]["forms"] = forms
    visits[visit_id]["observations"] = observations
    visits[visit_id]["conclusions"] = conclusions
    visits[visit_id]["status"] = status
    visits[visit_id]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_visits(visits)
    return True, "Visita salva com sucesso."

def _unique_path(directory: str, filename: str) -> tuple[str, str]:
    """Evita sobrescrever arquivos quando o nome padrão já existe."""
    safe_name = os.path.basename(str(filename or "foto.jpg"))
    root, ext = os.path.splitext(safe_name)
    candidate = safe_name
    counter = 2
    while os.path.exists(os.path.join(directory, candidate)):
        candidate = f"{root}_{counter}{ext}"
        counter += 1
    return candidate, os.path.join(directory, candidate)


def add_photo_to_visit(
    visit_id: str,
    file_bytes: bytes,
    filename: str,
    description: str,
    *,
    nome_arquivo: str | None = None,
    horario_registro: str | None = None,
    equipamento_id: str | None = None,
    reconhecimento_epi: dict | None = None,
):
    visits = load_visits()
    if visit_id not in visits:
        return False, "Visita não encontrada."

    photo_id = str(uuid.uuid4())[:8]
    ext = os.path.splitext(filename)[1] or ".jpg"
    if nome_arquivo:
        requested = os.path.basename(nome_arquivo)
        if not os.path.splitext(requested)[1]:
            requested += ext
        saved_filename, saved_path = _unique_path(PHOTOS_DIR, requested)
    else:
        saved_filename = f"{visit_id}_{photo_id}{ext}"
        saved_path = os.path.join(PHOTOS_DIR, saved_filename)

    with open(saved_path, "wb") as f:
        f.write(file_bytes)

    photo_record = {
        "id": photo_id,
        "filename": filename,
        "path": saved_path,
        "saved_filename": saved_filename,
        "nome_arquivo": saved_filename,
        "description": description,
        "horario_registro": horario_registro or datetime.now().strftime("%H:%M:%S"),
        "equipamento_id": equipamento_id,
        "reconhecimento_epi": reconhecimento_epi or {},
        "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    visits[visit_id].setdefault("photos", []).append(photo_record)
    visits[visit_id]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_visits(visits)
    return True, "Fotografia anexada com sucesso."

def replace_photo_in_visit(visit_id: str, photo_id: str, file_bytes: bytes, filename: str, description: str):
    """Substitui uma fotografia existente, mantendo o histórico da visita."""
    visits = load_visits()
    if visit_id not in visits:
        return False, "Visita não encontrada."

    photos = visits[visit_id].get("photos", [])
    target = next((p for p in photos if p["id"] == photo_id), None)
    if target is None:
        return False, "Fotografia não encontrada."

    new_photo_id = str(uuid.uuid4())[:8]
    ext = os.path.splitext(filename)[1] or ".jpg"
    desired_name = target.get("nome_arquivo") or target.get("saved_filename")
    if desired_name:
        saved_filename, saved_path = _unique_path(PHOTOS_DIR, desired_name)
    else:
        saved_filename = f"{visit_id}_{new_photo_id}{ext}"
        saved_path = os.path.join(PHOTOS_DIR, saved_filename)

    with open(saved_path, "wb") as f:
        f.write(file_bytes)

    old_path = target.get("path")
    target.update({
        "id": new_photo_id,
        "filename": filename,
        "path": saved_path,
        "saved_filename": saved_filename,
        "nome_arquivo": saved_filename,
        "description": description,
        "horario_registro": target.get("horario_registro")
        or datetime.now().strftime("%H:%M:%S"),
        "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    visits[visit_id]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_visits(visits)

    if old_path and os.path.exists(old_path):
        try:
            os.remove(old_path)
        except Exception:
            pass

    return True, "Fotografia substituída com sucesso."


def remove_photo_from_visit(visit_id: str, photo_id: str):
    visits = load_visits()
    if visit_id not in visits:
        return False, "Visita não encontrada."
    
    photos = visits[visit_id].get("photos", [])
    updated_photos = []
    for p in photos:
        if p["id"] == photo_id:
            try:
                if os.path.exists(p["path"]):
                    os.remove(p["path"])
            except Exception:
                pass
        else:
            updated_photos.append(p)
            
    visits[visit_id]["photos"] = updated_photos
    visits[visit_id]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_visits(visits)
    return True, "Fotografia removida com sucesso."


# ---------------------------------------------------------------------------
# Tabela lógica ``inspections`` (formulário de campo)
# ---------------------------------------------------------------------------
def create_inspection(
    empresa_nome: str = "",
    data_avaliacao: str = "",
    data_avaliacao_fim: str = "",
    technician: str = "",
):
    """Cria uma avaliação de campo em rascunho.

    A estrutura fica em ``visits.json`` (tabela ``inspections``) e mantém os
    campos usados pelo painel, pelos relatórios e pela galeria.
    """
    visits = load_visits()
    inspection_id = str(uuid.uuid4())[:8]
    empresa = (empresa_nome or "").strip()
    visits[inspection_id] = {
        "id": inspection_id,
        "kind": "inspection",
        "client_id": None,
        "client_name": empresa,
        "empresa_nome": empresa,
        "data_avaliacao": data_avaliacao or "",
        "data_avaliacao_fim": data_avaliacao_fim or data_avaliacao or "",
        "date": data_avaliacao or "",
        "technician": (technician or "").strip(),
        "status": "Rascunho",
        "temperatura_capturada": None,
        "umidade_capturada": None,
        "clima": {},
        "worker": {
            "funcionario_nome": "",
            "funcionario_foto_url": "",
            "funcao": "",
            "setor": "",
        },
        "devices": [],
        "forms": {},
        "observations": "",
        "conclusions": "",
        "photos": [],
        "signatures": {
            "ass_responsavel_tecnico": "",
            "ass_avaliador": "",
        },
        "created_at": _now_text(),
        "updated_at": _now_text(),
    }
    save_visits(visits)
    return True, inspection_id, "Avaliação iniciada com sucesso."


def update_inspection(inspection_id: str, **fields):
    """Atualiza campos pontuais da avaliação sem sobrescrever o formulário."""
    visits = load_visits()
    inspection = visits.get(inspection_id)
    if inspection is None:
        return False, "Avaliação não encontrada."

    allowed = {
        "empresa_nome",
        "client_name",
        "data_avaliacao",
        "data_avaliacao_fim",
        "date",
        "technician",
        "status",
        "temperatura_capturada",
        "umidade_capturada",
        "clima",
        "worker",
        "devices",
        "forms",
        "observations",
        "conclusions",
        "signatures",
    }
    for key, value in fields.items():
        if key in allowed:
            inspection[key] = value

    if "empresa_nome" in fields:
        inspection["client_name"] = fields.get("empresa_nome", "")
    if "client_name" in fields and "empresa_nome" not in fields:
        inspection["empresa_nome"] = fields.get("client_name", "")
    if "data_avaliacao" in fields:
        inspection["date"] = fields.get("data_avaliacao", "")

    inspection["updated_at"] = _now_text()
    save_visits(visits)
    return True, "Avaliação atualizada com sucesso."


def save_inspection_worker(
    inspection_id: str,
    funcionario_nome: str,
    funcao: str = "",
    setor: str = "",
    photo_bytes: bytes | None = None,
    photo_filename: str | None = None,
):
    """Grava a identificação do funcionário e, opcionalmente, a foto do rosto."""
    visits = load_visits()
    inspection = visits.get(inspection_id)
    if inspection is None:
        return False, "Avaliação não encontrada.", ""

    worker = dict(inspection.get("worker") or {})
    photo_url = worker.get("funcionario_foto_url", "")
    old_photo = photo_url

    if photo_bytes:
        ext = os.path.splitext(photo_filename or "")[1] or ".jpg"
        filename, path = _unique_path(
            WORKER_PHOTOS_DIR, f"funcionario_{inspection_id}{ext}"
        )
        with open(path, "wb") as file:
            file.write(photo_bytes)
        photo_url = path
        if old_photo and os.path.exists(old_photo) and old_photo != photo_url:
            try:
                os.remove(old_photo)
            except OSError:
                pass

    worker.update(
        {
            "funcionario_nome": (funcionario_nome or "").strip(),
            "funcionario_foto_url": photo_url,
            "funcao": (funcao or "").strip(),
            "setor": (setor or "").strip(),
        }
    )
    inspection["worker"] = worker
    inspection["updated_at"] = _now_text()
    save_visits(visits)
    return True, "Funcionário identificado com sucesso.", photo_url


def set_inspection_devices(inspection_id: str, devices: list[dict]):
    visits = load_visits()
    inspection = visits.get(inspection_id)
    if inspection is None:
        return False, "Avaliação não encontrada."
    inspection["devices"] = [dict(device) for device in (devices or [])]
    inspection["updated_at"] = _now_text()
    save_visits(visits)
    return True, "Equipamentos atualizados com sucesso."


def save_inspection_signatures(
    inspection_id: str,
    ass_responsavel_tecnico: str = "",
    ass_avaliador: str = "",
):
    visits = load_visits()
    inspection = visits.get(inspection_id)
    if inspection is None:
        return False, "Avaliação não encontrada."
    inspection["signatures"] = {
        "ass_responsavel_tecnico": ass_responsavel_tecnico or "",
        "ass_avaliador": ass_avaliador or "",
    }
    inspection["updated_at"] = _now_text()
    save_visits(visits)
    return True, "Assinaturas salvas com sucesso."


def save_inspection_weather(
    inspection_id: str,
    temperatura: float,
    umidade: float,
    clima: dict | None = None,
):
    return update_inspection(
        inspection_id,
        temperatura_capturada=temperatura,
        umidade_capturada=umidade,
        clima=clima or {},
    )


def load_inspections() -> dict:
    """Alias semântico para a tabela lógica ``inspections``."""
    return load_visits()


def save_inspections(inspections: dict) -> None:
    save_visits(inspections)


def add_inspection(*args, **kwargs):
    return create_inspection(*args, **kwargs)


def get_inspection(inspection_id: str) -> dict | None:
    return load_visits().get(inspection_id)
