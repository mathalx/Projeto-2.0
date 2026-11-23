"""Testes do menu lateral recolhível e reabrível (Streamlit 1.64.0)."""

import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src import ui_components as ui
from src.main import PAGE_CONFIG

MAIN_SCRIPT = str(Path(__file__).resolve().parents[1] / "src" / "main.py")


def _authenticated_app():
    app = AppTest.from_file(MAIN_SCRIPT, default_timeout=60)
    app.session_state["authenticated"] = True
    app.session_state["username"] = "Ana.norte"
    app.session_state["is_admin"] = True
    return app


def _rule_bodies(css: str, token: str):
    """Retorna o corpo das regras CSS cujo seletor contém ``token``."""
    return [
        body
        for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css)
        if token in selector
    ]


def test_page_config_starts_sidebar_automatically():
    assert PAGE_CONFIG["initial_sidebar_state"] == "auto"
    assert PAGE_CONFIG["layout"] == "wide"


def test_sidebar_css_keeps_native_controls_visible():
    css = ui.sidebar_css()

    # Streamlit 1.64.0: estes são os controles nativos de reabrir e fechar.
    assert '[data-testid="stExpandSidebarButton"]' in css
    assert '[data-testid="stSidebarCollapseButton"]' in css
    # Compatibilidade com versões anteriores.
    assert '[data-testid="stSidebarCollapsedControl"]' in css
    assert '[data-testid="collapsedControl"]' in css

    for token in (
        "stHeader",
        "stToolbar",
        "stExpandSidebarButton",
        "stSidebarCollapseButton",
        "stSidebarCollapsedControl",
        "collapsedControl",
    ):
        for body in _rule_bodies(css, token):
            assert "display: none" not in body.replace(" ", " ").lower()
            assert "visibility: hidden" not in body.lower()
            assert "opacity: 0" not in body.lower()


def test_sidebar_css_has_touch_target_and_mobile_rules():
    css = ui.sidebar_css()
    assert "min-width: 44px" in css
    assert "min-height: 44px" in css
    assert f"max-width: {ui.SIDEBAR_MOBILE_BREAKPOINT_PX}px" in css
    assert ".st-key-sidebar_toggle" in css
    assert ".st-key-sidebar_close_menu" in css


def test_bridge_html_supports_current_and_legacy_testids():
    markup = ui.build_sidebar_bridge_html(ui.SIDEBAR_COMMAND_TOGGLE)

    assert "window.parent.document" in markup
    assert '[data-testid="stExpandSidebarButton"]' in markup
    assert '[data-testid="stSidebarCollapseButton"]' in markup
    assert '[data-testid="stSidebarCollapsedControl"]' in markup
    assert '[data-testid="collapsedControl"]' in markup
    assert "Abrir menu" in markup
    assert "Fechar menu" in markup
    assert '"toggle"' in markup
    assert str(ui.SIDEBAR_MOBILE_BREAKPOINT_PX) in markup


def test_bridge_html_serializes_each_command():
    assert "const COMMAND = null;" in ui.build_sidebar_bridge_html(None)
    assert 'const COMMAND = "close";' in ui.build_sidebar_bridge_html(
        ui.SIDEBAR_COMMAND_CLOSE
    )
    assert 'const COMMAND = "close_if_mobile";' in ui.build_sidebar_bridge_html(
        ui.SIDEBAR_COMMAND_CLOSE_MOBILE
    )


def test_bridge_html_changes_between_runs_to_reexecute_toggle():
    first = ui.next_sidebar_render_token()
    second = ui.next_sidebar_render_token()

    assert first and second and first != second
    markup = ui.build_sidebar_bridge_html(ui.SIDEBAR_COMMAND_TOGGLE, first)
    assert first in markup
    assert "RENDER_TOKEN" in markup


def test_sidebar_state_defaults_to_open_and_survives_rerun():
    app = _authenticated_app()
    app.run()

    assert not app.exception, [error.value for error in app.exception]
    assert app.session_state[ui.SIDEBAR_OPEN_KEY] is True

    app.run()
    assert app.session_state[ui.SIDEBAR_OPEN_KEY] is True


def test_sidebar_toggle_button_flips_session_state():
    app = _authenticated_app()
    app.run()

    app.button(key="sidebar_toggle").click()
    app.run()
    assert not app.exception, [error.value for error in app.exception]
    assert app.session_state[ui.SIDEBAR_OPEN_KEY] is False

    app.button(key="sidebar_toggle").click()
    app.run()
    assert app.session_state[ui.SIDEBAR_OPEN_KEY] is True


