"""Funções reutilizáveis para aplicar o tema claro do ACNnorte.

Uso típico (uma única vez por execução, no início da aplicação)::

    from src.ui.theme.components import apply_theme

    apply_theme()

O tema nativo fica em ``.streamlit/config.toml``; estas funções injetam o CSS
complementar (classes próprias, menu lateral e superfícies de widgets).
"""

import streamlit as st

from .styles import get_global_css, get_sidebar_css

__all__ = ["apply_theme", "inject_sidebar_css"]


def inject_sidebar_css(mobile_breakpoint_px: int = 768) -> None:
    """Injeta o CSS exclusivo do menu lateral."""
    st.markdown(
        get_sidebar_css(mobile_breakpoint_px),
        unsafe_allow_html=True,
    )


def apply_theme(mobile_breakpoint_px: int = 768) -> None:
    """Aplica o tema claro completo (estilos globais + menu lateral)."""
    st.markdown(get_global_css(), unsafe_allow_html=True)
    inject_sidebar_css(mobile_breakpoint_px)
