import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

MAIN_SCRIPT = str(Path(__file__).resolve().parents[1] / "src" / "main.py")

PAGES = [
    "Painel Inicial",
    "Clientes",
    "Visitas Técnicas",
    "Fotografias",
    "Relatórios & Exportação",
    "Alterar Senha",
    "Gerenciar Usuários",
]


def _authenticated_app():
    app = AppTest.from_file(MAIN_SCRIPT, default_timeout=60)
    app.session_state["authenticated"] = True
    app.session_state["username"] = "Ana.norte"
    app.session_state["is_admin"] = True
    return app


def test_app_opens_directly_on_main_screen_without_login(monkeypatch):
    monkeypatch.setenv("REQUIRE_AUTH", "false")
    app = AppTest.from_file(MAIN_SCRIPT, default_timeout=60)
    app.run()
    assert not app.exception, [error.value for error in app.exception]
    assert app.session_state["authenticated"] is True
    assert app.session_state["current_page"] == "Painel Inicial"
    labels = [widget.label for widget in app.text_input]
    assert "Senha" not in labels
    assert "E-mail ou usuário" not in labels


def test_login_screen_renders_when_auth_required(monkeypatch):
    monkeypatch.setenv("REQUIRE_AUTH", "true")
    app = AppTest.from_file(MAIN_SCRIPT, default_timeout=60)
    app.run()
    assert not app.exception, [error.value for error in app.exception]
    assert app.session_state["authenticated"] is False
    labels = [widget.label for widget in app.text_input]
    assert "Senha" in labels
    assert "E-mail ou usuário" in labels


def test_login_blocks_empty_fields_when_auth_required(monkeypatch):
    monkeypatch.setenv("REQUIRE_AUTH", "true")
    app = AppTest.from_file(MAIN_SCRIPT, default_timeout=60)
    app.run()
    app.button[0].click()
    app.run()
    assert not app.exception, [error.value for error in app.exception]
    assert any("Informe o e-mail" in str(getattr(err, "value", "")) for err in app.error)


def test_login_with_email_calls_xano_login_flow(monkeypatch):
    monkeypatch.setenv("REQUIRE_AUTH", "true")
    import src.views.login_view as login_view
    from src.modules.authentication.auth_service import XanoSession

    called = {}

    def fake_auth(email, password):
        called["email"] = email
        called["password"] = password
        return XanoSession(
            token="fake-jwt",
            role="administrador",
            user={"id": 1, "name": "Ana Norte", "email": email},
        )

    monkeypatch.setattr(login_view, "authenticate_with_xano", fake_auth)

    app = AppTest.from_file(MAIN_SCRIPT, default_timeout=60)
    app.run()
    app.text_input[0].input("ana@acnnorte.com.br")
    app.text_input[1].input("senha123")
    app.button[0].click()
    app.run()
    assert not app.exception, [error.value for error in app.exception]
    assert called.get("email") == "ana@acnnorte.com.br"
    assert app.session_state["authenticated"] is True
    assert app.session_state["username"] == "Ana Norte"


@pytest.mark.parametrize("page", PAGES)
def test_authenticated_pages_render(page):
    app = _authenticated_app()
    app.session_state["current_page"] = page
    app.run()
    assert not app.exception, [error.value for error in app.exception]


def test_sidebar_navigation_changes_page():
    app = _authenticated_app()
    app.run()
    app.button(key="nav_Clientes").click()
    app.run()
    assert not app.exception, [error.value for error in app.exception]
    assert app.session_state["current_page"] == "Clientes"


def test_main_registers_every_navigation_page():
    import src.main as main_module
    from src.ui_components import NAV_ITEMS

    assert set(main_module.PAGE_RENDERERS) == {item[0] for item in NAV_ITEMS}


def test_feature_registry_loads_all_modules():
    from src.features import available_features, initialize_features

    loaded = initialize_features()
    assert set(loaded) == set(available_features())
    assert all(hasattr(module, "__name__") for module in loaded.values())


def test_entry_points_import_from_foreign_cwd():
    root = Path(__file__).resolve().parents[1]
    entry_points = (root / "src" / "main.py", root / "main.py")
    code = (
        "import importlib.util;"
        "spec=importlib.util.spec_from_file_location('acn_import_probe', {!r});"
        "module=importlib.util.module_from_spec(spec);"
        "spec.loader.exec_module(module);"
        "print('OK')"
    )
    for entry in entry_points:
        result = subprocess.run(
            [sys.executable, "-c", code.format(str(entry))],
            cwd=tempfile.gettempdir(),
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "OK" in result.stdout
