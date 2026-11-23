import os

import streamlit as st

from src.export_manager import (
    export_clients_to_excel,
    export_visits_to_excel,
    generate_pdf_report,
)
from src.storage_manager import load_clients, load_visits
from src.ui_components import (
    render_acnnorte_logo,
    render_empty_state,
    render_section_title,
    status_badge,
)


def _read_file(path: str) -> bytes:
    with open(path, "rb") as file:
        return file.read()


def render_reports_view():
    render_acnnorte_logo(size="medium", subtitle="Relatórios em PDF e Exportação Excel (XLSX)")

    visits = load_visits()
    clients = load_clients()

    tab_pdf, tab_excel = st.tabs(
        ["📄 Relatório PDF", "📊 Exportação Excel (XLSX)"]
    )

    # ------------------------------------------------------------------
    # PDF
    # ------------------------------------------------------------------
    with tab_pdf:
        render_section_title(
            "Relatório profissional em PDF",
            "Gere o documento da visita com a identidade visual da ACNnorte.",
            "📄",
        )

        if not visits:
            render_empty_state("📄", "Nenhuma visita para relatar", "Registre uma visita técnica primeiro.")
        else:
            visit_options = {
                f"Visita #{v_id} — {v.get('client_name', '—')} ({v.get('date', '—')}) • {v.get('status', 'Rascunho')}": v_id
                for v_id, v in visits.items()
            }
            selected_label = st.selectbox(
                "Selecione a visita",
                list(visit_options.keys()),
                key="report_visit_select",
            )
            selected_v_id = visit_options[selected_label]
            selected_visit = visits[selected_v_id]

            st.markdown(
                f"**Empresa:** {selected_visit.get('client_name', '—')} &nbsp;|&nbsp; "
                f"**Técnico:** {selected_visit.get('technician', '—')} &nbsp;|&nbsp; "
                f"**Situação:** {status_badge(selected_visit.get('status', 'Rascunho'))}",
                unsafe_allow_html=True,
            )

            if st.button("🚀 Gerar relatório PDF", key="generate_pdf", type="primary", width="stretch"):
                with st.spinner("Gerando relatório..."):
                    try:
                        pdf_path = generate_pdf_report(selected_v_id)
                    except Exception:
                        pdf_path = None

                if pdf_path and os.path.exists(pdf_path):
                    st.session_state["pdf_download"] = {
                        "data": _read_file(pdf_path),
                        "name": os.path.basename(pdf_path),
                    }
                    st.toast("Relatório PDF gerado com sucesso!")
                else:
                    st.session_state.pop("pdf_download", None)
                    st.error("Não foi possível gerar o relatório agora. Tente novamente.")

            pdf_download = st.session_state.get("pdf_download")
            if pdf_download:
                st.success("Relatório pronto para download.")
                st.download_button(
                    label="📥 Baixar arquivo PDF",
                    data=pdf_download["data"],
                    file_name=pdf_download["name"],
                    mime="application/pdf",
                    width="stretch",
                )

    # ------------------------------------------------------------------
    # Excel
    # ------------------------------------------------------------------
    with tab_excel:
        render_section_title(
            "Exportação para Microsoft Excel",
            "Baixe planilhas com os cadastros de clientes e o histórico de visitas.",
            "📊",
        )

        col_clients, col_visits = st.columns(2)

        with col_clients:
            st.markdown("#### 🏢 Clientes cadastrados")
            st.caption(f"Total de clientes no sistema: {len(clients)}")
            if st.button("📊 Gerar planilha de clientes", key="export_clients", width="stretch"):
                with st.spinner("Gerando planilha de clientes..."):
                    try:
                        excel_path = export_clients_to_excel()
                    except Exception:
                        excel_path = None
                if excel_path and os.path.exists(excel_path):
                    st.session_state["excel_clients"] = {
                        "data": _read_file(excel_path),
                        "name": os.path.basename(excel_path),
                    }
                    st.toast("Planilha de clientes gerada com sucesso!")
                else:
                    st.session_state.pop("excel_clients", None)
                    st.error("Não há clientes cadastrados para exportar.")

            excel_clients = st.session_state.get("excel_clients")
            if excel_clients:
                st.download_button(
                    label="📥 Baixar Excel de clientes",
                    data=excel_clients["data"],
                    file_name=excel_clients["name"],
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width="stretch",
                )

        with col_visits:
            st.markdown("#### 🛡️ Visitas técnicas")
            st.caption(f"Total de visitas registradas: {len(visits)}")
            if st.button("📊 Gerar planilha de visitas", key="export_visits", width="stretch"):
                with st.spinner("Gerando planilha de visitas..."):
                    try:
                        excel_path = export_visits_to_excel()
                    except Exception:
                        excel_path = None
                if excel_path and os.path.exists(excel_path):
                    st.session_state["excel_visits"] = {
                        "data": _read_file(excel_path),
                        "name": os.path.basename(excel_path),
                    }
                    st.toast("Planilha de visitas gerada com sucesso!")
                else:
                    st.session_state.pop("excel_visits", None)
                    st.error("Não há visitas registradas para exportar.")

            excel_visits = st.session_state.get("excel_visits")
            if excel_visits:
                st.download_button(
                    label="📥 Baixar Excel de visitas",
                    data=excel_visits["data"],
                    file_name=excel_visits["name"],
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width="stretch",
                )
