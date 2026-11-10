"""Novo fluxo isolado de inspeções de campo (Layout ACN Norte).

Ponto de entrada do pacote:
- ``render_field_inspection_view``: formulário principal;
- ``render_acn_sidebar``: menu lateral em blocos;
- utilitários de serviços/documentos para testes e reuso.
"""

from .sidebar import render_acn_sidebar
from .view import render_field_inspection_view

__all__ = ["render_acn_sidebar", "render_field_inspection_view"]
