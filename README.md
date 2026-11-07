# Aplicativo de Visitas Técnicas de Segurança do Trabalho

Aplicativo modular desenvolvido em Python para gestão de visitas técnicas de segurança do trabalho, preenchimento de formulários de inspeção, registro fotográfico e geração de relatórios e planilhas em Excel.

## 🚀 Arquitetura do Projeto

O projeto segue uma arquitetura modular baseada em responsabilidades:

- `src/core/`: Configurações centrais, banco de dados, segurança e utilitários.
- `src/modules/`: Módulos funcionais (autenticação, dashboard, clientes, visitas, formulários, fotos, relatórios, exportações).
- `src/shared/`: Componentes reutilizáveis, layouts e validadores.
- `storage/`: Armazenamento local de fotos, relatórios e exports.
- `assets/`: Recursos estáticos (logotipos, ícones, imagens).
- `tests/`: Testes unitários, de integração e validação.

## 📋 Pré-requisitos

- Python 3.10 ou superior
- Git

## 🛠️ Instalação e Execução

1. Clone o repositório:
```bash
git clone https://github.com/mathalx/Projeto-2.0.git
cd Projeto-2.0
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv venv
# No Windows:
venv\Scripts\activate
# No Linux/macOS:
source venv/bin/activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure o arquivo de ambiente:
```bash
cp .env.example .env
```

5. Execute a aplicação:
```bash
streamlit run src/main.py
```

## 📦 Versionamento e Padrões

O projeto utiliza Conventional Commits e uma estratégia estruturada de branches (`main`, `develop`, `feature/*`, `hotfix/*`). Consulte a documentação em `docs/versionamento/git-github.md`.

## 📄 Licença

Uso interno e restrito.
