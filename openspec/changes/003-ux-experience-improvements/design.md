# Design: Melhorias de Navegação e Experiência

## Navegação
Centralizada em `src/ui_components.py`, com constantes de páginas e abas,
`navigate_to()` e estado pendente (`set_pending_state`/`apply_pending_state`).
O estado pendente evita alterar widgets já criados no mesmo ciclo do Streamlit,
garantindo troca de página e de sub-aba sem erros.

O menu lateral usa botões: a página atual recebe `type="primary"` (verde) e as
demais aparecem como secundárias. O item de administração só é exibido para
administradores.

## Formulários em etapas
O checklist mantém exatamente o mesmo formato em `data/visits.json`:
`forms[secao][campo] = valor`.

Cada seção do `TECHNICAL_FORM_SECTIONS` é uma etapa; a etapa final contém
observações, conclusões e situação. Os valores são mantidos em
`st.session_state` e gravados por callbacks `on_change`, o que caracteriza o
salvamento automático.

Campos de seleção recebem uma opção “— Selecione —” apenas na interface. Ao
persistir, respostas não preenchidas viram string vazia, preservando a
compatibilidade com dados existentes e com o gerador de PDF.

Progresso é calculado por `visit_completion()` e
`first_unanswered_section()`, funções puras em `form_template.py`, testáveis
sem interface.

## Painel inicial
Indicadores calculados a partir dos dados já carregados. As atividades recentes
combinam visitas (`updated_at`) e clientes (`created_at`), ordenadas de forma
decrescente. Os atalhos usam `navigate_to()` com a sub-aba desejada.

## Fotografias
O upload usa `st.file_uploader` fora de formulário, permitindo pré-visualização
imediata com `st.image`. A substituição é feita por
`replace_photo_in_visit()`, que grava o novo arquivo, atualiza o registro e só
então remove o arquivo antigo — evitando perda de imagem em caso de falha.

## Mensagens
`set_flash()`/`render_flash()` garantem que uma mensagem de sucesso sobreviva ao
`st.rerun()` e apareça na próxima tela. Ações destrutivas usam confirmação em
duas etapas com estado de pendência.

## Design e responsividade
O CSS em `apply_global_styles()` usa exclusivamente a paleta oficial. Textos
gerais são pretos; a marca mantém ACN verde e norte grafite. Media queries
ajustam espaçamento, tipografia e área de toque em tablet e celular.

## Desempenho
- Dados carregados uma vez por renderização de tela.
- Sem recarregamentos adicionais desnecessários; filtros operam em memória.
- Indicador de sincronização mostra o horário da última gravação local.
- Armazenamento local em JSON dispensa conexão com internet.
