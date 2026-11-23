import streamlit as st
from src.ui_components import render_acnnorte_logo
from src.auth_manager import load_users, add_user, toggle_user_status, delete_user, admin_reset_password

def render_admin_view():
    is_admin = st.session_state.get("is_admin", False)
    if not is_admin:
        st.error("Acesso negado. Esta área é restrita a administradores autorizados da ACNnorte.")
        return
        
    render_acnnorte_logo(size="medium", subtitle="Gerenciamento Interno de Usuários")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["📋 Lista de Usuários", "➕ Adicionar Novo Usuário"])
    
    with tab1:
        st.markdown("#### Usuários Cadastrados no Sistema")
        users = load_users()
        
        for username, data in users.items():
            with st.container():
                cols = st.columns([2, 1, 1, 1.5])
                with cols[0]:
                    st.markdown(f"**{username}**")
                    role_badge = "👑 Administrador" if data.get("is_admin") else "👤 Usuário Padrão"
                    st.caption(role_badge)
                with cols[1]:
                    status = "✅ Ativo" if data.get("active", True) else "❌ Desativado"
                    st.markdown(status)
                with cols[2]:
                    st.markdown(f"<small style='color: #4B5563;'>Criado em: {data.get('created_at', 'N/D')}</small>", unsafe_allow_html=True)
                with cols[3]:
                    # Action buttons
                    col_act1, col_act2 = st.columns(2)
                    with col_act1:
                        status_label = "Desativar" if data.get("active", True) else "Ativar"
                        if st.button(status_label, key=f"toggle_{username}"):
                            success, msg = toggle_user_status(username)
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                    with col_act2:
                        if username != "Ana.norte":
                            if st.button("Remover", key=f"del_{username}", type="secondary"):
                                st.session_state["user_delete_pending"] = username
                        else:
                            st.caption("Protegido")
                if st.session_state.get("user_delete_pending") == username:
                    st.warning(f"Remover o usuário “{username}”? Ele perderá o acesso ao sistema.")
                    confirm_col, cancel_col = st.columns(2)
                    with confirm_col:
                        if st.button("Sim, remover", key=f"confirm_del_user_{username}", type="primary", width="stretch"):
                            success, msg = delete_user(username)
                            st.session_state.pop("user_delete_pending", None)
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                    with cancel_col:
                        if st.button("Cancelar", key=f"cancel_del_user_{username}", width="stretch"):
                            st.session_state.pop("user_delete_pending", None)
                            st.rerun()
                st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid #E5E9EC;'>", unsafe_allow_html=True)
                
        # Password reset section by admin
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        with st.expander("🔑 Redefinir Senha de Usuário (Administrativo)"):
            reset_user = st.selectbox("Selecione o usuário", options=list(users.keys()), key="reset_user_select")
            new_admin_pwd = st.text_input("Nova senha temporária", type="password", key="reset_pwd_input")
            if st.button("Aplicar Nova Senha"):
                if not new_admin_pwd or len(new_admin_pwd) < 6:
                    st.error("A senha deve ter pelo menos 6 caracteres.")
                else:
                    success, msg = admin_reset_password(reset_user, new_admin_pwd)
                    if success:
                        st.success(f"Senha de {reset_user} atualizada com sucesso.")
                    else:
                        st.error(msg)

    with tab2:
        st.markdown("#### Cadastrar Novo Usuário")
        st.info("O cadastro de novos usuários é exclusivo para a área administrativa protegida da ACNnorte.")
        
        with st.form("new_user_form"):
            new_username = st.text_input("Nome de Usuário", placeholder="Ex: joao.norte")
            new_password = st.text_input("Senha Inicial", type="password", placeholder="Mínimo de 6 caracteres")
            is_new_admin = st.checkbox("Conceder privilégios de Administrador")
            
            submit_new = st.form_submit_button("Cadastrar Usuário")
            
            if submit_new:
                if not new_username.strip() or not new_password.strip():
                    st.error("Preencha todos os campos obrigatórios.")
                elif len(new_password) < 6:
                    st.error("A senha deve ter pelo menos 6 caracteres.")
                else:
                    success, msg = add_user(new_username.strip(), new_password, is_new_admin)
                    if success:
                        st.success(f"Usuário '{new_username}' cadastrado com sucesso!")
                    else:
                        st.error(msg)
