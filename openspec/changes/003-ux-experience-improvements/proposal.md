# Change 003: Melhorias de Navegação e Experiência do Usuário

## Objetivo
Reduzir o tempo de preenchimento durante as visitas técnicas e tornar o
ACNnorte mais simples, rápido e intuitivo, preservando autenticação, dados e
funcionalidades existentes.

## Escopo
- **Navegação:** menu lateral organizado, página atual destacada, ícones e
  atalhos de acesso rápido.
- **Formulários:** checklist em etapas, progresso, campos obrigatórios,
  validação com mensagens claras e salvamento automático.
- **Painel inicial:** indicadores de clientes e visitas, atalhos e últimas
  atividades.
- **Fotografias:** envio em destaque, pré-visualização, legenda, galeria por
  visita, remoção com confirmação e substituição.
- **Mensagens:** feedback padronizado de sucesso, aviso, erro e carregamento.
- **Design:** padronização visual e responsividade mantendo a paleta ACNnorte.
- **Desempenho:** pesquisa e filtros, retomada de rascunhos, indicador de
  sincronização e prevenção de ações duplicadas.

## Fora de escopo
- Alterar regras de autenticação ou segurança.
- Alterar a estrutura dos arquivos de dados.
- Remover funcionalidades existentes.
- Criar módulos ou recursos não solicitados.

## Impacto
Mudanças concentradas em `src/main.py`, `src/ui_components.py`,
`src/form_template.py` e nas views. O armazenamento recebeu apenas a função
aditiva `replace_photo_in_visit`. Testes automatizados foram adicionados em
`tests/`.
