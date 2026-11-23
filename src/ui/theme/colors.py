"""Paleta central do tema claro do ACNnorte.

Todos os estilos da aplicação devem referenciar estas constantes em vez de
repetir códigos hexadecimais. Os nomes em português/legado no final do arquivo
existem para manter compatibilidade com módulos que já importavam cores de
``src.ui_components``.
"""

# ---------------------------------------------------------------------------
# Fundos
# ---------------------------------------------------------------------------
COLOR_BG_MAIN = "#F3F4F6"        # Fundo principal da aplicação
COLOR_BG_FIELD = "#FFFFFF"       # Fundo dos campos de entrada
COLOR_BG_SECONDARY = "#E5E7EB"   # Fundo secundário / hover de listas
COLOR_BG_HOVER = "#F9FAFB"       # Hover suave de superfícies
COLOR_BG_SELECTED = "#D1D5DB"    # Item selecionado em listas/dropdowns
COLOR_WHITE = "#FFFFFF"

# ---------------------------------------------------------------------------
# Texto
# ---------------------------------------------------------------------------
COLOR_TEXT_PRIMARY = "#111827"     # Texto principal
COLOR_TEXT_SECONDARY = "#4B5563"   # Texto secundário
COLOR_TEXT_MUTED = "#6B7280"       # Placeholders e legendas

# ---------------------------------------------------------------------------
# Bordas
# ---------------------------------------------------------------------------
COLOR_BORDER = "#D1D5DB"
COLOR_BORDER_SOFT = "#E5E7EB"

# ---------------------------------------------------------------------------
# Identidade institucional (verde ACNnorte)
# ---------------------------------------------------------------------------
COLOR_PRIMARY = "#16834A"          # Verde institucional
COLOR_PRIMARY_HOVER = "#126B3C"    # Verde de hover
COLOR_LIGHT_GREEN = "#E8F2EA"      # Verde claro (fundos de destaque)
COLOR_SOFT_GREEN = "#A5CFAF"       # Verde suave (bordas/foco)
COLOR_DARK_GREEN = "#216B45"       # Verde escuro (legado)
COLOR_GRAPHITE = "#59636A"         # Cinza grafite (legado)

# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------
COLOR_DANGER = "#DC2626"           # Ações destrutivas / erros
COLOR_DANGER_HOVER = "#B91C1C"
COLOR_WARNING = "#B45309"
COLOR_SUCCESS = "#16834A"

# ---------------------------------------------------------------------------
# Aliases legados (compatibilidade)
# ---------------------------------------------------------------------------
COLOR_LIGHT_GRAY = COLOR_BG_MAIN
COLOR_BLACK = COLOR_TEXT_PRIMARY
