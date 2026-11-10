import html
from datetime import datetime

import streamlit as st

from src.storage_manager import load_clients, load_visits
from src.ui_components import (
    CLIENTS_TAB_CONSULT,
    CLIENTS_TAB_NEW,
    PAGE_CLIENTS,
    PAGE_REPORTS,
    PAGE_VISITS,
    VISITS_TAB_NEW,
    navigate_to,
    render_acnnorte_logo,
    render_empty_state,
    render_section_title,
    status_badge,
)


def _parse_datetime(value: str):
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        return None


def _build_recent_activities(clients: dict, visits: dict, limit: int = 6):
    activities = []
    for visit in visits.values():
        activities.append(
            {
                "kind": "visita",
                "icon": "📋",
                "title": f"Visita de {visit.get('client_name', 'cliente')}",
                "detail": f"Técnico: {visit.get('technician', '—')}",
                "status": visit.get("status", "Rascunho"),
                "when": visit.get("updated_at") or visit.get("created_at", ""),
            }
        )
    for client in clients.values():
        activities.append(
            {
                "kind": "cliente",
                "icon": "🏢",
                "title": f"Cliente cadastrado: {client.get('name', '—')}",
                "detail": f"CNPJ: {client.get('cnpj', '—')}",
                "status": None,
                "when": client.get("created_at", ""),
            }
        )

    def sort_key(item):
        parsed = _parse_datetime(item.get("when", ""))
        return parsed or datetime.min

    return sorted(activities, key=sort_key, reverse=True)[:limit]


def render_main_dashboard():
    username = html.escape(st.session_state.get("username", "Usuário"))
    render_acnnorte_logo(size="medium", subtitle="Painel Inicial e Indicadores Operacionais")

    st.markdown(
        f"### Olá, **{username}**! Veja o resumo das suas visitas técnicas."
    )
    st.caption(f"Hoje é {datetime.now().strftime('%d/%m/%Y')} — dados salvos neste dispositivo.")

    clients = load_clients()
    visits = load_visits()

    total_clients = len(clients)
    total_visits = len(visits)
    pending_visits = sum(
        1 for v in visits.values() if v.get("status") in ["Rascunho", "Em Andamento"]
    )
    finished_visits = sum(1 for v in visits.values() if v.get("status") == "Finalizada")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Total de Clientes", value=total_clients, delta="Cadastrados")
    with col2:
        st.metric(label="Visitas Realizadas", value=finished_visits, delta="Finalizadas")
    with col3:
        st.metric(label="Visitas Pendentes", value=pending_visits, delta="A concluir")
    with col4:
        st.metric(label="Total de Visitas", value=total_visits, delta="Registradas")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # Atalhos rápidos (navegam de verdade para a funcionalidade)
    # ------------------------------------------------------------------
    render_section_title("Atalhos rápidos", "Acesse as ações mais usadas com um clique.", "⚡")
    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        if st.button("🏢 Cadastrar cliente", key="dash_new_client", width="stretch"):
            navigate_to(PAGE_CLIENTS, clients_tab=CLIENTS_TAB_NEW)
    with sc2:
        if st.button("🚀 Iniciar visita", key="dash_new_visit", width="stretch"):
            navigate_to(PAGE_VISITS, visits_tab=VISITS_TAB_NEW)
    with sc3:
        if st.button("🔍 Consultar registros", key="dash_consult", width="stretch"):
            navigate_to(PAGE_CLIENTS, clients_tab=CLIENTS_TAB_CONSULT)
    with sc4:
        if st.button("📊 Gerar relatórios", key="dash_reports", width="stretch"):
            navigate_to(PAGE_REPORTS)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # Últimas atividades
    # ------------------------------------------------------------------
    render_section_title("Últimas atividades", "Clientes e visitas atualizados recentemente.", "🕒")
    activities = _build_recent_activities(clients, visits)
    if not activities:
        render_empty_state(
            "🗂️",
            "Nenhuma atividade registrada ainda",
            "Cadastre um cliente ou inicie uma visita para começar.",
        )
    else:
        for activity in activities:
            badge = status_badge(activity["status"]) if activity.get("status") else ""
            st.markdown(
                f"""
                <div class="acn-activity">
                    <b>{activity['icon']} {html.escape(activity['title'])}</b> {badge}
                    <div>{html.escape(activity['detail'])}</div>
                    <div class="acn-activity-meta">Atualizado em {html.escape(str(activity['when']) or '—')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
