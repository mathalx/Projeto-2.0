# Melhorias de Navegação e Experiência do Usuário

Este documento registra o conjunto de melhorias de usabilidade aplicado ao
ACNnorte, sem alterar a autenticação, a estrutura dos dados ou as regras de
negócio existentes. As visitas, clientes, fotografias e relatórios continuam
usando os mesmos arquivos e formatos.

## CHANGE 01 — Navegação e usabilidade

- Menu lateral único, com páginas agrupadas e descrição de cada item.
- A página atual é destacada em verde; as demais aparecem como botões claros.
- Atalhos fixos no menu para **Cadastrar cliente** e **Nova visita**.
- Sub-abas internas em formato de pílulas para clientes, visitas e fotografias.
- A navegação é mantida em `st.session_state["current_page"]`, preservando o
  contexto durante os recarregamentos do Streamlit.

## CHANGE 02 — Formulários simplificados

- O checklist técnico deixou de ser uma tela única e passou a ser dividido em
  **5 seções + etapa final** (EPI, Condições Gerais, Incêndio, Máquinas e
  Documentação).
- Barra de progresso com a quantidade de campos obrigatórios respondidos.
- Campos obrigatórios identificados com `*`.
- Botões **Voltar**, **Salvar agora** e **Avançar** permitem navegar sem perder
  as respostas.
- Salvamento automático: cada resposta é gravada ao ser alterada.
- A visita pode ser retomada de onde parou, inclusive a partir da lista de
  visitas e do histórico do cliente.
- A finalização exige que todos os campos obrigatórios estejam respondidos e só
  ocorre após confirmação.

## CHANGE 03 — Painel inicial

- Indicadores de **Total de Clientes**, **Visitas Realizadas**, **Visitas
  Pendentes** e **Total de Visitas**.
- Atalhos visíveis que realmente navegam para cadastrar clientes, iniciar
  visitas, consultar registros e gerar relatórios.
- Seção **Últimas atividades**, combinando clientes e visitas atualizados
  recentemente.

## CHANGE 04 — Fotografias

- Área de envio em destaque, com pré-visualização imediata da imagem.
- Legenda obrigatória por fotografia.
- Galeria organizada por visita.
- Remoção com confirmação e opção de **substituir** a imagem mantendo a visita.
- Mensagem de confirmação após anexar, remover ou substituir.

## CHANGE 05 — Mensagens e interações

- Mensagens de sucesso após salvar clientes, visitas e fotografias.
- Aviso de confirmação antes de excluir cliente, fotografia ou usuário.
- Alertas claros para campos obrigatórios não preenchidos.
- Indicadores de carregamento (`st.spinner`) ao salvar, gerar PDF e exportar.
- Confirmação explícita ao finalizar uma visita.
- Feedback ao gerar relatórios e planilhas, com download disponível na mesma tela.
- Mensagens sem termos técnicos e com orientação sobre o próximo passo.

## CHANGE 06 — Design e responsividade

Design system centralizado em `src/ui_components.py`:

| Uso | Cor |
| --- | --- |
| Verde principal | `#16834A` |
| Verde escuro | `#216B45` |
| Verde suave | `#A5CFAF` |
| Verde claro | `#E8F2EA` |
| Cinza claro | `#F4F6F4` |
| Cinza grafite | `#59636A` |
| Preto (textos) | `#000000` |

- Botões com altura mínima de 46 px (50 px em telas sensíveis ao toque).
- Cartões, métricas, abas e mensagens padronizados.
- Layout responsivo para computador, tablet e celular via media queries.
- Respeito à preferência de movimento reduzido.
- O nome **ACNnorte** mantém ACN em verde e norte em cinza; os demais textos
  permanecem pretos.

## CHANGE 07 — Desempenho e experiência geral

- Pesquisa e filtros em clientes (nome, CNPJ, responsável) e visitas (cliente,
  técnico, código e situação).
- Continuidade de preenchimentos salvos como rascunho.
- Indicador de sincronização no menu lateral, com horário da última gravação e
  aviso de que os dados ficam no dispositivo (funciona sem internet).
- Prevenção de cadastros duplicados pelo CNPJ.
- Ações destrutivas exigem confirmação; formulários são limpos após o envio para
  evitar duplicidade.
- Dados preservados durante a navegação por meio do estado da sessão.

## Menu lateral: abrir e fechar

O menu lateral pode ser recolhido e reaberto em qualquer tela autenticada
(Painel Inicial, Clientes, Visitas Técnicas, Fotografias, Relatórios,
Alterar Senha e Gerenciar Usuários), no celular e no desktop.

### Causa encontrada

