"""Scanner de EPI por imagem (OCR opcional) para o checklist da NR-06.

O módulo procura texto do Certificado de Aprovação (CA), siglas e nomes de
EPIs na foto. Quando o Tesseract não está instalado no dispositivo, a imagem
ainda é validada e o formulário recebe uma sugestão conservadora ("Parcial"),
que deve ser confirmada pelo avaliador.
"""

from __future__ import annotations

import io
import os
import re
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

try:  # Pillow é dependência transitiva do Streamlit, mas tratamos a ausência.
    from PIL import Image, ImageOps, ImageStat
except Exception:  # pragma: no cover - ambientes sem Pillow
    Image = None
    ImageOps = None
    ImageStat = None

try:
    import pytesseract

    _tesseract_cmd = os.environ.get("TESSERACT_CMD", "").strip()
    if _tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = _tesseract_cmd
except Exception:  # pragma: no cover - pytesseract é opcional
    pytesseract = None


EPI_KEYWORDS = {
    "Protetor auditivo": ["protetor auditivo", "protetor auricular", "auricular", "abafador", "plug"],
    "Óculos de proteção": ["oculos", "óculos", "lente de seguranca", "lente de segurança"],
    "Luvas": ["luva", "luvas"],
    "Capacete": ["capacete"],
    "Calçado de segurança": ["bota", "botina", "calcado", "calçado"],
    "Máscara/Respirador": ["mascara", "máscara", "respirador", "pff1", "pff2", "pff3"],
    "Avental": ["avental", "jaleco"],
    "Cinto/Talabarte": ["cinto", "talabarte", "trava queda"],
}

EPI_TAGS = {
    "Protetor auditivo": "EPI_ProtetorAuditivo",
    "Óculos de proteção": "EPI_Oculos",
    "Luvas": "EPI_Luvas",
    "Capacete": "EPI_Capacete",
    "Calçado de segurança": "EPI_Calcado",
    "Máscara/Respirador": "EPI_Mascara",
    "Avental": "EPI_Avental",
    "Cinto/Talabarte": "EPI_Cinto",
}

# Prioridade usada quando mais de um EPI aparece na imagem.
TAG_PRIORITY = [
    "Protetor auditivo",
    "Óculos de proteção",
    "Máscara/Respirador",
    "Luvas",
    "Capacete",
    "Calçado de segurança",
    "Cinto/Talabarte",
    "Avental",
]


def _ocr_available() -> bool:
    if pytesseract is None:
        return False
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def ocr_status() -> str:
    return "disponível" if _ocr_available() else "indisponível"


def _normalise(text: str) -> str:
    return (
        str(text or "")
        .lower()
        .replace("á", "a")
        .replace("à", "a")
        .replace("ã", "a")
        .replace("â", "a")
        .replace("é", "e")
        .replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ô", "o")
        .replace("õ", "o")
        .replace("ú", "u")
        .replace("ç", "c")
    )


def _detect_items(text: str) -> list[str]:
    normalised = _normalise(text)
    found = []
    for item, keywords in EPI_KEYWORDS.items():
        if any(_normalise(keyword) in normalised for keyword in keywords):
            found.append(item)
    return found


def _detect_ca(text: str) -> list[str]:
    # Aceita "CA 12345", "CA: 12345", "C.A. 12345" e variações.
    matches = re.findall(r"\bC\.?\s*A\.?\s*[:\-]?\s*(\d{4,6})\b", text, re.IGNORECASE)
    return sorted(set(matches))


def analyze_epi_image(image_bytes: bytes) -> dict:
    """Analisa a foto e devolve um JSON com o reconhecimento do EPI."""
    recognition = {
        "detected": False,
        "items": [],
        "ca": [],
        "text": "",
        "confidence": 0.0,
        "status": "Revisar",
        "source": "visual",
        "ocr_status": ocr_status(),
        "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "image": {},
    }

    if not image_bytes:
        recognition["message"] = "Nenhuma imagem informada."
        return recognition

    if Image is None:
        recognition["message"] = "Não foi possível abrir a imagem neste dispositivo."
        return recognition

    try:
        image = Image.open(io.BytesIO(image_bytes))
        image = ImageOps.exif_transpose(image).convert("RGB")
    except Exception:
        recognition["message"] = "Arquivo de imagem inválido ou corrompido."
        return recognition

    stats = ImageStat.Stat(image)
    brightness = round(sum(stats.mean) / 3, 1)
    width, height = image.size
    recognition["image"] = {
        "width": width,
        "height": height,
        "brightness": brightness,
    }

    text = ""
    if _ocr_available():
        try:
            text = pytesseract.image_to_string(image, lang="por")
        except Exception:
            try:
                text = pytesseract.image_to_string(image)
            except Exception:
                text = ""
        if text:
            recognition["source"] = "ocr"

    text = (text or "").strip()
    items = _detect_items(text)
    ca_numbers = _detect_ca(text)

    recognition["items"] = items
    recognition["ca"] = ca_numbers
    recognition["text"] = text[:1500]
    recognition["detected"] = bool(items or ca_numbers)

    if ca_numbers:
        recognition["confidence"] = 0.95
        recognition["status"] = "Sim"
    elif items:
        recognition["confidence"] = 0.75
        recognition["status"] = "Sim"
    elif text:
        recognition["confidence"] = 0.35
        recognition["status"] = "Parcial"
        recognition["message"] = (
            "A foto foi lida, mas não foi possível confirmar o EPI. Revise o checklist."
        )
    else:
        recognition["confidence"] = 0.15
        recognition["status"] = "Parcial"
        recognition["message"] = (
            "Reconhecimento automático indisponível (instale o Tesseract para OCR). "
            "A foto foi registrada; confirme o checklist manualmente."
        )

    return recognition


def epi_tag(recognition: dict | None) -> str:
    """Tag usada no nome do arquivo, ex.: ``EPI_ProtetorAuditivo``."""
    recognition = recognition or {}
    items = recognition.get("items") or []
    for candidate in TAG_PRIORITY:
        if candidate in items:
            return EPI_TAGS[candidate]
    if recognition.get("ca"):
        return "EPI_CA"
    return "EPI_Registro"


def suggest_epi_answers(recognition: dict | None) -> dict:
    """Converte o reconhecimento em respostas do checklist NR-06."""
    recognition = recognition or {}
    detected = bool(recognition.get("detected"))
    has_ca = bool(recognition.get("ca"))
    items = recognition.get("items") or []
    confidence = float(recognition.get("confidence") or 0)

    if detected:
        status = "Sim"
    elif confidence > 0:
        status = "Parcial"
    else:
        status = "Parcial"

    detail_parts = []
    if items:
        detail_parts.append("EPIs identificados: " + ", ".join(items))
    if recognition.get("ca"):
        detail_parts.append("CA: " + ", ".join(recognition["ca"]))
    if recognition.get("message"):
        detail_parts.append(recognition["message"])
    detail = " | ".join(detail_parts) or "Sem identificação automática de EPI."
    detail = f"Scanner EPI ({recognition.get('analyzed_at', '')}): {detail}"

    answers = {
        "epi_fornecimento": status,
        "epi_uso": status,
        "epi_conservacao": "Sim" if detected and confidence >= 0.6 else "Parcial",
        "epi_ca": "Sim" if has_ca else "N/A",
        "epi_obs": detail,
    }
    return answers
