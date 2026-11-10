"""Testes do novo fluxo isolado de inspeção de campo (v2)."""

from __future__ import annotations

import base64
import io
import os
from pathlib import Path

import pytest
from PIL import Image
from streamlit.testing.v1 import AppTest

import src.equipment_catalog as equipment_catalog
import src.export_manager as export_manager
import src.storage_manager as storage
import src.weather_service as weather_service
from src.equipment_catalog import find_equipment
from src.features.field_inspection import render_field_inspection_view  # noqa: F401
from src.features.field_inspection.constants import NAV_GROUPS
from src.features.field_inspection.documents import generate_inspection_excel
from src.features.field_inspection.services import validate_for_finalize

MAIN_SCRIPT = str(Path(__file__).resolve().parents[1] / "src" / "main.py")


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


def _png_bytes(color=(10, 120, 60)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), color).save(buffer, format="PNG")
    return buffer.getvalue()


def _data_url(image_bytes: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(image_bytes).decode("ascii")


def test_sidebar_follows_acn_norte_layout():
    labels = [item.label for _group, items in NAV_GROUPS for item in items]
    assert labels == [
        "Painel Inicial",
        "Clientes",
        "Visitas Técnicas / Inspeções de Campo",
        "Fotografias (Galeria de Fotos do Dia)",
        "Relatórios & Exportação",
        "Cadastrar Cliente",
        "Nova Visita / Nova Inspeção",
    ]


def test_new_module_renders_directly_without_login(isolated_storage):
    app = AppTest.from_file(MAIN_SCRIPT, default_timeout=60)
    app.session_state["username"] = "Ana.norte"
    app.session_state["is_admin"] = True
    app.run()

    assert not app.exception, [error.value for error in app.exception]
    assert app.session_state["authenticated"] is True
    assert app.session_state["current_page"] == "Formulário de Campo"

    labels = [widget.label for widget in app.text_input]
    assert "Nome da empresa *" in labels
    assert "Nome do funcionário *" in labels
    assert "Senha" not in labels

    button_labels = [button.label for button in app.button]
    assert "📋 Visitas Técnicas / Inspeções de Campo" in button_labels
    assert "📷 Fotografias (Galeria de Fotos do Dia)" in button_labels
    assert "🚀 Nova Visita / Nova Inspeção" in button_labels

    rendered_markdown = "\n".join(markdown.value for markdown in app.markdown)
    assert "Ana.norte - Administrador" in rendered_markdown
    assert "Perfil ativo" in rendered_markdown


def test_quick_access_creates_a_new_inspection(isolated_storage):
    app = AppTest.from_file(MAIN_SCRIPT, default_timeout=60)
    app.session_state["username"] = "Ana.norte"
    app.session_state["is_admin"] = True
    app.run()

    before = len(storage.load_visits())
    app.button(key="quick_new_visit").click()
    app.run()

    assert not app.exception, [error.value for error in app.exception]
    assert len(storage.load_visits()) == before + 1
    assert app.session_state["current_page"] == "Formulário de Campo"


def test_equipment_chips_persist_official_ids(isolated_storage):
    app = AppTest.from_file(MAIN_SCRIPT, default_timeout=60)
    app.session_state["username"] = "Ana.norte"
    app.session_state["is_admin"] = True
    app.run()

    audiodosimeter = app.pills[0]
    audiodosimeter.set_value([audiodosimeter.options[0]])
    app.run()

    assert not app.exception, [error.value for error in app.exception]
    devices = list(storage.load_visits().values())[0]["devices"]
    assert devices[0]["identificacao"] == "03440"
    assert devices[0]["codigo"] == "CHR-SMARTDB-03440"


def test_weather_auto_falls_back_to_open_meteo(monkeypatch):
    class _FakeResponse:
        status_code = 200

        def json(self):
            return {
                "current": {
                    "temperature_2m": 27.3,
                    "relative_humidity_2m": 64,
                    "weather_code": 3,
                }
            }

    calls = []

    def fake_get(url, params=None, timeout=None):
        calls.append((url, params, timeout))
        return _FakeResponse()

    monkeypatch.setattr(weather_service, "is_configured", lambda api_key=None: False)
    monkeypatch.setattr(weather_service.requests, "get", fake_get)

    reading = weather_service.capture_weather_auto(-3.1, -60.0)
    assert reading.temperatura == 27.3
    assert reading.umidade == 64.0
    assert reading.descricao == "Nublado"
    assert calls[0][0] == weather_service.OPEN_METEO_URL


def test_final_validation_preserves_existing_business_rules(isolated_storage):
    storage.init_storage()
    _success, inspection_id, _ = storage.create_inspection(
        "", "2026-11-09", "2026-11-09", "Ana.norte"
    )
    inspection = storage.get_inspection(inspection_id)

    pending = validate_for_finalize(inspection, {}, "", "")
    assert "Nome da empresa" in pending
    assert "Nome do funcionário" in pending
    assert "Foto do rosto do funcionário" in pending
    assert "Pelo menos um equipamento" in pending
    assert "Assinatura do responsável técnico" in pending
    assert "Assinatura do avaliador" in pending


def test_per_inspection_excel_contains_technical_data(isolated_storage):
    storage.init_storage()
    _success, inspection_id, _ = storage.create_inspection(
        "Empresa Planilha", "2026-11-09", "2026-11-10", "Ana.norte"
    )
    storage.save_inspection_worker(
        inspection_id,
        "Maria Souza",
        "Técnica",
        "Produção",
        photo_bytes=_png_bytes(),
        photo_filename="rosto.png",
    )
    device = find_equipment(codigo="CHR-SMARTDB-03440")
    storage.set_inspection_devices(inspection_id, [device])
    storage.save_inspection_signatures(
        inspection_id,
        _data_url(_png_bytes()),
        _data_url(_png_bytes()),
    )

    path = generate_inspection_excel(inspection_id)
    assert path and os.path.exists(path)
    assert os.path.getsize(path) > 0
