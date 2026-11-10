"""Componentes visuais compartilhados e identidade visual do ACNnorte."""

import html
import re
from datetime import datetime
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Identidade visual (paleta oficial)
# ---------------------------------------------------------------------------
COLOR_PRIMARY = "#16834A"       # Verde principal
COLOR_DARK_GREEN = "#216B45"    # Verde escuro
COLOR_SOFT_GREEN = "#A5CFAF"    # Verde suave
COLOR_LIGHT_GREEN = "#E8F2EA"   # Verde claro
COLOR_LIGHT_GRAY = "#F4F6F4"    # Cinza claro
COLOR_GRAPHITE = "#59636A"      # Cinza grafite
COLOR_BLACK = "#000000"         # Preto

# ---------------------------------------------------------------------------
# Logotipo oficial (assets/logo/acnnorte_logo.svg)
# ---------------------------------------------------------------------------
LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "logo" / "acnnorte_logo.svg"
LOGO_VIEWBOX_WIDTH = 520
LOGO_VIEWBOX_HEIGHT = 210

# Larguras sugeridas para manter compatibilidade com a API antiga (size=...).
LOGO_WIDTH_PRESETS = {
    "small": 140,
    "normal": 200,
    "medium": 220,
    "large": 300,
}


# ---------------------------------------------------------------------------
# Chaves de navegação (compartilhadas entre main, views e atalhos)
# ---------------------------------------------------------------------------
PAGE_FORM = "Formulário de Campo"
PAGE_DASHBOARD = "Painel Inicial"
PAGE_CLIENTS = "Clientes"
PAGE_VISITS = "Visitas Técnicas"
PAGE_PHOTOS = "Fotografias"
PAGE_REPORTS = "Relatórios & Exportação"
PAGE_PROFILE = "Alterar Senha"
PAGE_ADMIN = "Gerenciar Usuários"

NAV_ITEMS = [
    (PAGE_FORM, "📝", "Formulário principal de avaliação em campo"),
    (PAGE_DASHBOARD, "🏠", "Visão geral e indicadores"),
    (PAGE_CLIENTS, "👥", "Cadastro e consulta de empresas"),
    (PAGE_VISITS, "📋", "Visitas e formulários técnicos"),
    (PAGE_PHOTOS, "📷", "Fotografias das visitas e galeria do dia"),
    (PAGE_REPORTS, "📊", "Relatórios PDF e planilhas"),
    (PAGE_PROFILE, "🔑", "Alterar sua senha"),
    (PAGE_ADMIN, "⚙️", "Gestão de usuários (administrador)"),
]

CLIENTS_TAB_LIST = "📋 Lista de Clientes"
CLIENTS_TAB_NEW = "➕ Cadastrar Cliente"
CLIENTS_TAB_CONSULT = "🔍 Consultar & Histórico"
CLIENTS_TABS = [CLIENTS_TAB_LIST, CLIENTS_TAB_NEW, CLIENTS_TAB_CONSULT]

VISITS_TAB_LIST = "📋 Lista de Visitas"
VISITS_TAB_NEW = "➕ Iniciar Visita"
VISITS_TAB_FILL = "✍️ Preencher Visita"
VISITS_TABS = [VISITS_TAB_LIST, VISITS_TAB_NEW, VISITS_TAB_FILL]

PHOTOS_TAB_ADD = "📷 Adicionar Fotografia"
PHOTOS_TAB_GALLERY = "🖼️ Galeria da Visita"
PHOTOS_TAB_TODAY = "📅 Galeria do Dia"
PHOTOS_TABS = [PHOTOS_TAB_ADD, PHOTOS_TAB_GALLERY, PHOTOS_TAB_TODAY]


PENDING_STATE_KEY = "_pending_state"


def set_pending_state(**state):
    """Agenda valores de session_state para antes dos widgets do próximo run."""
    pending = dict(st.session_state.get(PENDING_STATE_KEY, {}))
    pending.update(state)
    st.session_state[PENDING_STATE_KEY] = pending


def apply_pending_state():
    """Aplica valores agendados antes da criação de qualquer widget."""
    pending = st.session_state.pop(PENDING_STATE_KEY, None)
    if pending:
        for key, value in pending.items():
            st.session_state[key] = value


