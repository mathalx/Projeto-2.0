import base64
import io
import json
import os

import pytest
from PIL import Image

import src.equipment_catalog as equipment_catalog
import src.epi_scanner as epi_scanner
import src.export_manager as export_manager
import src.storage_manager as storage
import src.weather_service as weather_service
from src.equipment_catalog import (
    build_photo_filename,
    calibration_label,
    find_equipment,
    load_equipments,
)


@pytest.fixture()
def isolated_storage(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    monkeypatch.setattr(storage, "DATA_DIR", str(data_dir))
    monkeypatch.setattr(storage, "CLIENTS_FILE", str(data_dir / "clients.json"))
    monkeypatch.setattr(storage, "VISITS_FILE", str(data_dir / "visits.json"))
    monkeypatch.setattr(storage, "INSPECTIONS_FILE", str(data_dir / "visits.json"))
    monkeypatch.setattr(storage, "PHOTOS_DIR", str(data_dir / "photos"))
    monkeypatch.setattr(storage, "WORKER_PHOTOS_DIR", str(data_dir / "photos" / "workers"))
    monkeypatch.setattr(equipment_catalog, "DATA_DIR", str(data_dir))
    monkeypatch.setattr(
        equipment_catalog, "EQUIPMENTS_FILE", str(data_dir / "equipments.json")
    )
    monkeypatch.setattr(export_manager, "EXPORTS_DIR", str(data_dir / "exports"))
    return tmp_path


def _png_bytes(color=(200, 30, 30)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), color).save(buffer, format="PNG")
    return buffer.getvalue()


