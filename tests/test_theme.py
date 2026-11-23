"""Garante que o tema claro permaneça centralizado e sem superfícies escuras."""

import tomllib
from pathlib import Path

from src import ui_components
from src.ui.theme import colors
from src.ui.theme.styles import get_global_css, get_sidebar_css

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / ".streamlit" / "config.toml"


def test_streamlit_theme_config_uses_light_palette():
    config = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    theme = config["theme"]

    assert theme["base"] == "light"
    assert theme["primaryColor"] == "#16834A"
    assert theme["backgroundColor"] == "#F3F4F6"
    assert theme["secondaryBackgroundColor"] == "#FFFFFF"
    assert theme["textColor"] == "#111827"
    assert theme["borderColor"] == "#D1D5DB"

    sidebar = theme["sidebar"]
    assert sidebar["backgroundColor"] == "#FFFFFF"
    assert sidebar["textColor"] == "#111827"


def test_colors_module_matches_institutional_palette():
    assert colors.COLOR_PRIMARY == "#16834A"
    assert colors.COLOR_PRIMARY_HOVER == "#126B3C"
    assert colors.COLOR_BG_MAIN == "#F3F4F6"
    assert colors.COLOR_BG_FIELD == "#FFFFFF"
    assert colors.COLOR_TEXT_PRIMARY == "#111827"
    assert colors.COLOR_BORDER == "#D1D5DB"


def test_ui_components_keeps_legacy_color_exports():
    assert ui_components.COLOR_PRIMARY == colors.COLOR_PRIMARY
    assert ui_components.COLOR_LIGHT_GRAY == colors.COLOR_BG_MAIN
    assert ui_components.COLOR_BLACK == colors.COLOR_TEXT_PRIMARY


def test_global_css_covers_widgets_and_has_no_dark_surfaces():
    css = get_global_css()

    # Campos, dropdowns (fechado/aberto), calendário e horário.
    for selector in (
        '[data-testid="stTextInput"] input',
        '[data-testid="stDateInput"] input',
        '[data-testid="stTimeInput"] input',
        '[data-baseweb="select"] > div',
        '[data-baseweb="popover"]',
        '[role="listbox"]',
        '[role="option"]',
        '[data-baseweb="calendar"]',
    ):
        assert selector in css

    # Ações principais em verde institucional.
    assert "background-color: #16834A !important" in css
    assert "background-color: #126B3C !important" in css

    # Nenhum fundo preto/escuro indesejado.
    for dark in ("#000000", "#111111", "#1a1a1a", "#262626", "#333333"):
        assert dark not in css.lower()


def test_sidebar_css_is_delegated_and_keeps_native_controls():
    css = get_sidebar_css(768)

    assert '[data-testid="stExpandSidebarButton"]' in css
    assert '[data-testid="stSidebarCollapseButton"]' in css
    assert ".st-key-sidebar_toggle" in css
    assert ".st-key-sidebar_close_menu" in css
    assert "max-width: 768px" in css
    assert css == ui_components.sidebar_css()


def test_theme_is_applied_through_single_entry_point():
    # apply_global_styles continua existindo para compatibilidade e delega ao tema.
    assert callable(ui_components.apply_global_styles)
    assert callable(ui_components.inject_sidebar_css)
