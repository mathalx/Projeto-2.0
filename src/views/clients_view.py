import html
from datetime import date

import streamlit as st

from src.form_template import first_unanswered_section, visit_completion
from src.storage_manager import (
    add_client,
    add_visit,
    delete_client,
    load_clients,
    load_visits,
)
from src.ui_components import (
    CLIENTS_TAB_CONSULT,
    CLIENTS_TAB_LIST,
    CLIENTS_TAB_NEW,
    CLIENTS_TABS,
    PAGE_VISITS,
    VISITS_TAB_FILL,
    navigate_to,
    record_sync,
    render_acnnorte_logo,
    render_empty_state,
    render_section_title,
    set_flash,
    status_badge,
)

REQUIRED_HINT = "Campos marcados com * são obrigatórios."


def _select_clients_tab() -> str:
    if st.session_state.get("clients_tab") not in CLIENTS_TABS:
        st.session_state["clients_tab"] = CLIENTS_TAB_LIST
    return st.radio(
        "Seção de clientes",
        CLIENTS_TABS,
        key="clients_tab",
        horizontal=True,
        label_visibility="collapsed",
    )


def _open_visit(visit_id: str, forms: dict):
    st.session_state["active_visit_id"] = visit_id
    st.session_state[f"form_step_{visit_id}"] = first_unanswered_section(forms)
    navigate_to(PAGE_VISITS, visits_tab=VISITS_TAB_FILL)


def _render_client_list(clients: dict, visits: dict):
    render_section_title(
        "Empresas clientes cadastradas",
        "Pesquise pelo nome, CNPJ ou responsável.",
        "🏢",
    )

    if not clients:
        render_empty_state(
            "🏢",
            "Nenhum cliente cadastrado",
            "Use a seção “Cadastrar Cliente” para adicionar a primeira empresa.",
        )
        return

    search_query = st.text_input(
        "Pesquisar cliente",
        key="clients_search",
        placeholder="Digite o nome, CNPJ ou responsável...",
    ).strip().lower()

    filtered = {
        c_id: client
        for c_id, client in clients.items()
        if not search_query
        or search_query in client.get("name", "").lower()
        or search_query in client.get("cnpj", "").lower()
        or search_query in client.get("responsible", "").lower()
    }

    st.caption(f"{len(filtered)} de {len(clients)} cliente(s) exibido(s).")

    if not filtered:
        render_empty_state("🔍", "Nenhum cliente encontrado", "Tente outro nome, CNPJ ou responsável.")
        return

    for c_id, client in filtered.items():
        label = f"🏢 {client.get('name', '—')} — CNPJ: {client.get('cnpj', '—')}"
        with st.expander(label):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Endereço:** {client.get('address', '—')}")
                st.markdown(f"**Responsável:** {client.get('responsible', '—')}")
            with col2:
                st.markdown(f"**Telefone:** {client.get('phone', '—')}")
                st.markdown(f"**E-mail:** {client.get('email', '—')}")
                st.markdown(f"**Cadastrado em:** {client.get('created_at', '—')}")

            client_visits = [v for v in visits.values() if v.get("client_id") == c_id]
            st.markdown(f"📊 **Visitas registradas:** {len(client_visits)}")

            b_col1, b_col2, _ = st.columns([1.4, 1.1, 2.5])
            with b_col1:
                if st.button("🚀 Iniciar visita", key=f"start_visit_{c_id}", width="stretch"):
                    success, visit_id, message = add_visit(
                        c_id,
                        st.session_state.get("username", "Técnico"),
                        str(date.today()),
                    )
                    if success:
                        record_sync()
                        set_flash(f"Visita iniciada para {client.get('name')}. Continue o preenchimento.")
                        _open_visit(visit_id, {})
                    else:
                        st.error("Não foi possível iniciar a visita. Tente novamente.")
            with b_col2:
                if st.button("🗑️ Excluir", key=f"del_client_{c_id}", width="stretch"):
                    st.session_state["client_delete_pending"] = c_id

            if st.session_state.get("client_delete_pending") == c_id:
                st.warning(
                    f"Excluir o cliente “{client.get('name')}”? As visitas já registradas não serão apagadas."
                )
                confirm_col, cancel_col = st.columns(2)
                with confirm_col:
                    if st.button("Sim, excluir", key=f"confirm_del_{c_id}", type="primary", width="stretch"):
                        success, message = delete_client(c_id)
                        st.session_state.pop("client_delete_pending", None)
                        if success:
                            record_sync()
                            set_flash("Cliente excluído com sucesso.")
                            st.rerun()
                        else:
                            st.error(message)
                with cancel_col:
                    if st.button("Cancelar", key=f"cancel_del_{c_id}", width="stretch"):
                        st.session_state.pop("client_delete_pending", None)
                        st.rerun()


