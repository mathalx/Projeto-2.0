"""Componentes visuais compartilhados e identidade visual do ACNnorte."""

import base64
import html
import json
import re
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Identidade visual / tema claro (centralizado em src.ui.theme)
#
# As constantes continuam sendo exportadas por este módulo para manter
# compatibilidade, mas a fonte de verdade é ``src/ui/theme/colors.py``.
# ---------------------------------------------------------------------------
from src.ui.theme.colors import (  # noqa: E402
    COLOR_BLACK,
    COLOR_DARK_GREEN,
    COLOR_GRAPHITE,
    COLOR_LIGHT_GRAY,
    COLOR_LIGHT_GREEN,
    COLOR_PRIMARY,
    COLOR_SOFT_GREEN,
)

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
PAGE_DASHBOARD = "Painel Inicial"
PAGE_CLIENTS = "Clientes"
PAGE_VISITS = "Visitas Técnicas"
PAGE_PHOTOS = "Fotografias"
PAGE_REPORTS = "Relatórios & Exportação"
PAGE_PROFILE = "Alterar Senha"
PAGE_ADMIN = "Gerenciar Usuários"

NAV_ITEMS = [
    (PAGE_DASHBOARD, "🏠", "Visão geral e indicadores"),
    (PAGE_CLIENTS, "👥", "Cadastro e consulta de empresas"),
    (PAGE_VISITS, "🧾", "Visitas e formulários técnicos"),
    (PAGE_PHOTOS, "📷", "Fotografias das visitas"),
    (PAGE_REPORTS, "📊", "Relatórios PDF e planilhas"),
    (PAGE_PROFILE, "🔐", "Alterar sua senha"),
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
PHOTOS_TABS = [PHOTOS_TAB_ADD, PHOTOS_TAB_GALLERY]


PENDING_STATE_KEY = "_pending_state"

# ---------------------------------------------------------------------------
# Estado do menu lateral
#
# O Streamlit 1.64.0 guarda o estado aberto/fechado da sidebar no front-end
# (não existe API Python para abri-la/fechá-la depois do primeiro carregamento).
# Por isso mantemos no session_state apenas a *intenção* do usuário e uma
# "ordem" de um único uso, executada por uma pequena ponte HTML/JS que clica
# nos controles nativos. O estado real continua sobrevivendo a reruns porque
# é preservado pelo próprio React/Streamlit no navegador.
# ---------------------------------------------------------------------------
SIDEBAR_OPEN_KEY = "sidebar_open"
SIDEBAR_COMMAND_KEY = "_sidebar_command"
SIDEBAR_COMMAND_TOGGLE = "toggle"
SIDEBAR_COMMAND_CLOSE = "close"
SIDEBAR_COMMAND_CLOSE_MOBILE = "close_if_mobile"
SIDEBAR_MOBILE_BREAKPOINT_PX = 768


def next_sidebar_render_token() -> str:
    """Gera um token único para forçar o recarregamento da ponte JS.

    Isso é essencial: se o HTML do iframe fosse idêntico entre dois reruns,
    o navegador reaproveitaria o documento e o comando "toggle" seria
    executado apenas na primeira vez (o segundo clique não faria nada).
    """
    return uuid.uuid4().hex


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


def request_sidebar_toggle():
    """Registra o pedido de alternar o menu e atualiza a intenção da sessão."""
    st.session_state[SIDEBAR_OPEN_KEY] = not st.session_state.get(
        SIDEBAR_OPEN_KEY, True
    )
    st.session_state[SIDEBAR_COMMAND_KEY] = SIDEBAR_COMMAND_TOGGLE


def request_sidebar_close():
    """Registra o pedido de fechar o menu em qualquer tamanho de tela."""
    st.session_state[SIDEBAR_OPEN_KEY] = False
    st.session_state[SIDEBAR_COMMAND_KEY] = SIDEBAR_COMMAND_CLOSE


def request_sidebar_close_on_navigation():
    """Pede o fechamento automático apenas em telas pequenas (< 768 px).

    O Python não conhece a largura do navegador; a decisão é tomada pela
    ponte JS com ``matchMedia``. Em desktop o comando é ignorado, preservando
    o estado escolhido pelo usuário.
    """
    st.session_state[SIDEBAR_COMMAND_KEY] = SIDEBAR_COMMAND_CLOSE_MOBILE


def navigate_to(page: str, **extra_state):
    """Troca a página atual (e opcionalmente a aba interna) e recarrega a tela."""
    set_pending_state(**extra_state)
    st.session_state["current_page"] = page
    request_sidebar_close_on_navigation()
    st.rerun()


def record_sync():
    """Registra o horário da última gravação local bem-sucedida."""
    st.session_state["last_sync_at"] = datetime.now().strftime("%H:%M:%S")


@st.cache_data(show_spinner=False)
def _read_logo_svg(path: str, modified_at: float):
    """Lê o conteúdo do SVG oficial (com cache invalidado pela data de modificação)."""
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
        # Renderiza como imagem (data URI) para evitar exibição do código SVG como texto.
        encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
        markup = (
            f'<img src="data:image/svg+xml;base64,{encoded}" '
            f'alt="ACNnorte" width="{width}" '
            f'style="width:{width}px;max-width:100%;height:auto;display:inline-block;" />'
        )
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
    """Aplica o tema claro do ACNnorte a todas as telas.

    A implementação vive em ``src.ui.theme``; esta função é mantida por
    compatibilidade com o restante da aplicação.
    """
    from src.ui.theme.components import apply_theme

    apply_theme(SIDEBAR_MOBILE_BREAKPOINT_PX)


def sidebar_css() -> str:
    """CSS exclusivo do menu lateral (delegado a ``src.ui.theme``)."""
    from src.ui.theme.styles import get_sidebar_css

    return get_sidebar_css(SIDEBAR_MOBILE_BREAKPOINT_PX)


def inject_sidebar_css():
    """Injeta o CSS do menu lateral (uma única fonte de verdade)."""
    from src.ui.theme.components import inject_sidebar_css as _inject

    _inject(SIDEBAR_MOBILE_BREAKPOINT_PX)


def build_sidebar_bridge_html(
    command: str | None = None,
    render_token: str | None = None,
) -> str:
    """Monta a ponte HTML/JS que aciona os controles nativos da sidebar.

    A ponte roda em um iframe same-origin e acessa ``window.parent.document``.
    Ela tolera os testids do Streamlit 1.64.0 e os nomes usados por versões
    anteriores. ``command`` é executado uma única vez por renderização e
    ``render_token`` garante que o iframe seja recarregado a cada comando.
    """
    command_json = json.dumps(command)
    token_json = json.dumps(render_token or "")
    return f"""
    <!doctype html>
    <html>
    <head><meta charset="utf-8">
    <style>html, body {{ margin:0; padding:0; height:0; overflow:hidden; background:transparent; }}</style>
    </head>
    <body>
    <script>
    (function() {{
        const COMMAND = {command_json};
        const RENDER_TOKEN = {token_json};
        const MOBILE_BREAKPOINT = {SIDEBAR_MOBILE_BREAKPOINT_PX};
        const doc = window.parent.document;

        function sidebar() {{
            return doc.querySelector('[data-testid="stSidebar"]');
        }}
        function isExpanded() {{
            const el = sidebar();
            if (!el) return false;
            const aria = el.getAttribute('aria-expanded');
            if (aria === 'true') return true;
            if (aria === 'false') return false;
            return el.offsetWidth > 40;
        }}
        function isMobile() {{
            try {{
                return window.parent.matchMedia(
                    '(max-width: ' + MOBILE_BREAKPOINT + 'px)'
                ).matches;
            }} catch (e) {{
                return false;
            }}
        }}
        function first(selectors) {{
            for (const selector of selectors) {{
                const element = doc.querySelector(selector);
                if (element) return element;
            }}
            return null;
        }}
        function expandControl() {{
            return first([
                '[data-testid="stExpandSidebarButton"] button',
                '[data-testid="stExpandSidebarButton"]',
                '[data-testid="stSidebarCollapsedControl"] button',
                '[data-testid="stSidebarCollapsedControl"]',
                '[data-testid="collapsedControl"] button',
                '[data-testid="collapsedControl"]',
                'button[kind="header"][data-testid*="collapsed"]'
            ]);
        }}
        function collapseControl() {{
            return first([
                '[data-testid="stSidebarCollapseButton"] button',
                '[data-testid="stSidebarCollapseButton"]',
                '[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button',
                '[data-testid="stSidebar"] button[kind="header"]'
            ]);
        }}
        function click(element) {{
            if (!element) return false;
            element.click();
            return true;
        }}
        function tryOpen() {{
            return click(expandControl()) || click(collapseControl());
        }}
        function tryClose() {{
            return click(collapseControl()) || click(expandControl());
        }}
        function syncControls() {{
            const open = isExpanded();
            /* O Streamlit pode renderizar dois botões no mesmo container
               (um clone interno de tooltip). Atualizamos todos para que o
               botão realmente visível também receba o rótulo acessível. */
            doc.querySelectorAll('.st-key-sidebar_toggle button').forEach(
                function (button) {{
                    button.setAttribute('aria-label', open ? 'Fechar menu' : 'Abrir menu');
                    button.setAttribute('title', open ? 'Fechar menu' : 'Abrir menu');
                }}
            );
            doc.querySelectorAll('.st-key-sidebar_close_menu button').forEach(
                function (button) {{
                    button.setAttribute('aria-label', 'Fechar menu');
                }}
            );
            const toggleContainer = first(['.st-key-sidebar_toggle']);
            if (toggleContainer) {{
                /* No celular, com o menu aberto, o próprio "✕ Fechar menu"
                   já está visível; escondemos o flutuante para não cobrir. */
                toggleContainer.style.display = (open && isMobile()) ? 'none' : '';
            }}
        }}
        function applyCommand(tries) {{
            tries = tries || 0;
            let resolved = true;
            if (COMMAND === 'toggle') {{
                resolved = isExpanded() ? tryClose() : tryOpen();
            }} else if (COMMAND === 'close') {{
                resolved = isExpanded() ? tryClose() : true;
            }} else if (COMMAND === 'close_if_mobile') {{
                resolved = (isMobile() && isExpanded()) ? tryClose() : true;
            }}
            if (!resolved && tries < 20) {{
                window.setTimeout(function() {{ applyCommand(tries + 1); }}, 80);
                return;
            }}
            window.setTimeout(syncControls, 60);
        }}
        function observeSidebar() {{
            const el = sidebar();
            if (!el || !window.parent.MutationObserver) return;
            try {{
                const observer = new window.parent.MutationObserver(syncControls);
                observer.observe(el, {{
                    attributes: true,
                    attributeFilter: ['aria-expanded', 'class', 'style']
                }});
            }} catch (e) {{}}
        }}
        window.setTimeout(function() {{
            applyCommand(0);
            observeSidebar();
            syncControls();
        }}, 60);
    }})();
    </script>
    </body>
    </html>
    """


def _render_sidebar_bridge(markup: str):
    """Renderiza a ponte invisível (1 px) com compatibilidade de versões."""
    if hasattr(st, "iframe"):
        # st.iframe (Streamlit atual) substitui components.v1.html e mantém
        # acesso same-origin ao documento pai.
        st.iframe(markup, height=1)
        return
    from streamlit.components.v1 import html as component_html

    component_html(markup, height=1, scrolling=False)


def render_sidebar_toggle():
    """Botão "☰ Menu" fixo e ponte JS para abrir/fechar a sidebar nativa.

    O botão é um ``st.button`` real (testável, com foco e área de toque) e a
    ponte apenas executa a ação no front-end. A intenção fica em
    ``st.session_state["sidebar_open"]`` e sobrevive a reruns e navegação.
    """
    st.session_state.setdefault(SIDEBAR_OPEN_KEY, True)

    if st.button(
        "☰ Menu",
        key="sidebar_toggle",
        help="Abrir ou fechar o menu lateral",
    ):
        request_sidebar_toggle()

    command = st.session_state.pop(SIDEBAR_COMMAND_KEY, None)
    # O token muda o HTML a cada run para o navegador reexecutar a ponte
    # (inclusive em cliques repetidos de "alternar"). 1 px é suficiente.
    _render_sidebar_bridge(
        build_sidebar_bridge_html(command, next_sidebar_render_token())
    )
