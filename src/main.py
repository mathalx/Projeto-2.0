import streamlit as st

from src.auth_manager import init_db
from src.features.field_inspection import (
    render_acn_sidebar,
    render_field_inspection_view,
)
from src.features.field_inspection.constants import DEFAULT_USERNAME
from src.storage_manager import init_storage
from src.ui_components import (
    PAGE_ADMIN,
    PAGE_CLIENTS,
    PAGE_DASHBOARD,
    PAGE_FORM,
    PAGE_PHOTOS,
    PAGE_PROFILE,
    PAGE_REPORTS,
    PAGE_VISITS,
    apply_global_styles,
    apply_pending_state,
    render_flash,
)
from src.views.admin_view import render_admin_view
from src.views.clients_view import render_clients_view
from src.views.dashboard_main import render_main_dashboard
from src.views.photos_view import render_photos_view
from src.views.profile_view import render_profile_view
from src.views.reports_view import render_reports_view
from src.views.visits_view import render_visits_view

PAGE_RENDERERS = {
    PAGE_FORM: render_field_inspection_view,
    PAGE_DASHBOARD: render_main_dashboard,
    PAGE_CLIENTS: render_clients_view,
    PAGE_VISITS: render_visits_view,
    PAGE_PHOTOS: render_photos_view,
    PAGE_REPORTS: render_reports_view,
    PAGE_PROFILE: render_profile_view,
    PAGE_ADMIN: render_admin_view,
}


def _render_sidebar(is_admin: bool):
    """Delega o menu lateral ao novo módulo isolado de inspeção de campo."""
    render_acn_sidebar(is_admin)


def main():
    st.set_page_config(
        page_title="ACNnorte — Inspeções de Campo",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="auto",
    )

    # Inicialização única e idempotente do armazenamento local.
    init_db()
    init_storage()
    apply_global_styles()

    # CHANGE 08 — acesso direto ao formulário de campo, sem tela de login.
    st.session_state.setdefault("authenticated", True)
    st.session_state.setdefault("username", DEFAULT_USERNAME)
    st.session_state.setdefault("is_admin", True)
    st.session_state.setdefault("current_page", PAGE_FORM)

    apply_pending_state()

    is_admin = st.session_state.get("is_admin", True)
    current_page = st.session_state.get("current_page", PAGE_FORM)
    if current_page == PAGE_ADMIN and not is_admin:
        current_page = PAGE_FORM
    if current_page not in PAGE_RENDERERS:
        current_page = PAGE_FORM
    st.session_state["current_page"] = current_page

    _render_sidebar(is_admin)
    render_flash()

    renderer = PAGE_RENDERERS.get(current_page, render_field_inspection_view)
    renderer()


if __name__ == "__main__":
    main()
