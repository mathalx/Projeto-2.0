import streamlit as st

def main():
    st.set_page_config(
        page_title="Segurança do Trabalho - Visitas Técnicas",
        page_icon="🛡️",
        layout="wide",
    )
    
    st.title("🛡️ Aplicativo de Visitas Técnicas de Segurança do Trabalho")
    st.markdown("---")
    st.success("Estrutura inicial do projeto configurada com sucesso!")
    st.info("Utilize o menu lateral para navegar pelos módulos (em desenvolvimento).")

if __name__ == "__main__":
    main()
