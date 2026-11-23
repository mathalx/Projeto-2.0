"""Tela de login do ACNnorte com suporte a contas locais e Xano."""

import streamlit as st

from src.auth_manager import authenticate_user
from src.modules.authentication.auth_service import (
    AuthenticationError,
    LoginValidationError,
    XanoSession,
    authenticate_with_xano,
)
from src.ui_components import render_acnnorte_logo


def _persist_session(
    display_name: str,
    is_admin: bool,
    source: str = "local",
    xano_session: XanoSession | None = None,
) -> None:
    """Grava a sessão autenticada mantendo compatibilidade com as telas atuais."""
    st.session_state["authenticated"] = True
    st.session_state["username"] = display_name
    st.session_state["is_admin"] = is_admin
    st.session_state["auth_source"] = source

    if xano_session is not None:
        st.session_state["xano_token"] = xano_session.token
        st.session_state["xano_user"] = dict(xano_session.user)
        st.session_state["user_email"] = str(
            xano_session.user.get("email") or display_name
        )
    else:
        for key in ("xano_token", "xano_user", "user_email"):
            st.session_state.pop(key, None)


def render_login_view():
    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)

        with st.container():
            render_acnnorte_logo(width=260, subtitle="Sistema de Gestão e Operações")
            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

            with st.form("login_form", clear_on_submit=False):
                identifier = st.text_input(
                    "E-mail ou usuário",
                    placeholder="seu@email.com ou seu.usuario",
                    autocomplete="username",
                )
                password = st.text_input(
                    "Senha",
                    type="password",
                    placeholder="Digite sua senha",
                    autocomplete="current-password",
                )
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                submit_button = st.form_submit_button("ENTRAR", type="primary")

                if submit_button:
                    identifier = (identifier or "").strip()

                    if not identifier or not password.strip():
                        st.error("Informe o e-mail e a senha para continuar.")
                    elif "@" in identifier:
                        try:
                            xano_session = authenticate_with_xano(identifier, password)
                        except LoginValidationError as exc:
                            st.error(str(exc))
                        except AuthenticationError as exc:
                            st.error(exc.message)
                        else:
                            display_name = str(
                                xano_session.user.get("name")
                                or xano_session.user.get("email")
                                or identifier
                            )
                            _persist_session(
                                display_name,
                                xano_session.is_admin,
                                source="xano",
                                xano_session=xano_session,
                            )
                            st.success("Login realizado com sucesso! Redirecionando...")
                            st.rerun()
                    else:
                        success, _message, is_admin = authenticate_user(
                            identifier, password
                        )
                        if success:
                            _persist_session(
                                identifier,
                                is_admin,
                                source="local",
                            )
                            st.success("Login realizado com sucesso! Redirecionando...")
                            st.rerun()
                        else:
                            st.error("Usuário ou senha incorretos.")

            st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
            st.markdown(
                """
                <div style="text-align: center; color: #4B5563; font-size: 0.8rem;">
                    ACNnorte © 2026 — Todos os direitos reservados.
                </div>
                """,
                unsafe_allow_html=True,
            )
