# Arquitetura do Sistema ACNnorte

## Visão Geral
O sistema **ACNnorte** foi desenvolvido em Python utilizando o framework **Streamlit**, seguindo uma arquitetura modularizada, limpa e robusta.

## Estrutura de Diretórios
```text
projeto/
├── src/
│   ├── main.py              # Ponto de entrada, menu lateral e roteamento (acesso direto)
│   ├── auth_manager.py      # Gerenciamento interno de usuários e hashes
│   ├── storage_manager.py   # Persistência de inspeções, funcionários, fotos e assinaturas
│   ├── export_manager.py    # PDF homologado e planilhas Excel
│   ├── form_template.py     # Seções, campos e regras do checklist técnico
│   ├── equipment_catalog.py # Catálogo oficial ACN Norte e nomes padrão de arquivos
│   ├── weather_service.py   # OpenWeather + fallback Open-Meteo por GPS
│   ├── epi_scanner.py       # Reconhecimento de EPI por imagem/OCR (NR-06)
│   ├── components.py        # Assinatura digital e geolocalização (CCv2)
│   ├── ui_components.py     # Design system, navegação e identidade da marca (ACNnorte)
│   ├── features/
│   │   └── field_inspection/ # NOVO fluxo isolado de inspeção de campo (Layout ACN Norte)
│   │       ├── view.py        # Página principal e resumo da inspeção
│   │       ├── sidebar.py     # Menu lateral em blocos e perfil ativo
│   │       ├── header.py      # Empresa, datas e clima automático
│   │       ├── geolocation.py # GPS automático (componente v2)
│   │       ├── worker.py      # Trabalhador e foto obrigatória do rosto
│   │       ├── equipment.py   # Botoeira dinâmica de equipamentos
│   │       ├── epi.py         # Scanner de EPI e galeria
│   │       ├── checklist.py   # Checklist técnico e observações
│   │       ├── signatures.py  # Assinaturas canvas/touch
│   │       ├── actions.py     # Finalização, PDF/Excel e atalho da galeria
│   │       ├── documents.py   # Laudo PDF e planilha Excel por inspeção
│   │       └── services.py    # Orquestração e validação das regras existentes
│   └── views/
│       ├── field_form_view.py # Formulário legado preservado para compatibilidade
│       ├── dashboard_main.py  # Painel inicial, indicadores e atalhos
│       ├── clients_view.py    # Cadastro, busca e histórico de clientes
│       ├── visits_view.py     # Lista e preenchimento de visitas em etapas
│       ├── photos_view.py     # Upload, galeria, galeria do dia e substituição
│       ├── reports_view.py    # Relatórios PDF e exportações Excel
│       ├── admin_view.py      # Área administrativa de gestão de usuários
│       └── profile_view.py    # Tela de alteração de senha
├── tests/
│   ├── test_storage_manager.py      # Persistência, fotos e exportações
│   ├── test_inspection_features.py  # Catálogo, clima, scanner e laudo
│   ├── test_field_inspection_v2.py  # Novo módulo de inspeção de campo
│   └── test_app_pages.py            # Renderização e navegação das telas
├── data/
│   ├── users.json           # Armazenamento persistente de usuários e hashes
│   ├── clients.json         # Clientes cadastrados
│   ├── visits.json          # Inspeções/visitas, checklists, funcionário, equipamentos e assinaturas
│   ├── equipments.json      # Catálogo ACN Norte e datas de calibração
│   ├── photos/              # Fotos da galeria e do scanner de EPI
│   │   └── workers/         # Fotos do rosto dos funcionários avaliados
│   └── exports/             # PDFs e planilhas gerados sob demanda
├── assets/                  # Recursos visuais estáticos (sem código)
│   ├── images/              # Imagens gerais (banners, ilustrações, fundos)
│   ├── icons/               # Ícones avulsos (PNG, SVG, ICO)
│   ├── styles/              # Folhas de estilo e CSS externos
│   ├── logo/                # Logotipos e variações da marca ACNnorte
│   └── README.md            # Convenções de uso dos recursos visuais
├── docs/
│   └── acnnorte/            # Pasta exclusiva de documentação técnica e de projeto
├── requirements.txt         # Dependências do projeto
└── README.md                # Instruções gerais
```

> A pasta `assets/` está preparada para futuras melhorias de experiência do
> usuário. Nenhum recurso visual é carregado automaticamente pelo aplicativo:
> os componentes atuais permanecem em `src/ui_components.py`. Consulte
> `assets/README.md` e `docs/acnnorte/05-recursos-visuais.md`.
>
> As melhorias de navegação, formulários, painel, fotografias, mensagens,
> responsividade e desempenho estão descritas em
> `docs/acnnorte/06-melhorias-experiencia.md`.

## Navegação e Experiência
- O aplicativo abre diretamente no **Formulário de Campo**, sem tela de login.
- Menu lateral único, com destaque visual da página atual e atalhos de acesso rápido.
- Páginas internas (clientes, visitas e fotografias) usam sub-abas em formato de pílulas.
- O formulário de campo reúne empresa/datas, clima automático, funcionário com foto,
  catálogo de equipamentos, scanner de EPI, checklist e assinaturas digitais.
- O preenchimento da visita é dividido em etapas, com barra de progresso e salvamento automático.
- Mensagens de sucesso, aviso e erro são padronizadas e sem termos técnicos.

Detalhes do formulário principal em `docs/acnnorte/07-formulario-campo.md` e
do novo módulo isolado em `docs/acnnorte/08-modulo-inspecao-v2.md`.

## Identidade Visual
- **ACN**: `#16834A` (Verde Principal)
- **norte**: `#59636A` (Cinza Grafite)
- **Verde escuro**: `#216B45`
- **Verde suave**: `#A5CFAF`
- **Verde claro**: `#E8F2EA`
- **Cinza claro**: `#F4F6F4`
- **Preto**: `#000000` (textos em geral)
- A combinação é aplicada em todas as telas e cabeçalhos do sistema por meio de componentes padronizados em `ui_components.py`.
- O nome ACNnorte permanece com **ACN em verde** e **norte em cinza**; os demais textos usam preto para máxima legibilidade.
