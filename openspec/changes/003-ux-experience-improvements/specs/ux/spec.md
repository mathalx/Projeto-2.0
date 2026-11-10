# Specification: User Experience Improvements

## Purpose
Definir os requisitos de navegação, formulários, painel, fotografias, mensagens,
design e desempenho do ACNnorte.

## Requirements

### Navegação
1. O aplicativo deve possuir menu lateral com ícones e nomes objetivos.
2. A página atual deve ser visualmente destacada.
3. O menu deve oferecer atalhos para cadastrar cliente e iniciar visita.
4. A navegação não pode perder o estado da sessão nem os dados carregados.

### Formulários
5. O checklist técnico deve ser dividido em etapas (seções) com etapa final.
6. O progresso do preenchimento deve ser exibido.
7. Campos obrigatórios devem ser identificados e validados antes da finalização.
8. Deve ser possível avançar e voltar sem perder informações.
9. As respostas devem ser salvas automaticamente e recuperáveis como rascunho.

### Painel inicial
10. O painel deve exibir total de clientes, visitas realizadas e visitas
    pendentes.
11. O painel deve exibir as últimas atividades.
12. O painel deve oferecer atalhos para as principais funcionalidades.

### Fotografias
13. O envio de fotografia deve ser destacado e permitir pré-visualização.
14. Cada fotografia deve permitir legenda.
15. As fotografias devem ser organizadas por visita.
16. Deve ser possível remover (com confirmação) e substituir imagens.
17. O sistema deve confirmar o sucesso das operações.

### Mensagens
18. Ações importantes devem produzir feedback de sucesso, aviso ou erro.
19. Exclusões e finalização de visita devem exigir confirmação.
20. Operações demoradas devem exibir indicador de carregamento.
21. As mensagens não devem expor termos técnicos desnecessários.

### Design
22. A paleta deve ser: `#16834A`, `#216B45`, `#A5CFAF`, `#E8F2EA`, `#F4F6F4`,
    `#59636A` e `#000000`.
23. O nome ACNnorte deve manter ACN em verde e norte em cinza; demais textos
    devem ser pretos.
24. A interface deve ser responsiva para computador, tablet e celular.

### Desempenho e segurança dos dados
25. Clientes e visitas devem permitir pesquisa e filtros.
26. Rascunhos devem poder ser retomados.
27. O estado de sincronização local deve ser visível.
28. Ações duplicadas devem ser evitadas.
29. Autenticação, formatos de arquivo e funcionalidades existentes não podem ser
    alterados.

## Scenarios

### Preenchimento em etapas com salvamento
- **Given** uma visita em andamento
- **When** o técnico responde um campo e avança de etapa
- **Then** a resposta é persistida e permanece visível ao voltar

### Finalização segura
- **Given** um checklist incompleto
- **When** o técnico tenta finalizar
- **Then** o sistema informa os campos pendentes e não finaliza

### Retomada de rascunho
- **Given** uma visita com status Rascunho
- **When** o técnico clica em continuar preenchimento
- **Then** o formulário abre na primeira seção com campos pendentes

### Exclusão protegida
- **Given** um cliente ou fotografia existente
- **When** o usuário solicita exclusão
- **Then** o sistema pede confirmação antes de apagar
