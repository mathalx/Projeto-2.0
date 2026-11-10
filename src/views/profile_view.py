import streamlit as st
from src.ui_components import render_acnnorte_logo
from src.auth_manager import update_password

def render_profile_view():
    username = st.session_state.get("username", "")
    render_acnnorte_logo(size="medium", subtitle="Perfil e Alteração de Senha")
    st.markdown("---")
    
    st.markdown(f"#### Alteração de Senha para **{username}**")
    st.markdown("Para garantir a segurança da sua conta, informe sua senha atual e escolha uma nova senha forte.")
    
    with st.form("change_pwd_form"):
        current_pwd = st.text_input("Senha Atual", type="password")
        new_pwd = st.text_input("Nova Senha", type="password", placeholder="Mínimo de 6 caracteres")
        confirm_pwd = st.text_input("Confirme a Nova Senha", type="password")
        
        submit_pwd = st.form_submit_button("Atualizar Senha")
        
        if submit_pwd:
            if not current_pwd or not new_pwd or not confirm_pwd:
                st.error("Todos os campos são obrigatórios.")
            elif new_pwd != confirm_pwd:
                st.error("As duas novas senhas não coincidem.")
            elif len(new_pwd) < 6:
                st.error("A nova senha deve ter pelo menos 6 caracteres.")
            else:
                success, msg = update_password(username, current_pwd, new_pwd)
                if success:
                    st.success("Senha alterada com sucesso! A nova senha será utilizada nos próximos acessos.")
                else:
                    st.error(msg)
