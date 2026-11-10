# Proposal: Field Inspection v2 (Layout ACN Norte)

## Why

O formulário de campo concentrava navegação, UI e regras em um único arquivo,
dificultando evoluções de UX e a manutenção do fluxo. A nova estrutura isola o
fluxo em `src/features/field_inspection/`, preservando os serviços centrais e
os formatos de dados existentes.

## What Changes

- Menu lateral em blocos com perfil ativo e os grupos **Navegação** e
  **Acesso rápido** do Layout ACN Norte.
- Formulário principal modularizado em cabeçalho, trabalhador, equipamentos,
  EPI, checklist, assinaturas, ações e documentos.
- Captura de GPS automática com fallback meteorológico para Open-Meteo.
- Botoeira de equipamentos em chips, mantendo o catálogo oficial e a
  nomenclatura padrão dos arquivos.
- Emissão direta de laudo PDF e planilha Excel por inspeção.
- Atalho final para a Galeria do Dia.
- Nenhuma alteração nos formatos de `data/*.json` nem nas regras de validação.

## Impact

- Nova pasta: `src/features/field_inspection/`.
- `src/main.py` passa a delegar o menu e a página inicial ao novo módulo.
- `src/weather_service.py` ganha captura automática com fallback.
- `src/export_manager.py` passa a exibir tipo e certificado na tabela do PDF.
- Testes novos em `tests/test_field_inspection_v2.py`.
