"""Motor de documentos do fluxo v2: laudo PDF e planilha Excel por inspeção.

O PDF continua sendo produzido pelo motor homologado em
``src/export_manager.py`` (foto do funcionário, tabela de equipamentos e
assinaturas no rodapé). A planilha por inspeção é uma visão consolidada do
mesmo registro, sem alterar as exportações globais existentes.
"""

from __future__ import annotations

import base64
import io
import os
from datetime import datetime

import pandas as pd
from openpyxl.drawing.image import Image as XLImage

from src import export_manager
from src.form_template import TECHNICAL_FORM_SECTIONS
from src.storage_manager import get_inspection
from src.equipment_catalog import sanitize_filename_part


def _decode_data_url(value: str | None) -> bytes | None:
    if not value:
        return None
    text = str(value).strip()
    if "," in text and text.lower().startswith("data:"):
        text = text.split(",", 1)[1]
    try:
        return base64.b64decode(text)
    except (ValueError, TypeError):
        return None


def _add_image(worksheet, image, anchor: str) -> bool:
    try:
        worksheet.add_image(image, anchor)
        return True
    except Exception:
        return False


def _embed_worker_photo(worksheet, worker: dict) -> None:
    path = worker.get("funcionario_foto_url")
    if not path or not os.path.exists(path):
        return
    try:
        worksheet.column_dimensions["C"].width = 22
        worksheet.row_dimensions[2].height = 82
        worksheet["C2"] = "Foto do avaliado"
        image = XLImage(path)
        image.width = 92
        image.height = 92
        _add_image(worksheet, image, "C3")
    except Exception:
        return


def _embed_signatures(worksheet, signatures: dict) -> None:
    positions = (
        ("Responsável Técnico", "ass_responsavel_tecnico", "A3", "B3"),
        ("Avaliador de Campo", "ass_avaliador", "A4", "B4"),
    )
    worksheet.column_dimensions["A"].width = 26
    worksheet.column_dimensions["B"].width = 46
    for label, key, label_cell, image_cell in positions:
        worksheet[label_cell] = label
        raw = _decode_data_url(signatures.get(key))
        if not raw:
            continue
        try:
            image = XLImage(io.BytesIO(raw))
            image.width = 180
            image.height = 60
            _add_image(worksheet, image, image_cell)
        except Exception:
            continue
    worksheet.row_dimensions[3].height = 52
    worksheet.row_dimensions[4].height = 52


def _format_calibration(item: dict) -> str:
    value = str(item.get("data_ultima_calibracao") or "")
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return "Não informada"


def generate_inspection_pdf(inspection_id: str) -> str | None:
    """Gera o laudo PDF corporativo usando o motor existente."""
    return export_manager.generate_pdf_report(inspection_id)