def test_sidebar_close_button_sets_closed_state():
    app = _authenticated_app()
    app.run()

    assert app.button(key="sidebar_close_menu").label == "✕ Fechar menu"
    app.button(key="sidebar_close_menu").click()
    app.run()

    assert not app.exception, [error.value for error in app.exception]
    assert app.session_state[ui.SIDEBAR_OPEN_KEY] is False


def test_sidebar_state_survives_page_navigation():
    app = _authenticated_app()
    app.session_state[ui.SIDEBAR_OPEN_KEY] = False
    app.run()

    app.button(key="nav_Clientes").click()
    app.run()

    assert not app.exception, [error.value for error in app.exception]
    assert app.session_state["current_page"] == "Clientes"
    assert app.session_state[ui.SIDEBAR_OPEN_KEY] is False


@pytest.mark.parametrize(
    "page",
    [
        "Painel Inicial",
        "Clientes",
        "Visitas Técnicas",
        "Fotografias",
        "Relatórios & Exportação",
        "Alterar Senha",
        "Gerenciar Usuários",
    ],
)
def test_toggle_is_available_on_every_page(page):
    app = _authenticated_app()
    app.session_state["current_page"] = page
    app.run()

    assert not app.exception, [error.value for error in app.exception]
    assert app.button(key="sidebar_toggle").label == "☰ Menu"


def test_login_screen_does_not_render_sidebar_toggle(monkeypatch):
    monkeypatch.setenv("REQUIRE_AUTH", "true")
    app = AppTest.from_file(MAIN_SCRIPT, default_timeout=60)
    app.run()

    assert not app.exception, [error.value for error in app.exception]
    assert all(button.key != "sidebar_toggle" for button in app.button)


def test_request_helpers_update_session_state():
    script = f"""
import streamlit as st
from src import ui_components as ui

st.set_page_config(initial_sidebar_state="auto")
st.session_state.setdefault(ui.SIDEBAR_OPEN_KEY, True)

choice = st.radio("acao", ["none", "toggle", "close", "navigate"])
if choice == "toggle":
    ui.request_sidebar_toggle()
elif choice == "close":
    ui.request_sidebar_close()
elif choice == "navigate":
    ui.request_sidebar_close_on_navigation()

st.session_state["captured_open"] = st.session_state[ui.SIDEBAR_OPEN_KEY]
st.session_state["captured_command"] = st.session_state.get(ui.SIDEBAR_COMMAND_KEY)
"""
    app = AppTest.from_string(script)
    app.run()

    assert app.session_state["captured_open"] is True
    assert app.session_state["captured_command"] is None

    app.radio[0].set_value("toggle")
    app.run()
    assert app.session_state["captured_open"] is False
    assert app.session_state["captured_command"] == ui.SIDEBAR_COMMAND_TOGGLE

    app.radio[0].set_value("close")
    app.run()
    assert app.session_state["captured_open"] is False
    assert app.session_state["captured_command"] == ui.SIDEBAR_COMMAND_CLOSE

    app.session_state[ui.SIDEBAR_OPEN_KEY] = True
    app.radio[0].set_value("navigate")
    app.run()
    assert app.session_state["captured_open"] is True
    assert (
        app.session_state["captured_command"] == ui.SIDEBAR_COMMAND_CLOSE_MOBILE
    )


def test_navigate_to_requests_mobile_close_without_changing_desktop_state():
    """navigate_to deve apenas agendar o fechamento; o JS decide pelo viewport."""
    script = """
import streamlit as st
from src import ui_components as ui

st.set_page_config(initial_sidebar_state="auto")
st.session_state.setdefault(ui.SIDEBAR_OPEN_KEY, True)

if st.button("navegar"):
    original_rerun = st.rerun
    st.rerun = lambda: None
    try:
        ui.navigate_to(ui.PAGE_CLIENTS)
    finally:
        st.rerun = original_rerun

st.session_state["captured_page"] = st.session_state.get("current_page")
st.session_state["captured_open"] = st.session_state[ui.SIDEBAR_OPEN_KEY]
st.session_state["captured_command"] = st.session_state.get(ui.SIDEBAR_COMMAND_KEY)
"""
    app = AppTest.from_string(script)
    app.run()
    app.button[0].click()
    app.run()

    assert app.session_state["captured_page"] == ui.PAGE_CLIENTS
    assert app.session_state["captured_open"] is True
    assert app.session_state["captured_command"] == ui.SIDEBAR_COMMAND_CLOSE_MOBILE
