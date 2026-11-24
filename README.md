# Aplicativo de Visitas Técnicas de Segurança do Trabalho

Aplicativo modular desenvolvido em Python para gestão de visitas técnicas de segurança do trabalho, preenchimento de formulários de inspeção, registro fotográfico e geração de relatórios e planilhas em Excel.

## 🚀 Arquitetura do Projeto

O projeto segue uma arquitetura modular baseada em responsabilidades:

- `src/`: Aplicação Streamlit (ponto de entrada, autenticação, navegação, armazenamento e exportações).
  - `views/`: Telas da aplicação (login, painel, clientes, visitas, fotografias, relatórios e administração).
  - `features/visit_enhancements/`: Blocos modulares reutilizáveis de visitas (temperatura, assinaturas, equipamentos, fluxo do formulário, fotografias, relatórios e integração). Registrados em `src/features/__init__.py` e inicializados pelo `src/main.py`; acessíveis na tela de preenchimento de visitas em modo consulta.
  - `modules/authentication/`: Camada de autenticação integrada ao Xano e contas locais.
  - `core/database/`: Cliente HTTP e integração com Xano.
- `data/`: Armazenamento local de usuários, clientes, visitas, fotografias e exportações.
- `xano/`: Backend Xano (schema, endpoints e guia de integração). Veja `xano/README.md`.
- `assets/`: Recursos estáticos (logotipos, ícones, imagens e estilos). Veja `assets/README.md`.
- `docs/`: Documentação técnica, manual e relatórios de mudanças.
- `tests/`: Bateria completa de testes automatizados com `pytest`.
- `openspec/`: Registro das changes e especificações do projeto.

## ✨ Recursos de Experiência do Usuário

- **Autenticação segura** com tela de login, suporte a contas locais e autenticação via API Xano.
- **Painel inicial (Dashboard)** com indicadores operacionais, atalhos de ação rápida e últimas atividades.
- **Gestão de clientes** com busca em tempo real, validação de CNPJ e consulta com histórico.
- **Vistorias técnicas & Checklist normativo Wizard** em 5 etapas (NR-06, NR-24/NR-08, IT/NR-23, NR-12 e PGR/PCMSO/CIPA) com barra de progresso e salvamento automático.
- **Seleção configurável de equipamentos (Dosimetria de Ruído)** com botões destacáveis, múltipla seleção e vínculo automático de cada identificação à visita e à respectiva medição.
- **Captura automática de temperatura** pela localização do dispositivo (clima externo), com fallback gratuito para Open-Meteo e ajuste manual.
- **Assinaturas digitais obrigatórias** do Responsável Técnico e do Avaliador, com desenho por mouse ou toque, visualização, limpeza e inclusão no PDF.
- **Gestão fotográfica** com upload, pré-visualização, legendas técnicas, galeria da visita e substituição de imagens.
- **Emissão de laudos PDF profissionais** formatados com ReportLab e **exportação em planilhas Excel (.xlsx)**.
- **Área administrativa protegida** para gestão de usuários e redefinição de senhas.
- Layout responsivo para computador, tablet e celular, com a identidade visual ACNnorte.

Detalhes em `docs/acnnorte/06-melhorias-experiencia.md`.

## 🗄️ Backend Xano

O diretório `xano/` contém um pacote pronto para importar no Xano, com as tabelas
`users`, `clients`, `visits` e `photos`, além dos endpoints de autenticação, clientes,
visitas e fotografias.

- Guia de importação e configuração: `xano/README.md`
- Schema detalhado: `xano/schema.md`
- Referência da API: `xano/api.md`
- Integração com o Streamlit: `xano/integracao.md`

A aplicação continua usando `data/*.json` até que a camada de persistência seja
migrada para a API.

## 📋 Pré-requisitos

- Python 3.10 ou superior
- Git

## 🛠️ Instalação e Execução

1. Clone o repositório:
```bash
git clone URL_DO_REPOSITORIO
cd APP-SEGURANCA-TRABALHO
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
streamlit run main.py
```
ou
```bash
streamlit run src/main.py
```

## 📦 Versionamento e Padrões

O projeto utiliza Conventional Commits e uma estratégia estruturada de branches (`main`, `develop`, `feature/*`, `hotfix/*`). Consulte a documentação em `docs/versionamento/git-github.md`.

## ✅ Testes

```bash
python -m pytest -q
```

Os testes cobrem:
- Inicialização do armazenamento e persistência JSON;
- Operações de CRUD de clientes e fluxo de visitas e fotos;
- Catálogo, seleção, persistência e vínculo de equipamentos/medições (Dosimetria de Ruído);
- Captura de temperatura, fallbacks e persistência do clima na visita;
- Persistência, limpeza e validação das assinaturas digitais;
- Autenticação e integração de cliente Xano;
- Renderização de todas as telas autenticadas e tela de login.

## 📄 Licença

Uso interno e restrito.