def generate_inspection_excel(inspection_id: str) -> str | None:
    """Gera uma planilha consolidada da inspeção selecionada."""
    inspection = get_inspection(inspection_id)
    if not inspection:
        return None

    export_manager.init_exports_dir()
    worker = inspection.get("worker") or {}
    climate = inspection.get("clima") or {}
    signatures = inspection.get("signatures") or {}
    devices = inspection.get("devices") or []

    company = (
        inspection.get("empresa_nome")
        or inspection.get("client_name")
        or "Inspecao"
    )
    filename = (
        "Laudo_"
        f"{sanitize_filename_part(company, fallback='Inspecao')}_"
        f"{inspection_id}_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )
    path = os.path.join(export_manager.EXPORTS_DIR, filename)

    summary = pd.DataFrame(
        [
            {"Campo": "Empresa", "Valor": company},
            {"Campo": "Data de avaliação", "Valor": inspection.get("data_avaliacao") or inspection.get("date")},
            {"Campo": "Data final", "Valor": inspection.get("data_avaliacao_fim")},
            {"Campo": "Técnico responsável", "Valor": inspection.get("technician")},
            {"Campo": "Situação", "Valor": inspection.get("status")},
            {"Campo": "Temperatura (°C)", "Valor": inspection.get("temperatura_capturada")},
            {"Campo": "Umidade (%)", "Valor": inspection.get("umidade_capturada")},
            {"Campo": "Cidade/clima", "Valor": climate.get("cidade") or "—"},
            {"Campo": "Funcionário avaliado", "Valor": worker.get("funcionario_nome")},
            {"Campo": "Função", "Valor": worker.get("funcao")},
            {"Campo": "Setor", "Valor": worker.get("setor")},
            {"Campo": "Foto do funcionário", "Valor": worker.get("funcionario_foto_url")},
            {"Campo": "Observações", "Valor": inspection.get("observations")},
            {"Campo": "Conclusões", "Valor": inspection.get("conclusions")},
        ]
    )

    equipment_rows = []
    for item in devices:
        equipment_rows.append(
            {
                "Categoria": item.get("categoria"),
                "Tipo": item.get("tipo"),
                "Marca": item.get("marca"),
                "Modelo": item.get("modelo"),
                "Identificação": item.get("identificacao"),
                "Nº Série/Equipamento": item.get("num_serie")
                or item.get("num_equipamento"),
                "Certificado": item.get("certificado"),
                "Última calibração": _format_calibration(item),
            }
        )
    equipment = pd.DataFrame(
        equipment_rows,
        columns=[
            "Categoria",
            "Tipo",
            "Marca",
            "Modelo",
            "Identificação",
            "Nº Série/Equipamento",
            "Certificado",
            "Última calibração",
        ],
    )

    checklist_rows = []
    forms = inspection.get("forms") or {}
    for category, category_info in TECHNICAL_FORM_SECTIONS.items():
        answers = forms.get(category) or {}
        for field in category_info.get("fields", []):
            checklist_rows.append(
                {
                    "Seção": category_info.get("title", category),
                    "Item": field.get("label"),
                    "Resposta": answers.get(field["id"], ""),
                    "Obrigatório": bool(field.get("required", field.get("type") == "select")),
                }
            )
    checklist = pd.DataFrame(checklist_rows)

    photo_rows = []
    for photo in inspection.get("photos") or []:
        recognition = photo.get("reconhecimento_epi") or {}
        photo_rows.append(
            {
                "Arquivo": photo.get("nome_arquivo") or photo.get("saved_filename"),
                "Horário": photo.get("horario_registro"),
                "Equipamento": photo.get("equipamento_id"),
                "Legenda": photo.get("description"),
                "Reconhecimento EPI": recognition.get("status"),
                "EPIs": ", ".join(recognition.get("items") or []),
                "Caminho": photo.get("path"),
            }
        )
    photos = pd.DataFrame(
        photo_rows,
        columns=[
            "Arquivo",
            "Horário",
            "Equipamento",
            "Legenda",
            "Reconhecimento EPI",
            "EPIs",
            "Caminho",
        ],
    )

    signatures_df = pd.DataFrame(
        [
            {
                "Responsável Técnico": "Assinada"
                if signatures.get("ass_responsavel_tecnico")
                else "Pendente",
                "Avaliador de Campo": "Assinada"
                if signatures.get("ass_avaliador")
                else "Pendente",
            }
        ]
    )

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Inspeção", index=False)
        equipment.to_excel(writer, sheet_name="Equipamentos", index=False)
        checklist.to_excel(writer, sheet_name="Checklist", index=False)
        photos.to_excel(writer, sheet_name="Fotografias", index=False)
        signatures_df.to_excel(writer, sheet_name="Assinaturas", index=False)

        # A foto do trabalhador e as assinaturas digitais também são
        # incorporadas na planilha, mantendo a paridade com o laudo PDF.
        _embed_worker_photo(writer.sheets["Inspeção"], worker)
        _embed_signatures(writer.sheets["Assinaturas"], signatures)

    return path
