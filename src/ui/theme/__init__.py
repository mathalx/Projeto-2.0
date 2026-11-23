"""Tema visual central do ACNnorte.

Estrutura:

* :mod:`src.ui.theme.colors` — paleta de cores;
* :mod:`src.ui.theme.styles` — folhas de estilo (CSS);
* :mod:`src.ui.theme.components` — funções de aplicação do tema.
"""

from .components import apply_theme, inject_sidebar_css

__all__ = ["apply_theme", "inject_sidebar_css"]