- O CSS do sistema não ocultava `stHeader`, `stToolbar` nem o controle nativo;
  o problema estava no botão flutuante antigo.
- O botão antigo procurava `[data-testid="collapsedControl"]` e
  `[data-testid="stSidebarCollapsedControl"]`, seletores que **não existem no
  Streamlit 1.64.0** (versão instalada). Nessa versão o controle de reabrir é
  `[data-testid="stExpandSidebarButton"]` e o de fechar é
  `[data-testid="stSidebarCollapseButton"]`.
- Além disso, o botão antigo ficava em `top/left: 0.55rem`, sobre o controle
  nativo de reabrir, e não guardava estado nem fechava o menu no celular após
  a troca de página.

### Solução

- **Controles nativos preservados:** `inject_sidebar_css()` mantém
  `stHeader`, `stToolbar`, `stExpandSidebarButton` e `stSidebarCollapseButton`
  visíveis, com `pointer-events` e foco. Nada do header é escondido.
- **Botão “☰ Menu”** fixo no topo da área principal, com 44×44 px mínimos,
  cores da identidade ACNnorte e `aria-label` dinâmico (“Abrir menu” ou
  “Fechar menu”). É um `st.button` real, portanto sobrevive a reruns e pode ser
  testado com `AppTest`.
- **Botão “✕ Fechar menu”** no topo da sidebar, sempre visível
  (especialmente útil em telas pequenas).
- **Ponte HTML/JS** via `st.iframe` (substituto atual de
  `streamlit.components.v1.html`): acessa `window.parent.document` e clica no
  controle nativo com tolerância aos testids do Streamlit 1.64.0 e aos nomes
  legados. Um token único por renderização força a reexecução do comando em
  cliques repetidos.
- **Estado da sessão:** `st.session_state["sidebar_open"]` guarda a intenção
  do usuário; a ordem de execução fica em `_sidebar_command` e é consumida uma
  única vez. O estado real da sidebar é preservado pelo próprio Streamlit
  durante reruns e trocas de página.
- **Mobile-first:** `initial_sidebar_state="auto"` mantém o menu aberto no
  desktop e recolhido no celular. Abaixo de 768 px a sidebar nativa abre
  sobreposta ao conteúdo; ao escolher uma página, `navigate_to()` agenda
  `close_if_mobile` e a ponte fecha o menu automaticamente. Em desktop o
  comando é ignorado e o estado escolhido é mantido.

### Como usar

1. Toque em **☰ Menu** (ou no controle nativo) para abrir.
2. Toque em **✕ Fechar menu** (dentro da sidebar), no controle nativo ou
   novamente em **☰ Menu** para fechar.
3. No celular, escolher uma página no menu fecha a sidebar sozinha.

## Arquivos principais alterados

- `src/main.py` — menu lateral, destaque da página e roteamento.
- `src/ui_components.py` — design system, navegação, mensagens, indicadores e
  abertura/fechamento do menu lateral (`inject_sidebar_css`,
  `render_sidebar_toggle`).
- `tests/test_sidebar_toggle.py` — cobertura do estado, do CSS e da ponte JS.
- `src/form_template.py` — obrigatoriedade dos campos e utilitários de progresso.
- `src/views/dashboard_main.py` — indicadores, atalhos e atividades recentes.
- `src/views/clients_view.py` — busca, validação, confirmação e navegação.
- `src/views/visits_view.py` — checklist em etapas, progresso e salvamento automático.
- `src/views/photos_view.py` — envio, pré-visualização, galeria e substituição.
- `src/views/reports_view.py` — carregamento, feedback e downloads persistentes.
- `src/storage_manager.py` — função de substituição de fotografia.
- `src/export_manager.py` — tratamento de campos não preenchidos no PDF.

## Compatibilidade preservada

- Nenhuma regra de autenticação ou hash de senha foi alterada.
- O formato de `data/clients.json`, `data/visits.json` e `data/photos/` permanece
  o mesmo; apenas a função `replace_photo_in_visit` foi adicionada.
- Relatórios PDF e planilhas Excel continuam usando os mesmos caminhos e nomes.
- Funcionalidades existentes de clientes, visitas, fotografias e relatórios foram
  mantidas.

## Validação

Testes automatizados disponíveis em `tests/`:

```bash
python -m pytest -q
```

Cobrem:

- inicialização idempotente do armazenamento e preservação de dados;
- CRUD de clientes;
- criação, edição e finalização de visitas;
- anexar, substituir e remover fotografias;
- geração de PDF e planilhas Excel;
- renderização das telas e navegação lateral via `streamlit.testing.v1.AppTest`.
