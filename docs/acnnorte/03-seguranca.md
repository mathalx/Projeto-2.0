# Segurança e Gerenciamento de Credenciais — ACNnorte

## Armazenamento Seguro de Senhas
- As senhas nunca são armazenadas em texto puro.
- O sistema utiliza o algoritmo **PBKDF2-HMAC-SHA256** com salt aleatório de 16 bytes e 100.000 iterações (implementado na biblioteca padrão `hashlib` do Python).

## Controle de Sessão
- O estado da sessão é gerenciado de forma segura através do `st.session_state` do Streamlit.
- Páginas protegidas exigem autenticação prévia (`authenticated == True`).
- A opção **Sair do Sistema (Logout)** limpa imediatamente a sessão ativa.
