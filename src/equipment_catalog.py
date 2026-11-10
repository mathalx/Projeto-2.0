"""Catálogo oficial de equipamentos da ACN Norte.

O catálogo é a fonte única para:
- seleção rápida no formulário de campo;
- exibição da data da última calibração;
- geração do nome padrão dos arquivos de fotografia;
- tabela detalhada do laudo em PDF.

Os dados podem ser complementados em ``data/equipments.json`` (datas de
calibração, observações e novos equipamentos) sem alterar o código.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from datetime import date, datetime, time
from typing import Iterable

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
EQUIPMENTS_FILE = os.path.join(DATA_DIR, "equipments.json")

EQUIPMENT_CATEGORIES = [
    "Audiodosímetros",
    "Bombas de Amostragem",
    "Medidores/Monitores de Vibração",
    "Monitores IBUTG & Outros",
]

# Dados oficiais informados pela ACN Norte. A data de calibração não é
# inventada: quando ausente, o formulário exibe "Não informada" e permite que
# seja registrada no cadastro local do equipamento.
DEFAULT_EQUIPMENTS = [
    # Audiodosímetros -----------------------------------------------------
    {
        "codigo": "CHR-SMARTDB-03440",
        "categoria": "Audiodosímetros",
        "tipo": "Audiodosímetro",
        "marca": "Chrompack",
        "modelo": "SmartdB",
        "num_serie": "03440",
        "num_equipamento": "03440",
        "identificacao": "03440",
        "data_ultima_calibracao": "",
    },
    {
        "codigo": "CHR-SMARTDB-03558",
        "categoria": "Audiodosímetros",
        "tipo": "Audiodosímetro",
        "marca": "Chrompack",
        "modelo": "SmartdB",
        "num_serie": "03558",
        "num_equipamento": "03558",
        "identificacao": "03558",
        "data_ultima_calibracao": "",
    },
    {
        "codigo": "CHR-SMARTDB-03611",
        "categoria": "Audiodosímetros",
        "tipo": "Audiodosímetro",
        "marca": "Chrompack",
        "modelo": "SmartdB",
        "num_serie": "03611",
        "num_equipamento": "03611",
        "identificacao": "03611",
        "data_ultima_calibracao": "",
    },
    {
        "codigo": "CHR-SMARTDB-05981",
        "categoria": "Audiodosímetros",
        "tipo": "Audiodosímetro",
        "marca": "Chrompack",
        "modelo": "SmartdB",
        "num_serie": "05981",
        "num_equipamento": "05981",
        "identificacao": "05981",
        "data_ultima_calibracao": "",
    },
    {
        "codigo": "CHR-SMARTDB-02319",
        "categoria": "Audiodosímetros",
        "tipo": "Audiodosímetro",
        "marca": "Chrompack",
        "modelo": "SmartdB",
        "num_serie": "02319",
        "num_equipamento": "02319",
        "identificacao": "02319",
        "data_ultima_calibracao": "",
    },
    {
        "codigo": "CHR-SMARTDB-02386",
        "categoria": "Audiodosímetros",
        "tipo": "Audiodosímetro",
        "marca": "Chrompack",
        "modelo": "SmartdB",
        "num_serie": "02386",
        "num_equipamento": "02386",
        "identificacao": "02386",
        "data_ultima_calibracao": "",
    },
    {
        "codigo": "INS-DOS1000X-04_02385",
        "categoria": "Audiodosímetros",
        "tipo": "Audiodosímetro",
        "marca": "Instrutherm",
        "modelo": "DOS-1000X",
        "num_serie": "04_02385",
        "num_equipamento": "04_02385",
        "identificacao": "DOS1000_04_02385",
        "data_ultima_calibracao": "",
    },
    # Bombas de amostragem ------------------------------------------------
    {
        "codigo": "CRI-ACCURA3-22000098",
        "categoria": "Bombas de Amostragem",
        "tipo": "Bomba de Amostragem",
        "marca": "Criffer",
        "modelo": "Accura 3",
        "num_serie": "22000098",
        "num_equipamento": "22000098",
        "identificacao": "22000098",
        "data_ultima_calibracao": "",
    },
    {
        "codigo": "GIL-BDXII-20170104107",
        "categoria": "Bombas de Amostragem",
        "tipo": "Bomba de Amostragem",
        "marca": "Gilian",
        "modelo": "BDXII",
        "num_serie": "20170104107",
        "num_equipamento": "20170104107",
        "identificacao": "20170104107",
        "data_ultima_calibracao": "",
    },
    {
        "codigo": "INL-VENTUSPRO",
        "categoria": "Bombas de Amostragem",
        "tipo": "Bomba de Amostragem",
        "marca": "Inlite",
        "modelo": "Ventuspro",
        "num_serie": "VENTUSPRO",
        "num_equipamento": "VENTUSPRO",
        "identificacao": "VENTUSPRO",
        "data_ultima_calibracao": "",
    },
    # Vibração ------------------------------------------------------------
    {
        "codigo": "CHR-SMARTVIB-RBC5_12181_610",
        "categoria": "Medidores/Monitores de Vibração",
        "tipo": "Medidor de Vibração",
        "marca": "Chrompack",
        "modelo": "SmartVib",
        "num_serie": "RBC5-12181-610",
        "num_equipamento": "RBC5-12181-610",
        "identificacao": "RBC5_12181_610",
        "certificado": "RBC5-12181-610",
        "data_ultima_calibracao": "",
    },
    {
        "codigo": "INS-MV2000-04_328",
        "categoria": "Medidores/Monitores de Vibração",
        "tipo": "Medidor de Vibração",
        "marca": "Instrutherm",
        "modelo": "MV-2000",
        "num_serie": "04_328",
        "num_equipamento": "04_328",
        "identificacao": "04_328",
        "data_ultima_calibracao": "",
    },
    # IBUTG e outros ------------------------------------------------------
    {
        "codigo": "CHR-NETTEMP-IBU000000724",
        "categoria": "Monitores IBUTG & Outros",
        "tipo": "Monitor IBUTG",
        "marca": "Chrompack",
        "modelo": "Net.Temp",
        "num_serie": "IBU000000724",
        "num_equipamento": "IBU000000724",
        "identificacao": "IBU000000724",
        "data_ultima_calibracao": "",
    },
    {
        "codigo": "INS-THDL400-181123417",
        "categoria": "Monitores IBUTG & Outros",
        "tipo": "Monitor IBUTG",
        "marca": "Instrutherm",
        "modelo": "THDL-400",
        "num_serie": "181123417",
        "num_equipamento": "181123417",
        "identificacao": "181123417",
        "data_ultima_calibracao": "",
    },
]


def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _normalise_date(value) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y-%m-%d")
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return text


def _catalogue_by_code() -> dict:
    return {item["codigo"]: dict(item) for item in DEFAULT_EQUIPMENTS}


def load_equipments() -> list[dict]:
    """Carrega o catálogo, preservando calibrações registradas localmente."""
    _ensure_dir()
    stored: dict[str, dict] = {}
    if os.path.exists(EQUIPMENTS_FILE):
        try:
            with open(EQUIPMENTS_FILE, "r", encoding="utf-8") as file:
                raw = json.load(file)
            if isinstance(raw, list):
                stored = {item.get("codigo"): item for item in raw if item.get("codigo")}
            elif isinstance(raw, dict):
                stored = raw
        except (OSError, ValueError):
            stored = {}

    equipment = _catalogue_by_code()
    for code, item in stored.items():
        if code in equipment:
            equipment[code].update(item)
        elif item.get("categoria") in EQUIPMENT_CATEGORIES:
            equipment[code] = dict(item)

    # Mantém a ordem oficial do catálogo.
    order = {item["codigo"]: index for index, item in enumerate(DEFAULT_EQUIPMENTS)}
    result = sorted(equipment.values(), key=lambda item: order.get(item.get("codigo"), 999))
    for item in result:
        item["data_ultima_calibracao"] = _normalise_date(
            item.get("data_ultima_calibracao")
        )

    serialized = json.dumps(result, ensure_ascii=False, indent=4)
    existing = ""
    if os.path.exists(EQUIPMENTS_FILE):
        try:
            with open(EQUIPMENTS_FILE, "r", encoding="utf-8") as file:
                existing = file.read()
        except OSError:
            existing = ""
    if existing != serialized:
        save_equipments(result)
    return result


def save_equipments(equipments: Iterable[dict]) -> None:
    _ensure_dir()
    with open(EQUIPMENTS_FILE, "w", encoding="utf-8") as file:
        json.dump(list(equipments), file, ensure_ascii=False, indent=4)


def update_calibration_date(codigo: str, calibration_date) -> bool:
    equipments = load_equipments()
    normalised = _normalise_date(calibration_date)
    changed = False
    for item in equipments:
        if item.get("codigo") == codigo:
            item["data_ultima_calibracao"] = normalised
            changed = True
            break
    if changed:
        save_equipments(equipments)
    return changed


def find_equipment(codigo: str | None = None, identificacao: str | None = None) -> dict | None:
    for item in load_equipments():
        if codigo and item.get("codigo") == codigo:
            return item
        if identificacao and item.get("identificacao") == identificacao:
            return item
    return None


def equipment_label(item: dict) -> str:
    return (
        f"{item.get('marca', '—')} {item.get('modelo', '—')} — "
        f"{item.get('num_equipamento') or item.get('identificacao') or 's/n'}"
    )


def calibration_label(item: dict) -> str:
    value = _normalise_date(item.get("data_ultima_calibracao"))
    if not value:
        return "Não informada"
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return value


def _strip_accents(text: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", str(text))
        if not unicodedata.combining(char)
    )


def sanitize_filename_part(value: str, fallback: str = "GERAL") -> str:
    text = _strip_accents(value or "").strip()
    text = re.sub(r"[^0-9A-Za-z._-]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("._-")
    return text or fallback


def normalize_horario(value) -> str:
    """Retorna o horário no formato HHMM (ex.: 1430)."""
    if isinstance(value, datetime):
        return value.strftime("%H%M")
    if isinstance(value, time):
        return value.strftime("%H%M")
    text = str(value or "").strip()
    if re.fullmatch(r"\d{4}", text):
        return text
    if re.fullmatch(r"\d{2}:\d{2}(:\d{2})?", text):
        return text.replace(":", "")[:4]
    now = datetime.now()
    return now.strftime("%H%M")


def build_photo_filename(
    horario,
    equipment: dict | str | None,
    epi_tag: str | None = None,
    extension: str = ".jpg",
) -> str:
    """Gera ``[Horario]_[IdentificacaoAparelho]_[TagEPI].jpg``.

    Exemplos: ``1430_03440.jpg`` e ``1430_03440_EPI_ProtetorAuditivo.jpg``.
    """
    if isinstance(equipment, dict):
        identificacao = (
            equipment.get("identificacao")
            or equipment.get("num_equipamento")
            or equipment.get("codigo")
            or "GERAL"
        )
    else:
        identificacao = equipment or "GERAL"

    parts = [normalize_horario(horario), sanitize_filename_part(str(identificacao))]
    if epi_tag:
        parts.append(sanitize_filename_part(epi_tag, fallback="EPI"))
    ext = extension if str(extension).startswith(".") else f".{extension}"
    return "_".join(parts) + ext


def equipment_file_preview(codigo: str, when=None, epi_tag: str | None = None) -> str:
    item = find_equipment(codigo=codigo)
    return build_photo_filename(when or datetime.now(), item, epi_tag)
