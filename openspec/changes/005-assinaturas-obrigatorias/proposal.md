# Change 005: Assinaturas Obrigatórias

## Objetivo

Permitir que o **Responsável Técnico** e o **Avaliador** assinem digitalmente a
visita, com nome e desenho, garantindo que as duas assinaturas existam antes da
finalização.

## Escopo

- Dois campos de assinatura: **Responsável Técnico** e **Avaliador**.
- Nome do signatário e área para desenhar com mouse ou tela sensível ao toque.
- Ações de visualizar, limpar, desfazer e refazer o desenho.
- Persistência do nome, do arquivo PNG e do horário da assinatura na visita.
- Exigência das duas assinaturas para finalizar a visita.
- Rascunhos podem ser salvos sem assinaturas.
- Inclusão das assinaturas no relatório PDF.
- Aviso explícito de que o registro não possui validade jurídica automática.

## Fora de escopo

- Certificação digital, ICP-Brasil ou assinatura com validade jurídica.
- Biometria, reconhecimento facial ou autenticação externa do signatário.
- Assinatura de terceiros não vinculados à visita.
- Alteração das regras do checklist técnico.

## Impacto

Novo componente `src/signature_pad.py`, campo aditivo `signatures` em
`src/storage_manager.py`, seção de assinaturas em `src/views/visits_view.py`,
inclusão no PDF em `src/export_manager.py` e testes automatizados.
