from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import src.equipment_catalog as equipment_catalog
import src.storage_manager as storage

MAIN_SCRIPT = str(Path(__file__).resolve().parents[1] / "src" / "main.py")

PAGES = [
    "Formulário de Campo",
    "Painel Inicial",
    "Clientes",
    "Visitas Técnicas",
    "Fotografias",
    "Relatórios & Exportação",
    "Alterar Senha",
    "Gerenciar Usuários",
]


@pytest.fixture(autouse=True)
def isolated_app_storage(tmp_path, monkeypatch):
    """Evita que os testes de interface gravem no diretório data/ real."""
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
    yield


def _app():
    app = AppTest.from_file(MAIN_SCRIPT, default_timeout=60)
    app.session_state["username"] = "Ana.norte"
    app.session_state["is_admin"] = True
    return app


def test_app_opens_directly_on_field_form_without_login():
    app = _app()
    app.run()

    assert not app.exception, [error.value for error in app.exception]
    assert app.session_state["authenticated"] is True
    assert app.session_state["current_page"] == "Formulário de Campo"
    labels = [widget.label for widget in app.text_input]
    assert "Nome da empresa *" in labels
    assert "Nome do funcionário *" in labels
    assert "Senha" not in labels


@pytest.mark.parametrize("page", PAGES)
def test_all_pages_render_directly(page):
    app = _app()
    app.session_state["current_page"] = page
    app.run()
    assert not app.exception, [error.value for error in app.exception]


def test_sidebar_navigation_changes_page():
    app = _app()
    app.run()
    app.button(key="nav_Clientes").click()
    app.run()
    assert not app.exception, [error.value for error in app.exception]
    assert app.session_state["current_page"] == "Clientes"
