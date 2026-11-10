# Change 008: Formulário de Campo Integral (Changes 08 a 12)

## Objetivo
Transformar o formulário de campo na tela inicial do ACNnorte, sem login, e
concentrar nele a captura de empresa/datas, clima automático, funcionário com
foto, equipamentos oficiais, scanner de EPI, assinaturas digitais e geração de
laudo homologado.

## Escopo
- **Change 08:** acesso direto, empresa/datas, temperatura e umidade via GPS +
  OpenWeather.
- **Change 09:** funcionário com nome, função, setor e foto do rosto.
- **Change 10:** catálogo ACN Norte, data de calibração e nomes padronizados de
  arquivos.
- **Change 11:** scanner de EPI por imagem/OCR, galeria do dia e botão flutuante.
- **Change 12:** assinaturas digitais e PDF/Excel com foto, equipamentos e
  assinaturas.

## Fora de escopo
- Alterar a identidade visual ou remover telas administrativas existentes.
- Migrar a persistência local para o Xano em produção.
- Substituir o checklist técnico atual.

## Impacto
Principais arquivos: `src/main.py`, `src/views/field_form_view.py`,
`src/storage_manager.py`, `src/export_manager.py`, `src/ui_components.py`,
`src/equipment_catalog.py`, `src/weather_service.py`, `src/epi_scanner.py` e
`src/components.py`. A tabela lógica `inspections` é persistida em
`data/visits.json` para preservar compatibilidade.
