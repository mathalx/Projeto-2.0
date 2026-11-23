# Tasks: 005-assinaturas-obrigatorias

## Assinaturas

- [x] Componente de assinatura com mouse e tela sensível ao toque
- [x] Campo de nome do Responsável Técnico
- [x] Campo de nome do Avaliador
- [x] Ações de desfazer, limpar e desenhar novamente
- [x] Visualização da assinatura salva
- [x] Persistência do PNG e do nome em `data/photos/signatures/`

## Regras da visita

- [x] As duas assinaturas são obrigatórias para finalizar
- [x] Rascunho pode ser salvo sem assinaturas
- [x] Validação de nome e imagem no momento da finalização
- [x] Assinaturas incluídas no relatório PDF
- [x] Aviso de ausência de validade jurídica automática

## Validação

- [x] `python -m pytest -q` — todos os testes aprovados
- [x] Renderização da etapa final validada com `streamlit.testing.v1.AppTest`
- [x] Geração de PDF com assinaturas validada
- [x] Documentação registrada em `docs/acnnorte/08-assinaturas-digitais.md`