def navigate_to(page: str, **extra_state):
    """Troca a página atual (e opcionalmente a aba interna) e recarrega a tela."""
    set_pending_state(**extra_state)
    st.session_state["current_page"] = page
    st.rerun()


def record_sync():
    """Registra o horário da última gravação local bem-sucedida."""
    st.session_state["last_sync_at"] = datetime.now().strftime("%H:%M:%S")


@st.cache_data(show_spinner=False)
def _read_logo_svg(path: str, modified_at: float):
    """Lê o SVG oficial (com cache invalidado pela data de modificação)."""
    try:
        return Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _load_acnnorte_logo():
    """Carrega o arquivo do logotipo, retornando None quando indisponível."""
    try:
        modified_at = LOGO_PATH.stat().st_mtime
    except OSError:
        return None
    return _read_logo_svg(str(LOGO_PATH), modified_at)


def _prepare_inline_svg(svg: str, width: int) -> str:
    """Remove declarações e aplica a largura desejada ao SVG para uso inline."""
    svg = re.sub(r"<\?xml[^>]*\?>", "", svg, count=1)
    svg = re.sub(r"<!DOCTYPE[^>]*>", "", svg, count=1, flags=re.IGNORECASE)
    height = round(width * LOGO_VIEWBOX_HEIGHT / LOGO_VIEWBOX_WIDTH)

    def _rewrite(match: re.Match) -> str:
        tag = match.group(0)
        closing = "/>" if tag.endswith("/>") else ">"
        inner = tag[: -len(closing)]
        inner = re.sub(r'\s(?:width|height)="[^"]*"', "", inner)
        return (
            f'{inner} width="{width}" height="{height}" '
            f'style="width:{width}px;max-width:100%;height:auto;"{closing}'
        )

    return re.sub(r"<svg\b[^>]*>", _rewrite, svg, count=1)


def render_acnnorte_logo(
    width: int = 200,
    subtitle: str = None,
    align: str = "center",
    size: str = None,
):
    """Exibe o logotipo vetorial oficial da ACNnorte com fallback seguro.

    Args:
        width: largura em pixels do logotipo (padrão 200).
        subtitle: texto opcional exibido abaixo da marca.
        align: alinhamento horizontal ("left", "center" ou "right").
        size: presets legados ("small", "normal", "medium", "large").
    """
    # Compatibilidade com a API anterior: render_acnnorte_logo("large")
    if isinstance(width, str):
        size, width = width, LOGO_WIDTH_PRESETS.get(width, 200)
    if size is not None:
        width = LOGO_WIDTH_PRESETS.get(size, width)

    try:
        width = max(40, int(width))
    except (TypeError, ValueError):
        width = 200

    align_css = align if align in {"left", "center", "right"} else "center"

    svg = _load_acnnorte_logo()
    if svg:
        markup = _prepare_inline_svg(svg, width)
    else:
        # Fallback seguro: marca textual com a paleta institucional.
        font_size = max(1.1, round(width / 110, 2))
        markup = (
            f'<span style="font-family: \'Segoe UI\', Arial, sans-serif; '
            f'font-size: {font_size}rem; font-weight: 800; letter-spacing: -0.5px;">'
            f'<span style="color: {COLOR_PRIMARY};">ACN</span>'
            f'<span style="color: {COLOR_GRAPHITE};">norte</span></span>'
        )

    subtitle_html = ""
    if subtitle:
        subtitle_html = (
            f'<div style="color: {COLOR_BLACK}; font-size: 0.95rem; font-weight: 500; '
            f'margin-top: 6px;">{html.escape(str(subtitle))}</div>'
        )

    st.markdown(
        f'<div style="text-align: {align_css}; margin-bottom: 0.5rem;">{markup}{subtitle_html}</div>',
        unsafe_allow_html=True,
    )


def render_section_title(title: str, description: str = None, icon: str = None):
    """Título de seção padronizado, com descrição opcional."""
    icon_html = f'<span style="margin-right: 8px;">{icon}</span>' if icon else ""
    html_title = (
        f'<div class="acn-section-title">{icon_html}{html.escape(title)}</div>'
    )
    if description:
        html_title += f'<div class="acn-section-subtitle">{html.escape(description)}</div>'
    st.markdown(html_title, unsafe_allow_html=True)


