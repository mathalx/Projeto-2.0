"""Folhas de estilo do tema claro do ACNnorte.

O tema nativo (``.streamlit/config.toml``) já define as cores principais. Este
módulo concentra o CSS complementar em um único lugar:

* classes próprias da aplicação (``.acn-*``);
* botões do menu lateral (o Streamlit não expõe isso no ``config.toml``);
* uma camada de segurança para superfícies de widgets BaseWeb (dropdowns,
  calendários e seletores de horário), que podem ser renderizados em portal
  fora do container do widget.

Os seletores internos do Streamlit usados aqui estão documentados com a razão
de existirem. Sempre que possível, preferimos ``config.toml`` e atributos
estáveis (``data-testid`` e papéis ARIA do BaseWeb).
"""

from string import Template

from . import colors

# ---------------------------------------------------------------------------
# Tokens usados nas folhas de estilo
# ---------------------------------------------------------------------------
_TOKENS = {
    "BG_MAIN": colors.COLOR_BG_MAIN,
    "BG_FIELD": colors.COLOR_BG_FIELD,
    "BG_SECONDARY": colors.COLOR_BG_SECONDARY,
    "BG_HOVER": colors.COLOR_BG_HOVER,
    "BG_SELECTED": colors.COLOR_BG_SELECTED,
    "WHITE": colors.COLOR_WHITE,
    "TEXT_PRIMARY": colors.COLOR_TEXT_PRIMARY,
    "TEXT_SECONDARY": colors.COLOR_TEXT_SECONDARY,
    "TEXT_MUTED": colors.COLOR_TEXT_MUTED,
    "BORDER": colors.COLOR_BORDER,
    "BORDER_SOFT": colors.COLOR_BORDER_SOFT,
    "PRIMARY": colors.COLOR_PRIMARY,
    "PRIMARY_HOVER": colors.COLOR_PRIMARY_HOVER,
    "LIGHT_GREEN": colors.COLOR_LIGHT_GREEN,
    "SOFT_GREEN": colors.COLOR_SOFT_GREEN,
    "DARK_GREEN": colors.COLOR_DARK_GREEN,
    "DANGER": colors.COLOR_DANGER,
    "DANGER_HOVER": colors.COLOR_DANGER_HOVER,
}


