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

## Arquivos principais alterados

- `src/main.py` — menu lateral, destaque da página e roteamento.
- `src/ui_components.py` — design system, navegação, mensagens e indicadores.
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