def _render_new_client(clients: dict):
    render_section_title(
        "Cadastrar nova empresa cliente",
        REQUIRED_HINT,
        "➕",
    )

    nonce = st.session_state.get("new_client_form_nonce", 0)
    with st.form(f"new_client_form_{nonce}", clear_on_submit=False):
        c_name = st.text_input("Nome da empresa *", placeholder="Ex: Indústria Metalúrgica Norte Ltda")
        c_cnpj = st.text_input("CNPJ *", placeholder="Ex: 00.000.000/0001-00")
        c_address = st.text_input("Endereço completo *", placeholder="Ex: Av. Industrial, 1000 — Distrito Industrial")
        c_resp = st.text_input("Responsável técnico / contato *", placeholder="Ex: Eng. Carlos Alberto")
        c_phone = st.text_input("Telefone *", placeholder="Ex: (92) 99999-9999")
        c_email = st.text_input("E-mail *", placeholder="Ex: contato@empresa.com.br")

        with st.container(key="cadastrar_cliente_submit_wrap"):
            submitted = st.form_submit_button("Cadastrar cliente", type="primary", width="stretch")
        if submitted:
            missing = []
            if not c_name.strip():
                missing.append("Nome da empresa")
            if not c_cnpj.strip():
                missing.append("CNPJ")
            if not c_address.strip():
                missing.append("Endereço")
            if not c_resp.strip():
                missing.append("Responsável")
            if not c_phone.strip():
                missing.append("Telefone")
            if not c_email.strip():
                missing.append("E-mail")

            if missing:
                st.error("Preencha os campos obrigatórios: " + ", ".join(missing) + ".")
            elif any(c.get("cnpj", "").strip() == c_cnpj.strip() for c in clients.values()):
                st.error("Já existe um cliente cadastrado com este CNPJ.")
            else:
                with st.spinner("Salvando cliente..."):
                    success, _client_id, message = add_client(
                        c_name, c_cnpj, c_address, c_resp, c_phone, c_email
                    )
                if success:
                    st.session_state["new_client_form_nonce"] = nonce + 1
                    record_sync()
                    set_flash(f"Cliente “{c_name.strip()}” cadastrado com sucesso.")
                    st.rerun()
                else:
                    st.error(message)


def _render_consult(clients: dict, visits: dict):
    render_section_title(
        "Consultar cliente e histórico",
        "Selecione uma empresa para ver os dados e as visitas registradas.",
        "🔍",
    )

    if not clients:
        render_empty_state("🔍", "Nenhum cliente para consultar", "Cadastre um cliente primeiro.")
        return

    client_options = {f"{c.get('name', '—')} — {c.get('cnpj', '—')}": c_id for c_id, c in clients.items()}
    selected_label = st.selectbox("Selecione o cliente", list(client_options.keys()))
    selected_id = client_options[selected_label]
    client = clients[selected_id]

    with st.container(border=True):
        st.markdown(f"#### {html.escape(client.get('name', '—'))}")
        st.markdown(f"**CNPJ:** {client.get('cnpj', '—')}")
        st.markdown(f"**Responsável:** {client.get('responsible', '—')}")
        st.markdown(f"**Endereço:** {client.get('address', '—')}")
        st.markdown(f"**Contato:** {client.get('phone', '—')} / {client.get('email', '—')}")

    st.markdown("#### Histórico de visitas técnicas")
    client_visits = [v for v in visits.values() if v.get("client_id") == selected_id]
    if not client_visits:
        render_empty_state("📋", "Nenhuma visita registrada", "Inicie uma visita na aba Clientes ou em Visitas Técnicas.")
        return

    client_visits.sort(key=lambda v: v.get("date", ""), reverse=True)
    for visit in client_visits:
        v_id = visit.get("id", "")
        answered, total = visit_completion(visit.get("forms", {}))
        st.markdown(
            f"""
            <div class="acn-activity">
                <b>Visita de {html.escape(str(visit.get('date', '—')))}</b> {status_badge(visit.get('status', 'Rascunho'))}
                <div>Técnico: {html.escape(str(visit.get('technician', '—')))}</div>
                <div class="acn-activity-meta">Checklist: {answered}/{total} • Fotografias: {len(visit.get('photos', []))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("✍️ Abrir visita", key=f"open_visit_{v_id}", width="stretch"):
            _open_visit(v_id, visit.get("forms", {}))


def render_clients_view():
    render_acnnorte_logo(size="medium", subtitle="Gerenciamento e Cadastro de Clientes")

    clients = load_clients()
    visits = load_visits()
    selected_tab = _select_clients_tab()

    if selected_tab == CLIENTS_TAB_NEW:
        _render_new_client(clients)
    elif selected_tab == CLIENTS_TAB_CONSULT:
        _render_consult(clients, visits)
    else:
        _render_client_list(clients, visits)