# ---------------------------------------------------------------------------
# Estilos globais
# ---------------------------------------------------------------------------
_GLOBAL_CSS = Template(
    """
<style>
/* --------------------------------------------------------------------------
   Base e layout
   -------------------------------------------------------------------------- */
html, body {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
}
.stApp {
    background-color: $BG_MAIN;
    color: $TEXT_PRIMARY;
}
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1180px;
}
h1, h2, h3, h4 {
    font-weight: 700;
    letter-spacing: -0.2px;
    color: $TEXT_PRIMARY;
}
a { color: $PRIMARY; }
hr { border-color: $BORDER_SOFT; }
footer { visibility: hidden; }

/* --------------------------------------------------------------------------
   Campos de entrada — superfície clara
   Os data-testid são estáveis no Streamlit; os seletores [data-baseweb] cobrem
   o wrapper interno compartilhado por text/date/time/number/select.
   -------------------------------------------------------------------------- */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stDateInput"] input,
[data-testid="stTimeInput"] input,
[data-baseweb="input"],
[data-baseweb="base-input"],
[data-baseweb="select"] > div {
    background-color: $BG_FIELD !important;
    color: $TEXT_PRIMARY !important;
    -webkit-text-fill-color: $TEXT_PRIMARY !important;
    border-color: $BORDER !important;
}
[data-baseweb="input"] *,
[data-baseweb="base-input"] *,
[data-baseweb="select"] > div * {
    color: $TEXT_PRIMARY !important;
    -webkit-text-fill-color: $TEXT_PRIMARY !important;
}
input::placeholder,
textarea::placeholder {
    color: $TEXT_MUTED !important;
    -webkit-text-fill-color: $TEXT_MUTED !important;
    opacity: 1;
}
/* Ícones (calendário, relógio, seta do select) legíveis sobre fundo claro */
[data-baseweb="input"] svg,
[data-baseweb="select"] svg,
[data-testid="stDateInput"] svg,
[data-testid="stTimeInput"] svg {
    fill: $TEXT_SECONDARY !important;
    color: $TEXT_SECONDARY !important;
}
/* Foco visível e consistente */
[data-baseweb="input"]:focus-within,
[data-baseweb="base-input"]:focus-within,
[data-baseweb="select"] > div:focus-within {
    border-color: $PRIMARY !important;
    box-shadow: 0 0 0 2px rgba(22, 131, 74, 0.18) !important;
}

/* --------------------------------------------------------------------------
   Dropdowns / listas suspensas — estado aberto
   O BaseWeb renderiza o menu em um portal no fim do documento, portanto não é
   alcançado pelo container do widget. Os papéis ARIA são estáveis.
   -------------------------------------------------------------------------- */
[data-baseweb="popover"] > div,
[data-baseweb="menu"],
[data-baseweb="menu"] ul,
[role="listbox"] {
    background-color: $BG_FIELD !important;
    color: $TEXT_PRIMARY !important;
    border-color: $BORDER !important;
}
[role="option"],
[data-baseweb="menu"] li {
    background-color: $BG_FIELD !important;
    color: $TEXT_PRIMARY !important;
}
[role="option"] *,
[data-baseweb="menu"] li * {
    color: $TEXT_PRIMARY !important;
}
[role="option"]:hover,
[data-baseweb="menu"] li:hover {
    background-color: $BG_SECONDARY !important;
    color: $TEXT_PRIMARY !important;
}
[role="option"][aria-selected="true"],
[data-baseweb="menu"] li[aria-selected="true"] {
    background-color: $BG_SELECTED !important;
    color: $TEXT_PRIMARY !important;
    font-weight: 600 !important;
}

/* --------------------------------------------------------------------------
   Calendários e seletores de horário
   Também são renderizados em portal; mantemos as superfícies claras.
   -------------------------------------------------------------------------- */
[data-baseweb="calendar"],
[data-baseweb="datepicker"],
[data-baseweb="timepicker"] {
    background-color: $BG_FIELD !important;
    color: $TEXT_PRIMARY !important;
    border-color: $BORDER !important;
}
[data-baseweb="calendar"] *,
[data-baseweb="datepicker"] *,
[data-baseweb="timepicker"] * {
    color: $TEXT_PRIMARY !important;
}
[data-baseweb="calendar"] button,
[data-baseweb="timepicker"] button {
    background-color: transparent !important;
    color: $TEXT_PRIMARY !important;
}
[data-baseweb="calendar"] button:hover,
[data-baseweb="timepicker"] button:hover {
    background-color: $BG_SECONDARY !important;
}
[data-baseweb="calendar"] [aria-selected="true"] {
    background-color: $BG_SELECTED !important;
    color: $TEXT_PRIMARY !important;
}

/* Rótulos e legendas */
label,
.stSelectbox label,
.stTextInput label,
.stTextArea label,
.stDateInput label,
.stTimeInput label {
    font-weight: 600 !important;
    color: $TEXT_PRIMARY !important;
    font-size: 0.92rem;
}
[data-testid="stCaptionContainer"],
.stCaption {
    color: $TEXT_SECONDARY !important;
}

/* --------------------------------------------------------------------------
   Botões — ação principal em verde institucional
   -------------------------------------------------------------------------- */
.stButton > button,
.stDownloadButton > button,
.stFormSubmitButton > button {
    min-height: 46px;
    border-radius: 10px;
    font-weight: 600;
    font-size: 0.95rem;
    padding: 0.55rem 1rem;
    transition: background-color 0.15s ease, border-color 0.15s ease,
        box-shadow 0.15s ease;
}
.stButton > button p,
.stDownloadButton > button p,
.stFormSubmitButton > button p {
    color: inherit !important;
    font-weight: 600;
}
.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"],
.stDownloadButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"],
.stFormSubmitButton > button[data-testid="stBaseButton-primary"] {
    background-color: $PRIMARY !important;
    color: $WHITE !important;
    border: 1px solid $PRIMARY !important;
    box-shadow: 0 2px 6px rgba(22, 131, 74, 0.22);
}
.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primary"]:hover,
.stDownloadButton > button[kind="primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover,
.stFormSubmitButton > button[data-testid="stBaseButton-primary"]:hover {
    background-color: $PRIMARY_HOVER !important;
    border-color: $PRIMARY_HOVER !important;
    color: $WHITE !important;
}
.stButton > button[kind="primary"] p,
.stFormSubmitButton > button[kind="primary"] p,
.stDownloadButton > button[kind="primary"] p {
    color: $WHITE !important;
}
.stButton > button[kind="secondary"],
.stFormSubmitButton > button[kind="secondary"],
.stDownloadButton > button[kind="secondary"] {
    background-color: $BG_FIELD;
    color: $TEXT_PRIMARY;
    border: 1px solid $BORDER;
}
.stButton > button[kind="secondary"]:hover,
.stFormSubmitButton > button[kind="secondary"]:hover,
.stDownloadButton > button[kind="secondary"]:hover {
    background-color: $BG_HOVER;
    border-color: $PRIMARY;
}
.stButton > button:disabled { opacity: 0.5; }

/* Ações destrutivas de confirmação: mantêm indicação de perigo e não se
   confundem com os botões principais verdes. Os widgets usam chaves que
   começam com "confirm_del_" (ver views de clientes, fotos e usuários). */
[class*="st-key-confirm_del_"] button,
[class*="st-key-confirm_del_"] button[kind="primary"],
[class*="st-key-confirm_del_"] [data-testid="stBaseButton-primary"] {
    background-color: $DANGER !important;
    border: 1px solid $DANGER !important;
    color: $WHITE !important;
    box-shadow: none !important;
}
[class*="st-key-confirm_del_"] button p,
[class*="st-key-confirm_del_"] button span {
    color: $WHITE !important;
}
[class*="st-key-confirm_del_"] button:hover {
    background-color: $DANGER_HOVER !important;
    border-color: $DANGER_HOVER !important;
}

/* --------------------------------------------------------------------------
   Menu lateral — botões de navegação em cinza-claro
   -------------------------------------------------------------------------- */
[data-testid="stSidebar"] .stButton > button,
[data-testid="stSidebar"] .stButton > button[kind="primary"],
[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
    background-color: $BG_MAIN !important;
    background-image: none !important;
    color: $TEXT_PRIMARY !important;
    border: 1px solid $BG_SECONDARY !important;
    border-radius: 10px !important;
    box-shadow: none !important;
    opacity: 1 !important;
}
[data-testid="stSidebar"] .stButton > button *,
[data-testid="stSidebar"] .stButton > button p,
[data-testid="stSidebar"] .stButton > button span {
    background-color: transparent !important;
    background-image: none !important;
    color: $TEXT_PRIMARY !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] .stButton > button svg {
    fill: $TEXT_PRIMARY !important;
    stroke: $TEXT_PRIMARY !important;
}
[data-testid="stSidebar"] .stButton > button:hover,
[data-testid="stSidebar"] .stButton > button:active {
    background-color: $BG_SECONDARY !important;
    color: $TEXT_PRIMARY !important;
    border-color: $BORDER !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] .stButton > button:focus-visible {
    background-color: $BG_MAIN !important;
    color: $TEXT_PRIMARY !important;
    outline: 2px solid $PRIMARY !important;
    outline-offset: 2px;
    box-shadow: none !important;
}
/* Página ativa: fundo claro com barra verde à esquerda */
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background-color: $BG_MAIN !important;
    color: $TEXT_PRIMARY !important;
    box-shadow: inset 4px 0 0 0 $PRIMARY !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover,
[data-testid="stSidebar"] .stButton > button[kind="primary"]:active,
[data-testid="stSidebar"] .stButton > button[kind="primary"]:focus-visible {
    background-color: $BG_SECONDARY !important;
    color: $TEXT_PRIMARY !important;
    box-shadow: inset 4px 0 0 0 $PRIMARY !important;
}

/* --------------------------------------------------------------------------
   Componentes próprios (classes .acn-*)
   -------------------------------------------------------------------------- */
.acn-user-card {
    background: $LIGHT_GREEN;
    border: 1px solid $SOFT_GREEN;
    border-radius: 12px;
    padding: 10px 12px;
    margin: 4px 0 10px 0;
    font-size: 0.88rem;
    line-height: 1.35;
    color: $TEXT_PRIMARY;
}
.acn-user-card b { color: $TEXT_PRIMARY; }
.acn-user-name {
    font-size: 0.94rem;
    font-weight: 700;
    color: $TEXT_PRIMARY;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.acn-user-role {
    margin-top: 3px;
    font-size: 0.82rem;
    font-weight: 600;
    color: $DARK_GREEN;
}
.acn-user-caption {
    margin-top: 2px;
    font-size: 0.72rem;
    color: $TEXT_SECONDARY;
}
.acn-nav-label {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: $TEXT_SECONDARY;
    margin: 10px 0 4px 2px;
}
.acn-sync {
    display: flex;
    gap: 8px;
    align-items: flex-start;
    background: $LIGHT_GREEN;
    border: 1px solid $SOFT_GREEN;
    border-radius: 12px;
    padding: 10px 12px;
    font-size: 0.78rem;
    line-height: 1.35;
    color: $TEXT_PRIMARY;
    margin-top: 6px;
}
.acn-sync b { color: $TEXT_PRIMARY; }
.acn-sync-sub {
    color: $TEXT_SECONDARY;
    font-size: 0.72rem;
    margin-top: 2px;
}
.acn-sync-dot {
    width: 10px;
    height: 10px;
    margin-top: 3px;
    background: $PRIMARY;
    border-radius: 50%;
    flex: 0 0 auto;
    box-shadow: 0 0 0 3px rgba(22, 131, 74, 0.15);
}
.acn-section-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: $TEXT_PRIMARY;
    margin: 0.25rem 0 0.15rem 0;
}
.acn-section-subtitle {
    font-size: 0.88rem;
    color: $TEXT_SECONDARY;
    margin-bottom: 0.65rem;
}
.acn-banner {
    background: $LIGHT_GREEN;
    border: 1px solid $SOFT_GREEN;
    border-left: 4px solid $PRIMARY;
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 0.9rem;
    color: $TEXT_PRIMARY;
    margin-bottom: 0.6rem;
}
.acn-badge {
    display: inline-block;
    border: 1px solid;
    border-radius: 999px;
    padding: 2px 10px;
    font-size: 0.76rem;
    font-weight: 700;
    color: $TEXT_PRIMARY !important;
    white-space: nowrap;
}
.acn-empty {
    background: $BG_FIELD;
    border: 1px dashed $SOFT_GREEN;
    border-radius: 14px;
    padding: 26px 20px;
    text-align: center;
    margin: 8px 0 14px 0;
}
.acn-empty-icon { font-size: 2rem; line-height: 1.2; }
.acn-empty-title {
    font-weight: 700;
    color: $TEXT_PRIMARY;
    margin-top: 6px;
}
.acn-empty-hint {
    color: $TEXT_SECONDARY;
    font-size: 0.88rem;
    margin-top: 4px;
}
.acn-activity {
    background: $BG_FIELD;
    border: 1px solid $BORDER_SOFT;
    border-left: 4px solid $SOFT_GREEN;
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 8px;
    font-size: 0.9rem;
    color: $TEXT_PRIMARY;
}
.acn-activity b { color: $TEXT_PRIMARY; }
.acn-activity-meta {
    color: $TEXT_SECONDARY;
    font-size: 0.78rem;
}
.acn-photo-card {
    background: $BG_FIELD;
    border: 1px solid $BORDER_SOFT;
    border-radius: 14px;
    padding: 12px;
    margin-bottom: 12px;
}
.acn-photo-caption {
    font-weight: 600;
    color: $TEXT_PRIMARY;
    margin-top: 8px;
    font-size: 0.9rem;
}
.acn-photo-meta {
    color: $TEXT_SECONDARY;
    font-size: 0.76rem;
}

/* --------------------------------------------------------------------------
   Formulários, cartões, métricas e abas
   -------------------------------------------------------------------------- */
[data-testid="stForm"] {
    background-color: $BG_FIELD;
    border: 1px solid $BORDER_SOFT;
    border-radius: 14px;
    padding: 1.25rem 1.1rem;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}
.stTextArea textarea { min-height: 110px; }

[data-testid="stMetric"] {
    background: $BG_FIELD;
    border: 1px solid $BORDER_SOFT;
    border-left: 5px solid $PRIMARY;
    border-radius: 12px;
    padding: 14px 16px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}
[data-testid="stMetricLabel"] p {
    color: $TEXT_SECONDARY !important;
    font-weight: 600 !important;
    font-size: 0.88rem;
}
[data-testid="stMetricValue"] {
    color: $TEXT_PRIMARY !important;
    font-weight: 800 !important;
}
[data-testid="stMetricDelta"],
[data-testid="stMetricDelta"] * {
    color: $TEXT_SECONDARY !important;
    font-weight: 600 !important;
}
[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 14px !important; }

[data-testid="stExpander"] {
    background: $BG_FIELD;
    border: 1px solid $BORDER_SOFT;
    border-radius: 12px;
    overflow: hidden;
}
[data-testid="stExpander"] summary p {
    font-weight: 600 !important;
    color: $TEXT_PRIMARY !important;
}

.stProgress > div > div > div > div { background-color: $PRIMARY; }

[data-baseweb="tab-list"] { gap: 4px; }
[data-baseweb="tab"] { border-radius: 10px 10px 0 0; }
[data-baseweb="tab"] p {
    font-weight: 600 !important;
    color: $TEXT_PRIMARY !important;
}
[data-baseweb="tab-highlight"] { background-color: $PRIMARY; }

/* Abas internas em formato de pílulas (st.radio horizontal) */
[data-testid="stRadio"] [role="radiogroup"] {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}
[data-testid="stRadio"] label[data-baseweb="radio"] {
    background: $BG_FIELD;
    border: 1px solid $BORDER;
    border-radius: 999px;
    padding: 6px 14px;
    margin-right: 0;
}
[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {
    background: $LIGHT_GREEN;
    border-color: $PRIMARY;
}
[data-testid="stRadio"] label[data-baseweb="radio"] p {
    font-weight: 600 !important;
    color: $TEXT_PRIMARY !important;
}

/* Multiselect: chips em verde institucional com texto branco.
   O seletor inclui [data-baseweb="select"] para vencer a regra genérica de
   texto dos campos (que tem especificidade maior). */
[data-baseweb="select"] [data-baseweb="tag"],
[data-baseweb="tag"] {
    background-color: $PRIMARY !important;
    color: $WHITE !important;
}
[data-baseweb="select"] [data-baseweb="tag"] *,
[data-baseweb="tag"] * {
    color: $WHITE !important;
    fill: $WHITE !important;
}

/* --------------------------------------------------------------------------
   Responsividade
   -------------------------------------------------------------------------- */
@media (max-width: 1024px) {
    .block-container { padding-left: 1.2rem; padding-right: 1.2rem; }
}
@media (max-width: 768px) {
    .block-container {
        padding: 1rem 0.75rem 2.5rem 0.75rem;
        max-width: 100%;
    }
    h1 { font-size: 1.55rem !important; }
    h2 { font-size: 1.3rem !important; }
    h3 { font-size: 1.12rem !important; }
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; }
    .stButton > button,
    .stFormSubmitButton > button,
    .stDownloadButton > button {
        min-height: 50px;
        font-size: 1rem;
    }
    [data-testid="stForm"] { padding: 0.9rem 0.75rem; }
    .acn-section-title { font-size: 1.05rem; }
    .acn-user-card { font-size: 0.85rem; }
}
@media (hover: none) and (pointer: coarse) {
    .stButton > button,
    .stFormSubmitButton > button,
    .stDownloadButton > button {
        min-height: 50px;
    }
    [data-baseweb="select"] > div { min-height: 48px; }
    [data-testid="stRadio"] label[data-baseweb="radio"] { padding: 10px 16px; }
}
@media (prefers-reduced-motion: reduce) {
    * { transition: none !important; animation: none !important; }
}
</style>
"""
)


