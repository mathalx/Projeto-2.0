# Arquitetura do Sistema ACNnorte

## Visão Geral
O sistema **ACNnorte** foi desenvolvido em Python utilizando o framework **Streamlit**, seguindo uma arquitetura modularizada, limpa e robusta.

## Estrutura de Diretórios
```text
projeto/
├── src/
│   ├── main.py              # Ponto de entrada, menu lateral e roteamento
│   ├── auth_manager.py      # Autenticação, hash seguro e gerenciamento de usuários
│   ├── storage_manager.py   # Persistência local de clientes, visitas e fotografias
│   ├── export_manager.py    # Geração de relatórios PDF e planilhas Excel
│   ├── form_template.py     # Seções, campos e regras do checklist técnico
│   ├── equipment_catalog.py # Catálogo configurável de equipamentos e medições (Dosimetria de Ruído)
│   ├── weather_service.py   # Consulta de temperatura/umidade (OpenWeather/Open-Meteo)
│   ├── geolocation.py       # Componente de geolocalização do navegador (CCv2)
│   ├── signature_pad.py     # Componente de assinatura digital (mouse/toque, CCv2)
│   ├── ui_components.py     # Design system, navegação e identidade da marca (ACNnorte)
│   ├── core/                # Configurações de banco e cliente HTTP Xano
│   │   └── database/
│   │       └── xano_client.py
│   ├── modules/             # Serviços de negócio (ex: autenticação Xano)
│   │   └── authentication/
│   │       └── auth_service.py
│   └── views/
│       ├── login_view.py    # Tela de login
│       ├── dashboard_main.py# Painel inicial, indicadores e atalhos
│       ├── clients_view.py  # Cadastro, busca e histórico de clientes
│       ├── visits_view.py   # Lista e preenchimento de visitas em etapas
│       ├── photos_view.py   # Upload, galeria e substituição de fotografias
│       ├── reports_view.py  # Relatórios PDF e exportações Excel
│       ├── admin_view.py    # Área administrativa de gestão de usuários
│       └── profile_view.py  # Tela de alteração de senha
├── tests/
│   ├── test_storage_manager.py  # Persistência, fotos e exportações
│   ├── test_app_pages.py        # Renderização e navegação das telas
│   ├── test_auth_service.py     # Autenticação e validações
│   ├── test_weather_service.py  # Captura de temperatura e fallbacks
│   ├── test_visit_weather.py    # Persistência da temperatura na visita
│   ├── test_visit_signatures.py # Persistência e regras das assinaturas
│   ├── test_visit_equipment.py  # Catálogo, seleção e medições de equipamentos
│   └── test_xano_client.py      # Cliente HTTP e conectividade Xano
├── data/
│   ├── users.json           # Armazenamento persistente de usuários e hashes
│   ├── clients.json         # Clientes cadastrados
│   ├── visits.json          # Visitas, formulários e fotografias
│   ├── photos/              # Arquivos de imagem das visitas
│   │   ├── workers/         # Fotos dos funcionários
│   │   └── signatures/      # Assinaturas digitais (PNG)
│   └── exports/             # PDFs e planilhas gerados sob demanda
├── xano/                    # Pacote de backend Xano (schema, endpoints, workspace)
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
- Menu lateral único, com destaque visual da página atual e atalhos de acesso rápido.
- Páginas internas (clientes, visitas e fotografias) usam sub-abas em formato de pílulas.
- O preenchimento da visita é dividido em etapas, com barra de progresso e salvamento automático.
- Mensagens de sucesso, aviso e erro são padronizadas e sem termos técnicos.

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
