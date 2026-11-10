# Aplicativo de Visitas Técnicas de Segurança do Trabalho

Aplicativo modular desenvolvido em Python para gestão de visitas técnicas de segurança do trabalho, preenchimento de formulários de inspeção, registro fotográfico e geração de relatórios e planilhas em Excel.

## 🚀 Arquitetura do Projeto

O projeto segue uma arquitetura modular baseada em responsabilidades:

- `src/`: aplicação Streamlit (ponto de entrada, navegação, armazenamento e exportações).
  - `features/field_inspection/`: **novo fluxo isolado de inspeção de campo** (Layout ACN Norte). Reúne cabeçalho/clima automático, trabalhador, botoeira de equipamentos, scanner de EPI, checklist, assinaturas, ações e documentos. Veja `docs/acnnorte/08-modulo-inspecao-v2.md`.
  - `views/`: painel, clientes, visitas, fotografias, relatórios e administração (rotas legadas preservadas).
  - `equipment_catalog.py`: catálogo oficial de equipamentos da ACN Norte.
  - `weather_service.py`: captura de temperatura e umidade pela OpenWeather, com fallback automático para Open-Meteo.
  - `epi_scanner.py`: reconhecimento de EPI por imagem (OCR opcional).
  - `components.py`: assinatura digital e geolocalização (componentes v2).
- `data/`: armazenamento local de usuários, clientes, visitas/inspeções, equipamentos, fotografias, assinaturas e exportações.
- `xano/`: backend Xano (schema, endpoints e guia de integração). Veja `xano/README.md`.
- `assets/`: Recursos estáticos (logotipos, ícones, imagens e estilos). Veja `assets/README.md`.
- `docs/`: documentação técnica, manual e relatórios de mudanças.
- `tests/`: Testes unitários e de renderização das telas.
- `openspec/`: Registro das changes e especificações do projeto.

## ✨ Recursos de Experiência do Usuário

- **Acesso direto ao formulário de campo**, sem tela de login, com perfil ativo
  `Ana.norte - Administrador` no menu lateral.
- Menu em blocos do **Layout ACN Norte** com **Navegação** e **Acesso rápido**.
- Cabeçalho com empresa, datas de avaliação e **temperatura/umidade automáticas**
  via GPS, OpenWeather e fallback Open-Meteo.
- **Funcionário avaliado** com nome, função, setor e foto do rosto obrigatória.
- **Botoeira dinâmica de equipamentos** em chips, com o catálogo oficial ACN
  Norte, data da última calibração e nomes padronizados de arquivos.
- **Scanner de EPI** por imagem (OCR opcional) que preenche o checklist NR-06.
- **Assinaturas digitais** do responsável técnico e do avaliador.
- **Galeria do Dia** com botão final de acesso rápido a partir do formulário.
- **Laudo PDF homologado** com foto do funcionário, tabela técnica completa e
  quadros de assinatura; **planilha Excel por inspeção** com os mesmos dados.
- Checklist técnico dividido em etapas, com progresso e salvamento automático.
- Painel inicial com indicadores, atalhos e últimas atividades.
- Fotografias com pré-visualização, legenda, galeria e substituição.
- Pesquisa e filtros de clientes e visitas.
- Mensagens claras de sucesso, aviso e erro em todas as ações importantes.
- Layout responsivo para computador, tablet e celular, mantendo a identidade visual ACNnorte.

Detalhes em `docs/acnnorte/06-melhorias-experiencia.md`,
`docs/acnnorte/07-formulario-campo.md` e
`docs/acnnorte/08-modulo-inspecao-v2.md`.

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

   Para captura automática do clima, informe `OPENWEATHER_API_KEY` no `.env`.
   O scanner de EPI usa OCR opcional: instale o Tesseract no sistema e, se
   necessário, configure `TESSERACT_CMD`.

5. Execute a aplicação:
```bash
streamlit run src/main.py
```

   O aplicativo abre diretamente no **Formulário de Campo**.

## 📦 Versionamento e Padrões

O projeto utiliza Conventional Commits e uma estratégia estruturada de branches (`main`, `develop`, `feature/*`, `hotfix/*`). Consulte a documentação em `docs/versionamento/git-github.md`.

## ✅ Testes

```bash
python -m pytest -q
```

Os testes validam o armazenamento local, o fluxo de visitas e fotografias, as
exportações e a renderização das telas do Streamlit.

## 📄 Licença

Uso interno e restrito.