# ---------------------------------------------------------------------------
# Estilos exclusivos do menu lateral (ponte de abrir/fechar)
# ---------------------------------------------------------------------------
_SIDEBAR_CSS = Template(
    """
<style>
/* Mantém visíveis os controles nativos de abrir/fechar a sidebar. */
[data-testid="stHeader"],
[data-testid="stToolbar"] {
    visibility: visible !important;
}
[data-testid="stExpandSidebarButton"],
[data-testid="stExpandSidebarButton"] button,
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapseButton"] button {
    visibility: visible !important;
    opacity: 1 !important;
    pointer-events: auto !important;
    z-index: 1000003;
}
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {
    visibility: visible !important;
    opacity: 1 !important;
    pointer-events: auto !important;
}

/* Botão flutuante "☰ Menu" (key="sidebar_toggle") */
.st-key-sidebar_toggle {
    position: fixed !important;
    top: 0.55rem !important;
    right: 9.5rem !important;
    left: auto !important;
    z-index: 1000004 !important;
    width: auto !important;
    margin: 0 !important;
}
.st-key-sidebar_toggle [data-testid="stButton"] { width: auto; }
.st-key-sidebar_toggle button {
    min-width: 44px;
    min-height: 44px;
    padding: 0 14px;
    border-radius: 10px;
    border: 1px solid $PRIMARY;
    background-color: $PRIMARY;
    color: $WHITE;
    font-weight: 700;
    box-shadow: 0 2px 8px rgba(22, 131, 74, 0.28);
}
.st-key-sidebar_toggle button p {
    color: $WHITE !important;
    font-weight: 700 !important;
}
.st-key-sidebar_toggle button:hover {
    background-color: $PRIMARY_HOVER;
    border-color: $PRIMARY_HOVER;
}
.st-key-sidebar_toggle button:focus-visible {
    outline: 3px solid $SOFT_GREEN !important;
    outline-offset: 2px;
}

/* Botão "Fechar menu" dentro da sidebar */
[data-testid="stSidebar"] .st-key-sidebar_close_menu button,
[data-testid="stSidebar"] .st-key-sidebar_close_menu button:focus-visible {
    background-color: $WHITE !important;
    border: 1px solid $PRIMARY !important;
    color: $PRIMARY_HOVER !important;
    font-weight: 700 !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] .st-key-sidebar_close_menu button p,
[data-testid="stSidebar"] .st-key-sidebar_close_menu button span {
    color: $PRIMARY_HOVER !important;
    font-weight: 700 !important;
}
[data-testid="stSidebar"] .st-key-sidebar_close_menu button:hover {
    background-color: $LIGHT_GREEN !important;
    border-color: $PRIMARY_HOVER !important;
}

@media (max-width: ${MOBILE_BREAKPOINT}px) {
    .st-key-sidebar_toggle {
        top: 0.5rem !important;
        right: 7.5rem !important;
    }
    .st-key-sidebar_toggle button {
        min-width: 46px;
        min-height: 46px;
        padding: 0 12px;
    }
    [data-testid="stSidebar"] {
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.18);
    }
}
</style>
"""
)


def get_global_css() -> str:
    """Retorna o bloco ``<style>`` global do tema claro."""
    return _GLOBAL_CSS.substitute(_TOKENS)


def get_sidebar_css(mobile_breakpoint_px: int = 768) -> str:
    """Retorna o bloco ``<style>`` do menu lateral.

    Args:
        mobile_breakpoint_px: largura (px) abaixo da qual o menu é tratado
            como móvel. Deve corresponder ao breakpoint usado pela ponte JS.
    """
    tokens = dict(_TOKENS)
    tokens["MOBILE_BREAKPOINT"] = str(int(mobile_breakpoint_px))
    return _SIDEBAR_CSS.substitute(tokens)