def _data_url(image_bytes: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(image_bytes).decode("ascii")


def test_equipment_catalogue_has_all_official_devices(isolated_storage):
    equipments = load_equipments()
    assert len(equipments) == 14

    codes = {item["codigo"] for item in equipments}
    assert "CHR-SMARTDB-03440" in codes
    assert "INS-DOS1000X-04_02385" in codes
    assert "INL-VENTUSPRO" in codes
    assert "CHR-SMARTVIB-RBC5_12181_610" in codes
    assert "CHR-NETTEMP-IBU000000724" in codes

    dos = find_equipment(codigo="INS-DOS1000X-04_02385")
    assert dos["identificacao"] == "DOS1000_04_02385"
    assert calibration_label(dos) == "Não informada"


def test_standard_photo_file_names():
    smartdb = find_equipment(codigo="CHR-SMARTDB-03440")
    assert build_photo_filename("14:30", smartdb) == "1430_03440.jpg"
    assert (
        build_photo_filename("14:30", smartdb, "EPI_ProtetorAuditivo")
        == "1430_03440_EPI_ProtetorAuditivo.jpg"
    )

    dos = find_equipment(codigo="INS-DOS1000X-04_02385")
    assert build_photo_filename("09:15", dos) == "0915_DOS1000_04_02385.jpg"


def test_inspection_full_flow_with_worker_equipment_photos_and_signatures(
    isolated_storage,
):
    storage.init_storage()
    success, inspection_id, _ = storage.create_inspection(
        "Empresa ACN", "2026-11-09", "2026-11-10", "Ana.norte"
    )
    assert success and inspection_id

    storage.update_inspection(
        inspection_id,
        empresa_nome="Empresa ACN",
        data_avaliacao="2026-11-09",
        data_avaliacao_fim="2026-11-10",
    )
    storage.save_inspection_weather(
        inspection_id,
        24.5,
        58.0,
        {
            "temperatura": 24.5,
            "umidade": 58.0,
            "latitude": -23.55,
            "longitude": -46.63,
            "cidade": "São Paulo",
        },
    )

    success, _message, photo_url = storage.save_inspection_worker(
        inspection_id,
        "João da Silva",
        "Operador",
        "Setor B",
        photo_bytes=_png_bytes(),
        photo_filename="rosto.png",
    )
    assert success
    assert os.path.exists(photo_url)

    smartdb = find_equipment(codigo="CHR-SMARTDB-03440")
    assert storage.set_inspection_devices(inspection_id, [smartdb])[0]

    recognition = {
        "detected": True,
        "items": ["Protetor auditivo"],
        "ca": ["12345"],
        "status": "Sim",
        "confidence": 0.95,
    }
    filename = build_photo_filename("14:30", smartdb, "EPI_ProtetorAuditivo")
    success, _message = storage.add_photo_to_visit(
        inspection_id,
        _png_bytes(),
        filename,
        "Foto de EPI",
        nome_arquivo=filename,
        horario_registro="14:30:00",
        equipamento_id=smartdb["codigo"],
        reconhecimento_epi=recognition,
    )
    assert success

    success, _message = storage.save_inspection_signatures(
        inspection_id,
        _data_url(_png_bytes()),
        _data_url(_png_bytes()),
    )
    assert success

    inspection = storage.get_inspection(inspection_id)
    assert inspection["empresa_nome"] == "Empresa ACN"
    assert inspection["temperatura_capturada"] == 24.5
    assert inspection["umidade_capturada"] == 58.0
    assert inspection["worker"]["funcionario_nome"] == "João da Silva"
    assert inspection["worker"]["funcionario_foto_url"] == photo_url
    assert inspection["devices"][0]["codigo"] == smartdb["codigo"]
    assert inspection["photos"][0]["nome_arquivo"] == filename
    assert inspection["photos"][0]["horario_registro"] == "14:30:00"
    assert inspection["photos"][0]["equipamento_id"] == smartdb["codigo"]
    assert inspection["photos"][0]["reconhecimento_epi"]["items"] == [
        "Protetor auditivo"
    ]
    assert inspection["signatures"]["ass_responsavel_tecnico"].startswith("data:image")
    assert inspection["signatures"]["ass_avaliador"].startswith("data:image")


def test_epi_scanner_returns_json_and_suggests_nr06_answers(isolated_storage):
    recognition = epi_scanner.analyze_epi_image(_png_bytes())
    json.dumps(recognition)  # garante que o campo JSON é serializável
    assert recognition["image"]["width"] == 64
    assert recognition["status"] in {"Parcial", "Sim", "Revisar"}
    assert epi_scanner.epi_tag(recognition) == "EPI_Registro"

    fake = {
        "detected": True,
        "items": ["Protetor auditivo"],
        "ca": ["12345"],
        "status": "Sim",
        "confidence": 0.95,
        "analyzed_at": "2026-11-09 14:30:00",
    }
    answers = epi_scanner.suggest_epi_answers(fake)
    assert answers["epi_fornecimento"] == "Sim"
    assert answers["epi_uso"] == "Sim"
    assert answers["epi_ca"] == "Sim"
    assert "Protetor auditivo" in answers["epi_obs"]
    assert epi_scanner.epi_tag(fake) == "EPI_ProtetorAuditivo"


class _FakeResponse:
    status_code = 200

    def json(self):
        return {
            "main": {"temp": 23.4, "humidity": 61},
            "weather": [{"description": "nublado"}],
            "name": "São Paulo",
        }


def test_openweather_capture(monkeypatch):
    calls = []

    def fake_get(url, params=None, timeout=None):
        calls.append((url, params, timeout))
        return _FakeResponse()

    monkeypatch.setattr(weather_service, "get_api_key", lambda api_key=None: "chave")
    monkeypatch.setattr(weather_service.requests, "get", fake_get)

    reading = weather_service.capture_weather(-23.55, -46.63)
    assert reading.temperatura == 23.4
    assert reading.umidade == 61.0
    assert reading.cidade == "São Paulo"
    assert calls[0][1]["units"] == "metric"
    assert calls[0][1]["appid"] == "chave"


def test_openweather_requires_key(monkeypatch):
    monkeypatch.setattr(weather_service, "get_api_key", lambda api_key=None: "")
    with pytest.raises(weather_service.WeatherError):
        weather_service.capture_weather(-23.55, -46.63)


def test_pdf_includes_worker_equipment_and_signatures(isolated_storage):
    storage.init_storage()
    _success, inspection_id, _ = storage.create_inspection(
        "Empresa Laudo", "2026-11-09", "2026-11-09", "Ana.norte"
    )
    storage.update_inspection(
        inspection_id,
        empresa_nome="Empresa Laudo",
        data_avaliacao="2026-11-09",
        temperatura_capturada=23.4,
        umidade_capturada=61.0,
    )
    storage.save_inspection_worker(
        inspection_id,
        "Maria Souza",
        "Técnica",
        "Produção",
        photo_bytes=_png_bytes((10, 120, 60)),
        photo_filename="rosto.png",
    )
    device = find_equipment(codigo="CHR-SMARTDB-03440")
    storage.set_inspection_devices(inspection_id, [device])
    storage.save_inspection_signatures(
        inspection_id,
        _data_url(_png_bytes()),
        _data_url(_png_bytes()),
    )

    pdf_path = export_manager.generate_pdf_report(inspection_id)
    assert pdf_path and os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 0
