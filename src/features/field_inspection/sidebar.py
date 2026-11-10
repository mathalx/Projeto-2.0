"""Menu lateral em blocos do Layout ACN Norte."""

from __future__ import annotations

import html

import streamlit as st

from src.ui_components import (
    PAGE_ADMIN,
    PAGE_CLIENTS,
    PAGE_FORM,
    PAGE_VISITS,
    navigate_to,
    render_acnnorte_logo,
    render_sync_indicator,
)

from .constants import (
    ADMIN_NAV_ITEM,
    DEFAULT_USERNAME,
    NAV_GROUPS,
    SECONDARY_NAV_ITEMS,
    NavItem,
)
from .services import create_inspection_draft


def _user_role(is_admin: bool) -> str:
    explicit = st.session_state.get("role_name")
    if explicit:
        return str(explicit)
    return "Administrador" if is_admin else "Usuário"


def _render_user_card(is_admin: bool) -> None:
    username = str(st.session_state.get("username") or DEFAULT_USERNAME)
    role = _user_role(is_admin)
    st.markdown(
        f"""
        <div class="acn-user-card">
            <div class="acn-user-name">👤 <b>{html.escape(username)}</b></div>
            <div class="acn-user-role">{html.escape(username)} - {html.escape(role)}</div>
            <div class="acn-user-caption">Perfil ativo neste dispositivo</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _is_active(item: NavItem, current_page: str) -> bool:
    if item.page == PAGE_FORM:
        return current_page in (PAGE_FORM, PAGE_VISITS)
    return current_page == item.page


def _render_nav_item(item: NavItem, current_page: str) -> None:
    active = _is_active(item, current_page)
    if st.button(
        f"{item.icon} {item.label}",
        key=f"nav_{item.page}",
        help=item.description,
        type="primary" if active else "secondary",
        width="stretch",
    ):
        if item.create_inspection:
            inspection_id = create_inspection_draft()
            if not inspection_id:
                st.error("Não foi possível iniciar uma nova inspeção.")
                return
        extra_state = dict(item.extra_state)
        navigate_to(item.page, **extra_state)


def _render_quick_actions(items: tuple[NavItem, ...]) -> None:
    for item in items:
        key = (
            "quick_new_client"
            if item.page == PAGE_CLIENTS and not item.create_inspection
            else "quick_new_visit"
        )
        if st.button(
            f"{item.icon} {item.label}",
            key=key,
            type="primary" if item.create_inspection else "secondary",
            width="stretch",
            help=item.description,
        ):
            if item.create_inspection:
                inspection_id = create_inspection_draft()
                if not inspection_id:
                    st.error("Não foi possível iniciar uma nova inspeção.")
                    return
            navigate_to(item.page, **dict(item.extra_state))


def _render_xano_smoke_test() -> None:
    """Teste opcional de conectividade com o backend Xano."""
    from src.core.database.xano_client import smoke_test

    if st.button(
        "🔌 Testar conexão com o Xano",
        key="xano_smoke_test",
        width="stretch",
        help="Verifica se o API group do Xano está acessível.",
    ):
        with st.spinner("Testando conexão com o Xano..."):
            st.session_state["xano_smoke_result"] = smoke_test()

    result = st.session_state.get("xano_smoke_result")
    if result is None:
        return
    if not result.ok:
        st.error(result.message)
    elif result.authenticated:
        st.success(result.message)
    else:
        st.info(result.message)


def _render_secondary_tools(is_admin: bool) -> None:
    with st.expander("🗂️ Registros e administração"):
        for item in SECONDARY_NAV_ITEMS:
            if st.button(
                f"{item.icon} {item.label}",
                key=f"secondary_{item.page}",
                width="stretch",
            ):
                navigate_to(item.page)

        if is_admin and st.button(
            f"{ADMIN_NAV_ITEM.icon} {ADMIN_NAV_ITEM.label}",
            key=f"secondary_{PAGE_ADMIN}",
            width="stretch",
        ):
            navigate_to(PAGE_ADMIN)

        _render_xano_smoke_test()


def render_acn_sidebar(is_admin: bool) -> None:
    """Renderiza o menu lateral completo e mantém a página atual destacada."""
    username = str(st.session_state.get("username") or DEFAULT_USERNAME)
    st.session_state.setdefault("username", username)
    current_page = st.session_state.get("current_page", PAGE_FORM)

    with st.sidebar:
        render_acnnorte_logo(width=200)
        _render_user_card(is_admin)

        for group_name, items in NAV_GROUPS:
            st.markdown(
                f'<div class="acn-nav-label">{html.escape(group_name)}</div>',
                unsafe_allow_html=True,
            )
            if group_name == "Acesso rápido":
                _render_quick_actions(items)
                continue
            for item in items:
                _render_nav_item(item, current_page)

        _render_secondary_tools(is_admin)

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        render_sync_indicator()
        st.markdown(
            "<div style='text-align:center; font-size:0.72rem; margin-top:10px;'>"
            "ACNnorte v2.0 © 2026</div>",
            unsafe_allow_html=True,
        )