def render_empty_state(icon: str, title: str, hint: str = None):
    """Bloco visual para listas vazias, evitando telas sem orientação."""
    hint_html = f'<div class="acn-empty-hint">{html.escape(hint)}</div>' if hint else ""
    st.markdown(
        f"""
        <div class="acn-empty">
            <div class="acn-empty-icon">{icon}</div>
            <div class="acn-empty-title">{html.escape(title)}</div>
            {hint_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_badge(status: str) -> str:
    """Retorna o HTML de um selo de status (texto sempre preto)."""
    borders = {
        "Finalizada": COLOR_PRIMARY,
        "Em Andamento": COLOR_DARK_GREEN,
        "Rascunho": COLOR_GRAPHITE,
    }
    border = borders.get(status, COLOR_GRAPHITE)
    background = COLOR_LIGHT_GREEN if status == "Finalizada" else COLOR_LIGHT_GRAY
    return (
        f'<span class="acn-badge" style="background:{background}; border-color:{border};">'
        f"{html.escape(str(status))}</span>"
    )


def render_sync_indicator():
    """Indicador discreto do estado de sincronização (armazenamento local)."""
    last_sync = st.session_state.get("last_sync_at")
    if last_sync:
        main_text = f"Última gravação às {last_sync}"
    else:
        main_text = "Dados carregados do armazenamento local"
    st.markdown(
        f"""
        <div class="acn-sync">
            <span class="acn-sync-dot"></span>
            <div>
                <b>{html.escape(main_text)}</b>
                <div class="acn-sync-sub">Salvo neste dispositivo — funciona sem internet</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def info_banner(message: str, icon: str = "ℹ️"):
    """Aviso informativo padronizado (texto simples, sem jargão técnico)."""
    st.markdown(
        f'<div class="acn-banner">{icon} {html.escape(message)}</div>',
        unsafe_allow_html=True,
    )


def set_flash(message: str, level: str = "success"):
    """Guarda uma mensagem para ser exibida após o próximo recarregamento."""
    st.session_state["flash_message"] = {"level": level, "message": message}


def render_flash():
    """Exibe e descarta a mensagem pendente (sobrevive à navegação)."""
    flash = st.session_state.pop("flash_message", None)
    if not flash:
        return
    level = flash.get("level", "info")
    renderer = {
        "success": st.success,
        "info": st.info,
        "warning": st.warning,
        "error": st.error,
    }.get(level, st.info)
    renderer(flash.get("message", ""))


def apply_global_styles():
    """Aplica o design system do ACNnorte a todas as telas."""
    st.markdown(
        f"""
        <style>
        /* ------------------------------------------------------------------
           Base
        ------------------------------------------------------------------ */
        html, body, [class*="css"] {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
        }}
        .stApp {{
            background-color: {COLOR_LIGHT_GRAY};
            color: {COLOR_BLACK};
        }}
        .stApp p, .stApp li, .stApp span, .stApp label,
        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
        .stApp strong, .stApp b {{
            color: {COLOR_BLACK};
        }}
        .block-container {{
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1180px;
        }}
        h1, h2, h3, h4 {{ font-weight: 700; letter-spacing: -0.2px; }}
        a {{ color: {COLOR_PRIMARY}; }}
        hr {{ border-color: #E1E6E2; }}
        #MainMenu {{ visibility: visible; }}
        footer {{ visibility: hidden; }}

        /* ------------------------------------------------------------------
           Sidebar
        ------------------------------------------------------------------ */
        [data-testid="stSidebar"] {{
            background-color: #FFFFFF;
            border-right: 1px solid #E1E6E2;
        }}
        [data-testid="stSidebar"] .block-container {{
            padding-top: 1.25rem;
        }}
        .acn-user-card {{
            background: {COLOR_LIGHT_GREEN};
            border: 1px solid #CDE4D3;
            border-radius: 12px;
            padding: 10px 12px;
            margin: 4px 0 10px 0;
            font-size: 0.88rem;
            line-height: 1.35;
            color: {COLOR_BLACK};
        }}
        .acn-user-card b {{ color: {COLOR_BLACK}; }}
        .acn-user-name {{
            font-size: 0.94rem;
            font-weight: 700;
            color: {COLOR_BLACK};
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .acn-user-role {{
            margin-top: 3px;
            font-size: 0.82rem;
            font-weight: 600;
            color: {COLOR_DARK_GREEN};
        }}
        .acn-user-caption {{
            margin-top: 2px;
            font-size: 0.72rem;
            color: {COLOR_BLACK};
        }}
        [data-testid="stSidebar"] .stButton > button p {{
            font-size: 0.88rem;
            line-height: 1.25;
        }}
        .acn-nav-label {{
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: {COLOR_BLACK};
            margin: 10px 0 4px 2px;
        }}
        .acn-sync {{
            display: flex;
            gap: 8px;
            align-items: flex-start;
            background: {COLOR_LIGHT_GREEN};
            border: 1px solid #CDE4D3;
            border-radius: 12px;
            padding: 10px 12px;
            font-size: 0.78rem;
            line-height: 1.35;
            color: {COLOR_BLACK};
            margin-top: 6px;
        }}
        .acn-sync b {{ color: {COLOR_BLACK}; }}
        .acn-sync-sub {{ color: {COLOR_BLACK}; font-size: 0.72rem; margin-top: 2px; }}
        .acn-sync-dot {{
            width: 10px; height: 10px; margin-top: 3px;
            background: {COLOR_PRIMARY};
            border-radius: 50%;
            flex: 0 0 auto;
            box-shadow: 0 0 0 3px rgba(22, 131, 74, 0.15);
        }}

        /* ------------------------------------------------------------------
           Botões (área de toque confortável)
        ------------------------------------------------------------------ */
        .stButton > button,
        .stDownloadButton > button,
        .stFormSubmitButton > button {{
            min-height: 46px;
            border-radius: 10px;
            font-weight: 600;
            font-size: 0.95rem;
            padding: 0.55rem 1rem;
            transition: background-color 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
        }}
        .stButton > button p, .stDownloadButton > button p, .stFormSubmitButton > button p {{
            color: inherit !important;
            font-weight: 600;
        }}
        .stButton > button[kind="primary"],
        .stFormSubmitButton > button[kind="primary"],
        .stDownloadButton > button[kind="primary"] {{
            background-color: {COLOR_PRIMARY};
            color: #FFFFFF;
            border: 1px solid {COLOR_PRIMARY};
            box-shadow: 0 2px 6px rgba(22, 131, 74, 0.22);
        }}
        .stButton > button[kind="primary"]:hover,
        .stFormSubmitButton > button[kind="primary"]:hover,
        .stDownloadButton > button[kind="primary"]:hover {{
            background-color: {COLOR_DARK_GREEN};
            border-color: {COLOR_DARK_GREEN};
            color: #FFFFFF;
        }}
        .stButton > button[kind="secondary"],
        .stFormSubmitButton > button[kind="secondary"],
        .stDownloadButton > button[kind="secondary"] {{
            background-color: #FFFFFF;
            color: {COLOR_BLACK};
            border: 1px solid #CDD5D0;
        }}
        .stButton > button[kind="secondary"]:hover,
        .stFormSubmitButton > button[kind="secondary"]:hover,
        .stDownloadButton > button[kind="secondary"]:hover {{
            border-color: {COLOR_PRIMARY};
            background-color: {COLOR_LIGHT_GREEN};
        }}
        .stButton > button:disabled {{
            opacity: 0.5;
        }}

        /* ------------------------------------------------------------------
           Menu lateral: botões padronizados em cinza-claro
        ------------------------------------------------------------------ */
        [data-testid="stSidebar"] .stButton > button,
        [data-testid="stSidebar"] .stButton > button[kind="primary"],
        [data-testid="stSidebar"] .stButton > button[kind="secondary"],
        [data-testid="stSidebar"] [data-testid="stBaseButton-primary"],
        [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {{
            background-color: #F3F4F6 !important;
            background-image: none !important;
            color: #111827 !important;
            border: 1px solid #E5E7EB !important;
            border-radius: 10px !important;
            box-shadow: none !important;
            opacity: 1 !important;
        }}
        [data-testid="stSidebar"] .stButton > button *,
        [data-testid="stSidebar"] .stButton > button p,
        [data-testid="stSidebar"] .stButton > button span,
        [data-testid="stSidebar"] .stButton > button div {{
            background-color: transparent !important;
            background-image: none !important;
            color: #111827 !important;
            box-shadow: none !important;
        }}
        [data-testid="stSidebar"] .stButton > button svg {{
            fill: #111827 !important;
            stroke: #111827 !important;
        }}
        [data-testid="stSidebar"] .stButton > button:hover,
        [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover,
        [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover,
        [data-testid="stSidebar"] [data-testid="stBaseButton-primary"]:hover,
        [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {{
            background-color: #E5E7EB !important;
            color: #111827 !important;
            border-color: #D1D5DB !important;
            box-shadow: none !important;
        }}
        [data-testid="stSidebar"] .stButton > button:active,
        [data-testid="stSidebar"] .stButton > button[kind="primary"]:active,
        [data-testid="stSidebar"] .stButton > button[kind="secondary"]:active {{
            background-color: #E5E7EB !important;
            color: #111827 !important;
            border-color: #D1D5DB !important;
            box-shadow: none !important;
        }}
        [data-testid="stSidebar"] .stButton > button:focus-visible,
        [data-testid="stSidebar"] .stButton > button[kind="primary"]:focus-visible,
        [data-testid="stSidebar"] .stButton > button[kind="secondary"]:focus-visible {{
            background-color: #F3F4F6 !important;
            color: #111827 !important;
            outline: 2px solid {COLOR_PRIMARY} !important;
            outline-offset: 2px;
            box-shadow: none !important;
        }}
        /* Item selecionado: mesmo fundo cinza, com detalhe verde discreto */
        [data-testid="stSidebar"] .stButton > button[kind="primary"],
        [data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {{
            background-color: #F3F4F6 !important;
            color: #111827 !important;
            box-shadow: inset 4px 0 0 0 {COLOR_PRIMARY} !important;
        }}
        [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover,
        [data-testid="stSidebar"] [data-testid="stBaseButton-primary"]:hover,
        [data-testid="stSidebar"] .stButton > button[kind="primary"]:active,
        [data-testid="stSidebar"] .stButton > button[kind="primary"]:focus-visible {{
            background-color: #E5E7EB !important;
            color: #111827 !important;
            box-shadow: inset 4px 0 0 0 {COLOR_PRIMARY} !important;
        }}

        /* ------------------------------------------------------------------
           Formulários e campos
        ------------------------------------------------------------------ */
        [data-testid="stForm"] {{
            background-color: #FFFFFF;
            border: 1px solid #E1E6E2;
            border-radius: 14px;
            padding: 1.25rem 1.1rem;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
        }}
        .stTextInput > div > div > input,
        .stTextArea textarea,
        .stNumberInput input,
        .stDateInput input {{
            border-radius: 10px;
            border: 1px solid #CDD5D0;
            padding: 0.6rem 0.8rem;
            font-size: 1rem;
            min-height: 44px;
            background-color: #FFFFFF;
            color: {COLOR_BLACK};
        }}
        .stTextArea textarea {{ min-height: 110px; }}
        .stTextInput > div > div > input:focus,
        .stTextArea textarea:focus {{
            border-color: {COLOR_PRIMARY};
            box-shadow: 0 0 0 3px rgba(22, 131, 74, 0.15);
        }}
        [data-baseweb="select"] > div {{
            border-radius: 10px;
            min-height: 44px;
            border-color: #CDD5D0;
        }}
        label, .stSelectbox label, .stTextInput label, .stTextArea label {{
            font-weight: 600 !important;
            color: {COLOR_BLACK} !important;
            font-size: 0.92rem;
        }}
        [data-testid="stCaptionContainer"], .stCaption {{
            color: {COLOR_BLACK} !important;
        }}

        /* Abas internas em formato de pílulas */
        [data-testid="stRadio"] [role="radiogroup"] {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        [data-testid="stRadio"] label[data-baseweb="radio"] {{
            background: #FFFFFF;
            border: 1px solid #CDD5D0;
            border-radius: 999px;
            padding: 6px 14px;
            margin-right: 0;
        }}
        [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {{
            background: {COLOR_LIGHT_GREEN};
            border-color: {COLOR_PRIMARY};
        }}
        [data-testid="stRadio"] label[data-baseweb="radio"] p {{
            font-weight: 600 !important;
            color: {COLOR_BLACK} !important;
        }}

        /* ------------------------------------------------------------------
           Cartões, métricas e estados
        ------------------------------------------------------------------ */
        [data-testid="stMetric"] {{
            background: #FFFFFF;
            border: 1px solid #E1E6E2;
            border-left: 5px solid {COLOR_PRIMARY};
            border-radius: 12px;
            padding: 14px 16px;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
        }}
        [data-testid="stMetricLabel"] p {{
            color: {COLOR_BLACK} !important;
            font-weight: 600 !important;
            font-size: 0.88rem;
        }}
        [data-testid="stMetricValue"] {{
            color: {COLOR_BLACK} !important;
            font-weight: 800 !important;
        }}
        [data-testid="stMetricDelta"] {{
            color: {COLOR_BLACK} !important;
            font-weight: 600 !important;
        }}
        [data-testid="stMetricDelta"] * {{
            color: {COLOR_BLACK} !important;
        }}
        [data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 14px !important;
        }}
        .acn-section-title {{
            font-size: 1.15rem;
            font-weight: 700;
            color: {COLOR_BLACK};
            margin: 0.25rem 0 0.15rem 0;
        }}
        .acn-section-subtitle {{
            font-size: 0.88rem;
            color: {COLOR_BLACK};
            margin-bottom: 0.65rem;
        }}
        .acn-banner {{
            background: {COLOR_LIGHT_GREEN};
            border: 1px solid #CDE4D3;
            border-left: 4px solid {COLOR_PRIMARY};
            border-radius: 10px;
            padding: 10px 14px;
            font-size: 0.9rem;
            color: {COLOR_BLACK};
            margin-bottom: 0.6rem;
        }}
        .acn-badge {{
            display: inline-block;
            border: 1px solid;
            border-radius: 999px;
            padding: 2px 10px;
            font-size: 0.76rem;
            font-weight: 700;
            color: {COLOR_BLACK} !important;
            white-space: nowrap;
        }}
        .acn-empty {{
            background: #FFFFFF;
            border: 1px dashed #C6D2CA;
            border-radius: 14px;
            padding: 26px 20px;
            text-align: center;
            margin: 8px 0 14px 0;
        }}
        .acn-empty-icon {{ font-size: 2rem; line-height: 1.2; }}
        .acn-empty-title {{ font-weight: 700; color: {COLOR_BLACK}; margin-top: 6px; }}
        .acn-empty-hint {{ color: {COLOR_BLACK}; font-size: 0.88rem; margin-top: 4px; }}
        .acn-activity {{
            background: #FFFFFF;
            border: 1px solid #E1E6E2;
            border-left: 4px solid {COLOR_SOFT_GREEN};
            border-radius: 10px;
            padding: 10px 14px;
            margin-bottom: 8px;
            font-size: 0.9rem;
            color: {COLOR_BLACK};
        }}
        .acn-activity b {{ color: {COLOR_BLACK}; }}
        .acn-activity-meta {{ color: {COLOR_BLACK}; font-size: 0.78rem; }}
        .acn-photo-card {{
            background: #FFFFFF;
            border: 1px solid #E1E6E2;
            border-radius: 14px;
            padding: 12px;
            margin-bottom: 12px;
        }}
        .acn-photo-caption {{
            font-weight: 600;
            color: {COLOR_BLACK};
            margin-top: 8px;
            font-size: 0.9rem;
        }}
        .acn-photo-meta {{ color: {COLOR_BLACK}; font-size: 0.76rem; }}

        /* Expanders */
        [data-testid="stExpander"] {{
            background: #FFFFFF;
            border: 1px solid #E1E6E2;
            border-radius: 12px;
            overflow: hidden;
        }}
        [data-testid="stExpander"] summary p {{
            font-weight: 600 !important;
            color: {COLOR_BLACK} !important;
        }}

        /* Barra de progresso */
        .stProgress > div > div > div > div {{
            background-color: {COLOR_PRIMARY};
        }}

        /* Abas do Streamlit */
        [data-baseweb="tab-list"] {{ gap: 4px; }}
        [data-baseweb="tab"] {{
            border-radius: 10px 10px 0 0;
        }}
        [data-baseweb="tab"] p {{
            font-weight: 600 !important;
            color: {COLOR_BLACK} !important;
        }}
        [data-baseweb="tab-highlight"] {{ background-color: {COLOR_PRIMARY}; }}

        /* ------------------------------------------------------------------
           Formulário de campo
        ------------------------------------------------------------------ */
        .acn-field-header {{
            background: #FFFFFF;
            border: 1px solid #E1E6E2;
            border-radius: 14px;
            padding: 14px 16px;
            margin-bottom: 12px;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
        }}
        .acn-weather-card {{
            background: {COLOR_LIGHT_GREEN};
            border: 1px solid #CDE4D3;
            border-left: 5px solid {COLOR_PRIMARY};
            border-radius: 12px;
            padding: 12px 14px;
            color: {COLOR_BLACK};
            font-size: 0.9rem;
        }}
        .acn-weather-card b {{ color: {COLOR_BLACK}; }}
        .acn-worker-photo {{
            border: 2px solid {COLOR_SOFT_GREEN};
            border-radius: 12px;
            padding: 6px;
            background: #FFFFFF;
        }}
        .acn-chip-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 4px;
        }}
        .acn-chip {{
            display: inline-block;
            background: {COLOR_LIGHT_GREEN};
            border: 1px solid {COLOR_PRIMARY};
            border-radius: 999px;
            padding: 3px 10px;
            font-size: 0.78rem;
            font-weight: 600;
            color: {COLOR_BLACK};
        }}

        /* Botão flutuante de acesso rápido à galeria do dia */
        .st-key-gallery_fab {{
            position: fixed;
            right: 22px;
            bottom: 22px;
            z-index: 99999;
            width: auto !important;
            background: transparent;
        }}
        .st-key-gallery_fab .stButton > button {{
            border-radius: 999px;
            background-color: {COLOR_PRIMARY};
            color: #FFFFFF;
            border: 1px solid {COLOR_PRIMARY};
            box-shadow: 0 6px 18px rgba(22, 131, 74, 0.35);
            min-height: 52px;
            padding: 0.6rem 1.2rem;
            font-weight: 700;
        }}
        .st-key-gallery_fab .stButton > button:hover {{
            background-color: {COLOR_DARK_GREEN};
            border-color: {COLOR_DARK_GREEN};
            color: #FFFFFF;
        }}

        /* ------------------------------------------------------------------
           Responsividade (computador, tablet e celular)
        ------------------------------------------------------------------ */
        @media (max-width: 1024px) {{
            .block-container {{ padding-left: 1.2rem; padding-right: 1.2rem; }}
        }}
        @media (max-width: 768px) {{
            .block-container {{
                padding: 1rem 0.75rem 2.5rem 0.75rem;
                max-width: 100%;
            }}
            h1 {{ font-size: 1.55rem !important; }}
            h2 {{ font-size: 1.3rem !important; }}
            h3 {{ font-size: 1.12rem !important; }}
            [data-testid="stMetricValue"] {{ font-size: 1.5rem !important; }}
            .stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {{
                min-height: 50px;
                font-size: 1rem;
            }}
            [data-testid="stForm"] {{ padding: 0.9rem 0.75rem; }}
            .acn-section-title {{ font-size: 1.05rem; }}
            .acn-user-card {{ font-size: 0.85rem; }}
        }}
        @media (hover: none) and (pointer: coarse) {{
            .stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {{
                min-height: 50px;
            }}
            [data-baseweb="select"] > div {{ min-height: 48px; }}
            [data-testid="stRadio"] label[data-baseweb="radio"] {{ padding: 10px 16px; }}
        }}
        @media (prefers-reduced-motion: reduce) {{
            * {{ transition: none !important; animation: none !important; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
