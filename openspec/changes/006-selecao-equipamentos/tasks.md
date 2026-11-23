# Tasks: 006-selecao-equipamentos

## Catálogo e persistência

- [x] Criar catálogo configurável `src/equipment_catalog.py` com apenas as opções fornecidas
- [x] Adicionar campos aditivos `equipment` e `measurements` às visitas
- [x] Implementar seleção, normalização e rejeição de códigos desconhecidos
- [x] Vincular automaticamente cada equipamento selecionado à sua medição

## Interface

- [x] Adicionar etapa “Dosimetria de Ruído — equipamentos utilizados”
- [x] Renderizar botões selecionáveis por categoria/marca com destaque visual
- [x] Permitir seleção múltipla e desmarcação com persistência imediata
- [x] Exibir equipamentos selecionados e medição vinculada
- [x] Exigir pelo menos um equipamento para finalizar a visita

## Relatórios

- [x] Incluir equipamentos e medições no PDF
- [x] Incluir equipamentos e medições na planilha de visitas

## Validação e documentação

- [x] Testes automatizados de catálogo, persistência, vínculo e compatibilidade
- [x] Validação com `streamlit.testing.v1.AppTest` (renderização, clique e finalização)
- [x] Documentação em `docs/acnnorte/09-selecao-equipamentos.md`
- [x] Atualização de README, arquitetura, manual e histórico consolidado
