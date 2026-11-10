# ACNnorte — Histórico Consolidado e Unificado de Alterações

Este documento consolida integralmente todas as alterações, especificações e melhorias realizadas no projeto desde a sua fundação até o momento atual, unificando as informações das especificações técnicas ([`openspec/changes/`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/openspec/changes/)) e dos relatórios de implementação ([`docs/acnnorte/`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/docs/acnnorte/)), eliminando repetições e preservando todos os detalhes técnicos.

> **DIRETRIZ OBRIGATÓRIA DE PROJETO:**  
> A partir desta versão, **toda e qualquer alteração realizada no sistema deve ser documentada nesta pasta** ([`historico-alteracoes/`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/historico-alteracoes/)), sem exceção, garantindo histórico contínuo e centralizado.

---

## Índice dos Marcos de Alterações

- [Marco 01: Estrutura Topológica, Governança e Versionamento](#marco-01-estrutura-topológica-governança-e-versionamento)
- [Marco 02: Identidade Visual e Estrutura de Ativos Estáticos (Assets)](#marco-02-identidade-visual-e-estrutura-de-ativos-estáticos-assets)
- [Marco 03: Autenticação, Segurança e Gestão de Usuários (Changes 01 a 07)](#marco-03-autenticação-segurança-e-gestão-de-usuários-changes-01-a-07)
- [Marco 04: Painel Inicial (Dashboard) e Navegação Global](#marco-04-painel-inicial-dashboard-e-navegação-global)
- [Marco 05: Gestão Cadastral de Clientes e Histórico Operacional](#marco-05-gestão-cadastral-de-clientes-e-histórico-operacional)
- [Marco 06: Vistorias Técnicas & Checklist Normativo Wizard (Etapas)](#marco-06-vistorias-técnicas--checklist-normativo-wizard-etapas)
- [Marco 07: Gestão Fotográfica e Evidências de Campo](#marco-07-gestão-fotográfica-e-evidências-de-campo)
- [Marco 08: Motor de Emissão de Laudos PDF e Planilhas Excel](#marco-08-motor-de-emissão-de-laudos-pdf-e-planilhas-excel)
- [Marco 09: Backend em Nuvem Xano, API Group e Cliente HTTP](#marco-09-backend-em-nuvem-xano-api-group-e-cliente-http)
- [Marco 10: Suíte de Testes Automatizados e Garantia da Qualidade (QA)](#marco-10-suíte-de-testes-automatizados-e-garantia-da-qualidade-qa)
- [Marco 11: Ponto de Entrada Raiz e Configurações de Ambiente](#marco-11-ponto-de-entrada-raiz-e-configurações-de-ambiente)
- [Marco 12: Recursos Avançados de Campo (Equipamentos, Clima, Assinatura e Scanner EPI)](#marco-12-recursos-avançados-de-campo-equipamentos-clima-assinatura-e-scanner-epi)

---

## Marco 01: Estrutura Topológica, Governança e Versionamento

* **Arquitetura Base**: Divisão estruturada em pastas especializadas:
  * [`src/`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/): Código da aplicação, dividido em views, managers e utilitários.
  * [`data/`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/data/): Persistência local em arquivos JSON para operação autônoma off-line.
  * [`storage/`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/storage/): Diretório legado/reserva para fotos e relatórios temporários.
  * [`assets/`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/assets/): Recursos estáticos institucionais.
  * [`docs/`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/docs/): Manuais operacionais, segurança e arquitetura.
  * [`tests/`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/tests/): Bateria completa de testes automatizados com `pytest`.
  * [`openspec/`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/openspec/): Registro estruturado de especificações de mudanças.
* **Governança de Código e Git**:
  * Configuração de branches com política de promoção (`main`, `develop`, `feature/*`, `hotfix/*`).
  * Criação do [`.gitignore`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/.gitignore) protegendo ambientes virtuais, arquivos temporários e variáveis de ambiente.
  * Padronização de quebras de linha cross-platform no [`.gitattributes`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/.gitattributes).
  * Criação do template institucional de pull requests em [`.github/pull_request_template.md`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/.github/pull_request_template.md).
  * Documentação das diretrizes de versionamento em [`docs/versionamento/git-github.md`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/docs/versionamento/git-github.md).

---

## Marco 02: Identidade Visual e Estrutura de Ativos Estáticos (Assets)

* **Design System Institucional ACNnorte**:
  * **Verde Principal (ACN)**: `#16834A` — Utilizado no logotipo, botões primários e cabeçalhos de destaque.
  * **Cinza Grafite (norte)**: `#59636A` — Utilizado no logotipo, subtítulos e textos informativos secundários.
  * **Verde Escuro**: `#216B45` — Foco, interações ativas e rodapés.
  * **Verde Suave**: `#A5CFAF` — Bordas de cartões e divisores.
  * **Verde Claro**: `#E8F2EA` — Fundo de alertas de sucesso e painéis informativos.
  * **Cinza Claro**: `#F4F6F4` — Fundo neutro de telas e cartões de dados.
  * **Preto Puro**: `#000000` — Tipografia de leitura geral para maximizar legibilidade e acessibilidade.
* **Diretório Centralizado de Ativos ([`assets/`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/assets/))**:
  * [`assets/images/`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/assets/images/): Imagens gerais e banners.
  * [`assets/icons/`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/assets/icons/): Ícones em formato PNG, SVG e ICO.
  * [`assets/styles/`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/assets/styles/): Folhas de estilo CSS adicionais.
  * [`assets/logo/`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/assets/logo/): Logotipos e variações da marca.
  * Preservação da estrutura com arquivos `.gitkeep`.
  * Manual de convenções estabelecido em [`assets/README.md`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/assets/README.md).

---

## Marco 03: Autenticação, Segurança e Gestão de Usuários (Changes 01 a 07)

* **Change 01**: Concepção da tela de login moderna, minimalista e responsiva com o logotipo da marca ([`src/views/login_view.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/views/login_view.py)).
* **Change 02**: Campos de identificador e senha protegidos, com validações contra valores vazios antes de qualquer requisição.
* **Change 03**: Persistência de usuários ([`data/users.json`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/data/users.json)) com criptografia PBKDF2-HMAC-SHA256 (100.000 iterações e salt randômico de 16 bytes). Criação das três contas padrão: `Ana.norte` (Admin), `anaju.mãe` (Técnico) e `anaju.pai` (Técnico).
* **Change 04**: Painel administrativo de controle de usuários ([`src/views/admin_view.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/views/admin_view.py)) com permissões exclusivas para administradores (criação, edição, bloqueio de acesso, reset de senha e exclusão segura).
* **Change 05**: Módulo de troca de senha autônoma ([`src/views/profile_view.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/views/profile_view.py)) com verificação da credencial anterior.
* **Change 06**: Gerenciamento de ciclo de vida da sessão via `st.session_state`, redirecionamento de acessos anônimos e botão de logout.
* **Change 07**: Refinamento de responsividade com folhas de estilo CSS dedicadas em [`src/ui_components.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/ui_components.py).

---

## Marco 04: Painel Inicial (Dashboard) e Navegação Global

* **Menu Lateral Integrado ([`src/main.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/main.py))**:
  * Destaque visual da página atual (`type="primary"`).
  * Exibição do cartão de identificação do usuário logado e papel de acesso.
  * Ocultação de telas administrativas para usuários não administradores.
  * Atalhos operacionais diretos para "Cadastrar cliente" e "Nova visita".
  * Indicador de sincronização informando o horário do último salvamento local.
* **Navegação Segura**:
  * Funções `navigate_to()`, `set_pending_state()` e `apply_pending_state()` em [`src/ui_components.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/ui_components.py) para alternância de telas e abas sem conflitos no ciclo do Streamlit.
* **Painel Executivo ([`src/views/dashboard_main.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/views/dashboard_main.py))**:
  * Cards de indicadores (KPIs): Total de Clientes, Visitas Realizadas, Visitas Pendentes e Total de Fotos.
  * Botões de ação rápida para as principais rotinas.
  * Seção "Últimas Atividades" consolidando clientes e vistorias atualizadas recentemente.

---

## Marco 05: Gestão Cadastral de Clientes e Histórico Operacional

* **Persistência de Clientes**: Estrutura em [`data/clients.json`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/data/clients.json) com identificadores únicos em [`src/storage_manager.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/storage_manager.py).
* **Sub-abas em Formato de Pílulas ([`src/views/clients_view.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/views/clients_view.py))**:
  * *Lista de Clientes*: Busca textual em tempo real por Razão Social, Nome Fantasia ou CNPJ.
  * *Cadastrar Cliente*: Validações completas e verificação contra duplicações de CNPJ.
  * *Consultar & Histórico*: Visão individual da empresa e listagem cronológica de todas as inspeções realizadas para o cliente.

---

## Marco 06: Vistorias Técnicas & Checklist Normativo Wizard (Etapas)

* **Checklist Estruturado em 5 Etapas Normativas + Etapa Final ([`src/form_template.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/form_template.py) e [`src/views/visits_view.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/views/visits_view.py))**:
  1. **NR-06 (Equipamentos de Proteção Individual)**: Fornecimento adequado, obrigatoriedade de uso, estado de conservação, validade do Certificado de Aprovação (CA) e campo de observações.
  2. **NR-24 / NR-08 (Condições Gerais e Instalações)**: Higiene e conservação de sanitários, níveis de iluminação, ventilação e conforto térmico, organização geral (housekeeping) e observações.
  3. **IT / NR-23 (Segurança Contra Incêndio e Pânico)**: Validade e carga de extintores, desobstrução de extintores/hidrantes, sinalização e rotas de fuga, saídas de emergência e observações.
  4. **NR-12 (Segurança em Máquinas e Equipamentos)**: Proteções fixas/móveis intertravadas, botoeiras de parada de emergência, segurança de instalações elétricas e observações.
  5. **PGR / PCMSO / CIPA (Documentação e Programas)**: Vigência do PGR, ASOs e PCMSO atualizados, constituição de CIPA/designado, treinamentos registrados e observações.
  6. **Etapa Final**: Recomendações técnicas finais, parecer conclusivo e fechamento da vistoria.
* **Mecanismos de Produtividade em Campo**:
  * Barra de progresso visual com contagem de itens respondidos (`visit_completion`).
  * Identificação de campos obrigatórios com asterisco (`*`).
  * Salvamento automático a cada resposta alterada via callbacks do Streamlit.
  * Navegação não destrutiva ("Voltar" e "Avançar") com botão explícito "Salvar agora".
  * Retomada automática de visitas em rascunho na primeira seção pendente (`first_unanswered_section`).
  * Bloqueio de finalização caso existam questões obrigatórias não respondidas.

---

## Marco 07: Gestão Fotográfica e Evidências de Campo

* **Captura e Envio ([`src/views/photos_view.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/views/photos_view.py))**:
  * Área de upload com suporte para formatos PNG, JPG e JPEG.
  * Pré-visualização instantânea da foto selecionada antes da confirmação.
  * Campo de legenda técnica obrigatória para caracterizar a inconformidade ou evidência.
* **Armazenamento e Galeria**:
  * Persistência dos arquivos em [`data/photos/`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/data/photos/) e metadados em [`data/visits.json`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/data/visits.json).
  * Galeria organizada por visita técnica com carimbo de data e hora.
* **Substituição Segura de Imagens**:
  * Função `replace_photo_in_visit()` em [`src/storage_manager.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/storage_manager.py), gravando a nova imagem e atualizando o registro antes de excluir a antiga (prevenção contra perda de dados).
  * Exclusão controlada mediante confirmação em tela.

---

## Marco 08: Motor de Emissão de Laudos PDF e Planilhas Excel

* **Relatório Técnico em PDF ([`src/export_manager.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/export_manager.py) e [`src/views/reports_view.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/views/reports_view.py))**:
  * Compilado profissionalmente via biblioteca `ReportLab`.
  * Cabeçalho institucional nas cores ACNnorte com dados da visita e do cliente.
  * Tabela formatada e paginada contendo todas as perguntas normativas, respostas e observações.
  * Anexo fotográfico diagramado com fotos em miniatura e legendas associadas.
  * Geração física em [`data/exports/`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/data/exports/).
* **Planilhas Analíticas em Excel (.xlsx)**:
  * Exportação gerencial utilizando `Pandas` e `OpenPyXL`.
  * Colunas estruturadas para relatórios de auditoria e alimentação de ferramentas de BI.
  * Botão de download direto integrado na tela do operador.

---

## Marco 09: Backend em Nuvem Xano, API Group e Cliente HTTP

* **Definições XanoScript**:
  * [`xano/acnnorte.xs`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/xano/acnnorte.xs): Arquivo multidoc oficial com validação de 0 erros no language server.
  * [`xano/workspace/`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/xano/workspace/): 25 arquivos individuais prontos para deploy via `xano workspace push`.
  * Especificações detalhadas em [`xano/schema.md`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/xano/schema.md), [`xano/api.md`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/xano/api.md) e [`xano/integracao.md`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/xano/integracao.md).
* **Modelagem Relacional de Dados**:
  * Tabela `users`: id, name, email (índice único), password, role, status, timestamps.
  * Tabela `clients`: id, name, cnpj (índice), address, responsible, phone, email, timestamps.
  * Tabela `visits`: id, client_id, user_id, status (`draft`/`finalized`), form (JSON estruturado), timestamps.
  * Tabela `photos`: id, visit_id, file, caption, order, timestamp.
* **Conjunto de 20 Endpoints REST**:
  * Módulo Auth: `POST /auth/login`, `POST /auth/signup`, `GET /auth/me`, `POST /auth/change_password`.
  * Módulo Usuários: `GET /users`, `PATCH /users/{id}/status`.
  * Módulo Clientes: `GET /clients`, `POST /clients`, `GET /clients/{id}`, `PATCH /clients/{id}`, `DELETE /clients/{id}`.
  * Módulo Visitas: `GET /visits`, `POST /visits`, `GET /visits/{id}`, `PATCH /visits/{id}`, `POST /visits/{id}/finalize`.
  * Módulo Fotografias: `GET /photos`, `POST /photos`, `PATCH /photos/{id}`, `DELETE /photos/{id}`.
* **Cliente HTTP e Integração**:
  * Módulo [`src/core/database/xano_client.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/core/database/xano_client.py) com pooling de sessões HTTP, injeção de Bearer Token JWT e captura controlada de falhas.
  * Camada de autenticação [`src/modules/authentication/auth_service.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/modules/authentication/auth_service.py) realizando validação de campos antes de qualquer tráfego HTTP.
  * Botão de diagnóstico em tempo real (**"🔌 Testar conexão"**) na barra lateral da aplicação.

---

## Marco 10: Suíte de Testes Automatizados e Garantia da Qualidade (QA)

A plataforma conta com **37 testes automatizados** aprovados com **100% de sucesso**:

1. [`tests/test_storage_manager.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/tests/test_storage_manager.py) (6 testes):
   - Inicialização idempotente do armazenamento.
   - Escrita estrita de arquivos JSON.
   - CRUD de clientes e tratamento de conflitos.
   - Fluxo completo de visitas e fotos.
   - Cálculo de progresso de formulários.
   - Compilação física de arquivos PDF e Excel.
2. [`tests/test_app_pages.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/tests/test_app_pages.py) (11 testes):
   - Renderização da tela de login e bloqueio de entradas em branco.
   - Disparo do fluxo de login com e-mail direcionado ao Xano.
   - Renderização das 7 telas autenticadas da aplicação.
   - Transição de rotas via barra lateral.
3. [`tests/test_auth_service.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/tests/test_auth_service.py) (10 testes):
   - Validação preventiva de e-mail e senha.
   - Isolamento de chamadas HTTP quando há campos vazios.
   - Chamada direta a `/auth/login` sem token estático no ambiente.
   - Captura amigável de falhas de credencial, rede e configuração.
4. [`tests/test_xano_client.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/tests/test_xano_client.py) (10 testes):
   - Teste de requisições GET e POST com JSON e headers.
   - Tratamento de status codes de erro e timeouts.
   - Validação da rotina de Smoke Test na rota `/auth/me`.

---

## Marco 11: Ponto de Entrada Raiz e Configurações de Ambiente

* **Ponto de Execução Central ([`main.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/main.py))**:
  * Ponto de entrada leve criado na raiz para facilitar a execução com `python -m streamlit run main.py`.
  * Redirecionamento limpo para o núcleo em [`src/main.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/main.py).
* **Variáveis de Ambiente**:
  * Configuração padronizada via [`.env`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/.env) e [`.env.example`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/.env.example) com suporte a `python-dotenv`.

---

## Marco 12: Recursos Avançados de Campo (Equipamentos, Clima, Assinatura e Scanner EPI)

* **Catálogo Oficial de Equipamentos de Medição ([`src/equipment_catalog.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/equipment_catalog.py))**:
  * Base única e oficial de instrumentos da ACN Norte: Audiodosímetros, Bombas de Amostragem, Medidores de Vibração e Monitores IBUTG.
  * Controle e exibição de datas de calibração vigentes, suporte a calibrações personalizadas via [`data/equipments.json`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/data/equipments.json) e padronização na nomenclatura de fotos e laudos técnicos.
* **Serviço de Condições Climáticas em Campo ([`src/weather_service.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/weather_service.py))**:
  * Integração com a API `OpenWeather` para aferição automática de temperatura e umidade relativa a partir das coordenadas GPS do avaliador.
  * Suporte a inserção manual de coordenadas quando o navegador bloqueia a permissão de geolocalização.
* **Componentes Interativos de Campo ([`src/components.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/components.py))**:
  * **`signature_pad`**: Componente canvas HTML5 interativo permitindo coleta de assinatura digital do cliente ou técnico via toque na tela, caneta stylus ou mouse.
  * **`geolocation_button`**: Componente para captura imediata da posição geográfica (latitude e longitude) com alta precisão via GPS.
* **Scanner de EPI e Reconhecimento OCR ([`src/epi_scanner.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/epi_scanner.py))**:
  * Extração automatizada de texto e número de Certificado de Aprovação (CA) a partir de fotografias de equipamentos com OCR (suporte a Pillow e Pytesseract).
  * Sugestão assistida no checklist da NR-06 para agilizar a inspeção de conformidade.
* **Preparação do Formulário de Campo**:
  * Inclusão da rota `PAGE_FORM = "Formulário de Campo"` em [`src/ui_components.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/ui_components.py).
