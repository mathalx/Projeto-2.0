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
- [Marco 12: Acesso Direto à Tela Principal (CHANGE 01 — Remoção da Tela de Login)](#marco-12-acesso-direto-à-tela-principal-change-01--remoção-da-tela-de-login)
- [Marco 13: Captura Automática de Temperatura (CHANGE 03)](#marco-13-captura-automática-de-temperatura-change-03)
- [Marco 14: Assinaturas Digitais Obrigatórias (CHANGE 04)](#marco-14-assinaturas-digitais-obrigatórias-change-04)
- [Atualização 2026-11-14: Captura de Fotografia (upload + câmera frontal/traseira)](#atualização-2026-11-14-captura-de-fotografia-upload--câmera-frontaltraseira)
- [Atualização 2026-11-14: Menu lateral recolhível e reabrível](#atualização-2026-11-14-menu-lateral-recolhível-e-reabrível)

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

## Marco 12: Acesso Direto à Tela Principal (CHANGE 01 — Remoção da Tela de Login)

* **Remoção da Obrigatoriedade de Senha**:
  * Ao abrir o aplicativo, o usuário é direcionado imediatamente para a tela principal ([`Painel Inicial`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/views/dashboard_main.py)), permitindo iniciar visitas, cadastrar clientes e emitir laudos sem telas intermediárias.
  * Inicialização automática de sessão com usuário padrão (`Ana.norte` - Administrador).
* **Preservação de Módulos e Dados**:
  * Todos os módulos de autenticação permanecem íntegros ([`src/auth_manager.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/auth_manager.py), [`src/modules/authentication/auth_service.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/modules/authentication/auth_service.py) e [`src/views/login_view.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/views/login_view.py)).
  * Dados existentes em [`data/`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/data/) preservados sem modificações.
* **Salvaguarda de Ambiente e Rede**:
  * Suporte à variável `REQUIRE_AUTH=true` no arquivo [`.env`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/.env): caso o sistema seja publicado na internet, a proteção por senha pode ser reativada instantaneamente para proteger dados de clientes e funcionários.
  * Suporte a `DEFAULT_USERNAME` para personalizar o nome do avaliador padrão.
* **Validação e Testes**:
  * Bateria de testes expandida para 38 testes automatizados, validando tanto o acesso direto quanto o modo protegido.

---

## Marco 13: Captura Automática de Temperatura (CHANGE 03)

* **Objetivo**:
  * Facilitar o preenchimento da temperatura durante a visita, reduzindo digitação e erros, sem presumir que o celular possua sensor de temperatura ambiente.
* **Captura por localização**:
  * Componente de geolocalização ([`src/geolocation.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/geolocation.py)) solicita a localização ao navegador somente após autorização do usuário.
  * Botão **“Obter temperatura”** consulta o clima externo e grava o resultado na visita.
  * A OpenWeather é usada quando `OPENWEATHER_API_KEY` está configurada; a Open-Meteo é o fallback gratuito automático.
  * Temperatura externa, umidade, origem, local e horário da consulta são exibidos e persistidos no registro `weather` da visita.
  * O campo **“Temperatura externa (°C) — clima”** é preenchido automaticamente e permanece editável.
* **Temperatura externa x interna**:
  * A interface mantém um campo separado e opcional para a **temperatura interna medida** com termômetro na empresa.
  * A temperatura interna nunca é preenchida automaticamente; o celular não é tratado como sensor de temperatura ambiente.
* **Origem da informação**:
  * A interface identifica claramente `Clima externo • OpenWeather`, `Clima externo • Open-Meteo` ou `Preenchimento manual`.
  * O valor meteorológico não é apresentado como temperatura interna da empresa.
* **Fallbacks**:
  * GPS negado, falta de internet ou falha do serviço não bloqueiam a visita: o técnico pode informar temperatura, umidade, latitude e longitude manualmente.
* **Arquivos e testes**:
  * Serviço em [`src/weather_service.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/weather_service.py) e persistência em [`src/storage_manager.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/storage_manager.py).
  * Seção de interface em [`src/views/visits_view.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/views/visits_view.py).
  * Testes em [`tests/test_weather_service.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/tests/test_weather_service.py) e [`tests/test_visit_weather.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/tests/test_visit_weather.py).
  * Documentação detalhada em [`docs/acnnorte/07-captura-temperatura.md`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/docs/acnnorte/07-captura-temperatura.md) e especificação em [`openspec/changes/004-captura-automatica-temperatura/`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/openspec/changes/004-captura-automatica-temperatura/).

---

## Marco 14: Assinaturas Digitais Obrigatórias (CHANGE 04)

* **Objetivo**:
  * Registrar as assinaturas do **Responsável Técnico** e do **Avaliador** ao final da visita, com nome e desenho, e incluí-las no relatório PDF.
* **Assinatura**:
  * Componente [`src/signature_pad.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/signature_pad.py) com canvas compatível com mouse e tela sensível ao toque.
  * Nome e desenho para cada papel, com ações de desfazer, limpar, visualizar e desenhar novamente.
  * Exportação do traço em PNG e persistência em `data/photos/signatures/`.
* **Regras da visita**:
  * As duas assinaturas são obrigatórias para finalizar a visita.
  * Rascunhos podem ser salvos sem assinaturas.
  * Visitas finalizadas exibem as assinaturas em modo somente leitura.
* **PDF**:
  * As imagens, os nomes e os horários são incluídos no relatório.
  * A interface e o PDF informam que o registro não possui validade jurídica automática.
* **Arquivos e testes**:
  * Componente em [`src/signature_pad.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/signature_pad.py); persistência em [`src/storage_manager.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/storage_manager.py); interface em [`src/views/visits_view.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/views/visits_view.py); PDF em [`src/export_manager.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/export_manager.py).
  * Testes em [`tests/test_visit_signatures.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/tests/test_visit_signatures.py).
  * Documentação em [`docs/acnnorte/08-assinaturas-digitais.md`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/docs/acnnorte/08-assinaturas-digitais.md) e especificação em [`openspec/changes/005-assinaturas-obrigatorias/`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/openspec/changes/005-assinaturas-obrigatorias/).

---

## Marco 15: Seleção dos Equipamentos de Dosimetria de Ruído (CHANGE 05)

* **Objetivo**:
  * Substituir o preenchimento manual da identificação do equipamento por botões selecionáveis, com destaque visual para as opções escolhidas, vinculando cada identificação à visita e à sua respectiva medição.
* **Catálogo configurável**:
  * Módulo [`src/equipment_catalog.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/equipment_catalog.py) com opções organizadas por categoria, marca e identificação.
  * Categoria **Dosimetria de Ruído** com apenas as opções fornecidas pela equipe:
    * Chrompack: 2386, 3440, 2319, 3558, 5981.
    * Instrutherm: DOS-100X.
  * Códigos fora do catálogo são rejeitados, evitando cadastro de opções não fornecidas.
* **Seleção na visita**:
  * Nova etapa **“Dosimetria de Ruído — equipamentos utilizados”** em [`src/views/visits_view.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/views/visits_view.py).
  * Botões selecionáveis com destaque visual (verde quando selecionados), seleção múltipla, desmarcação e persistência imediata.
  * Cada equipamento selecionado é associado à visita e a uma medição vinculada (`measurement_id`/`equipment_code`).
* **Persistência e validação**:
  * Campos aditivos `equipment` e `measurements` em [`src/storage_manager.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/storage_manager.py).
  * Rascunhos podem ser salvos sem seleção; a finalização exige pelo menos um equipamento.
  * Visitas antigas continuam compatíveis; registros legados em `devices` podem ser interpretados quando correspondem ao catálogo.
* **Relatórios**:
  * PDF inclui a seção **“Equipamentos Utilizados — Dosimetria de Ruído”** com categoria, marca, identificação e medição ([`src/export_manager.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/export_manager.py)).
  * Planilha de visitas inclui equipamentos e medições vinculadas.
* **Arquivos e testes**:
  * Testes em [`tests/test_visit_equipment.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/tests/test_visit_equipment.py) e cobertura em [`tests/test_storage_manager.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/tests/test_storage_manager.py).
  * Validação com `streamlit.testing.v1.AppTest` (renderização, clique/deseleção e bloqueio de finalização sem equipamento).
  * `python -m pytest -q` → 64 passed.
  * Documentação em [`docs/acnnorte/09-selecao-equipamentos.md`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/docs/acnnorte/09-selecao-equipamentos.md) e especificação em [`openspec/changes/006-selecao-equipamentos/`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/openspec/changes/006-selecao-equipamentos/).

---

## Atualização 2026-11-14: Captura de Fotografia (upload + câmera frontal/traseira)

* **Data**: 2026-11-14.
* **Objetivo**:
  * Permitir upload de imagem existente ou captura na hora em todo campo de fotografia do sistema.
  * Oferecer câmera frontal e traseira, com escolha de dispositivo quando houver mais de uma câmera.
* **Novo componente**:
  * Pasta [`src/components/photo_capture/`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/components/photo_capture/) com `__init__.py`, `photo_capture.py`, `camera_component.html` e `README.md`.
  * Função pública `photo_input(label, key, allow_upload=True, allow_camera=True, default_camera="environment") -> bytes | None`.
  * Componente HTML/JS via `streamlit.components.v1`/Components v2, seguindo o padrão de [`src/signature_pad.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/signature_pad.py) e [`src/geolocation.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/geolocation.py).
  * Abas **📁 Carregar arquivo** e **📷 Usar câmera**, com pré-visualização ao vivo, **Capturar**, **Refazer** e **Usar esta foto**.
  * Alternância `facingMode: "user"` (frontal) e `"environment"` (traseira); fallback automático para a frontal quando a traseira não existe.
  * Lista de câmeras via `enumerateDevices()` quando há mais de um dispositivo de vídeo.
  * Compressão no cliente: maior lado ≤ 1600 px e JPEG com qualidade ~0.85.
  * Encerramento do stream com `track.stop()` ao capturar, trocar de aba ou desmontar.
* **Fallback e mensagens**:
  * Permissão negada, câmera inexistente, câmera em uso, contexto inseguro e navegador sem suporte exibem mensagens em português.
  * Em HTTP fora de localhost, a interface exige HTTPS e oferece `st.camera_input` e `st.file_uploader` como alternativa.
* **Validação no servidor**:
  * Pillow valida JPG/PNG/WEBP, limite de 10 MB, corrige orientação EXIF e converte tudo para JPEG normalizado.
  * [`src/storage_manager.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/storage_manager.py) recebe `validate_photo=True` nos fluxos novos e mantém compatibilidade com chamadas legadas.
  * Fotos continuam em `data/photos/workers/` e `data/photos/`, preservando galeria, checklist, PDF e sincronização Xano best-effort.
* **Integração**:
  * [`src/views/visits_view.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/views/visits_view.py): fotografia do funcionário na Etapa 4.
  * [`src/views/photos_view.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/views/photos_view.py): upload de evidências e substituição de imagem na galeria.
  * Estado em `st.session_state` com chaves derivadas de `key`; `clear_photo_input(key)` reinicia o campo após salvar.
* **Dependência**:
  * Nenhuma dependência nova: `Pillow>=10.0.0` já constava em [`requirements.txt`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/requirements.txt).
* **Testes**:
  * Novo [`tests/test_photo_capture.py`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/tests/test_photo_capture.py) com validação de formatos, tamanho, EXIF, conversão JPEG, retorno `None`, fallback de câmera e persistência.
  * `python -m pytest -q` → 104 passed.
* **Documentação**:
  * [`docs/acnnorte/10-captura-fotografia.md`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/docs/acnnorte/10-captura-fotografia.md).
  * [`src/components/photo_capture/README.md`](file:///c:/Users/Matheus%20Alexandre/Desktop/projeto/src/components/photo_capture/README.md).
* **Arquivos alterados**:
  * `src/components/__init__.py` (novo)
  * `src/components/photo_capture/__init__.py` (novo)
  * `src/components/photo_capture/photo_capture.py` (novo)
  * `src/components/photo_capture/camera_component.html` (novo)
  * `src/components/photo_capture/README.md` (novo)
  * `src/storage_manager.py`
  * `src/views/visits_view.py`
  * `src/views/photos_view.py`
  * `requirements.txt`
  * `tests/test_photo_capture.py` (novo)
  * `docs/acnnorte/10-captura-fotografia.md` (novo)



---

## Atualização 2026-11-14: Menu lateral recolhível e reabrível

* **Data**: 2026-11-14.
* **Objetivo**:
  * Permitir fechar e reabrir o menu lateral em qualquer tela autenticada, no celular e no desktop, sem perder o estado durante reruns, trocas de página ou preenchimento do wizard de visitas.
* **Causa encontrada**:
  * O CSS do sistema não ocultava `stHeader`, `stToolbar`, `stSidebarCollapsedControl` nem `collapsedControl`; o problema estava no botão flutuante antigo.
  * O botão antigo usava os seletores `collapsedControl` e `stSidebarCollapsedControl`, que não existem no Streamlit 1.64.0 instalado. Nessa versão os controles são `stExpandSidebarButton` (reabrir) e `stSidebarCollapseButton` (fechar).
  * O botão ficava em `top/left: 0.55rem`, sobre o controle nativo de reabrir, e não mantinha estado nem fechava o menu no celular após a navegação.
* **Solução**:
  * `inject_sidebar_css()` centraliza o CSS do menu e garante visibilidade dos controles nativos do Streamlit 1.64.0 e dos nomes legados, sem esconder o header/toolbar.
  * Botão real `☰ Menu`, fixo no topo da área principal, com área de toque mínima de 44x44 px, cores ACNnorte e `aria-label` dinâmico (“Abrir menu”/“Fechar menu”).
  * Botão `✕ Fechar menu` no topo da sidebar, visível também em telas pequenas.
  * Ponte HTML/JS via `st.iframe` (substituto de `components.v1.html`) acessa `window.parent.document` e aciona `stExpandSidebarButton`/`stSidebarCollapseButton`, com fallback para versões antigas.
  * Token único por renderização força o recarregamento da ponte, garantindo que cliques repetidos de alternância funcionem.
  * `st.session_state["sidebar_open"]` guarda a intenção do usuário; `_sidebar_command` executa uma única ordem (`toggle`, `close` ou `close_if_mobile`).
  * `initial_sidebar_state="auto"` mantém o menu aberto no desktop e recolhido no celular; abaixo de 768 px a sidebar abre sobreposta e `navigate_to()` agenda o fechamento automático após a escolha da página.
* **Arquivos alterados**:
  * `src/main.py` — `PAGE_CONFIG`, inicialização de `sidebar_open` e botão “✕ Fechar menu”.
  * `src/ui_components.py` — `inject_sidebar_css`, `render_sidebar_toggle`, ponte JS e comandos de navegação.
  * `tests/test_sidebar_toggle.py` (novo) — estado, CSS, ponte JS e renderização via `AppTest`.
  * `docs/acnnorte/06-melhorias-experiencia.md` — seção “Menu lateral: abrir e fechar”.
* **Testes**:
  * `python -m pytest -q` -> 124 passed.
