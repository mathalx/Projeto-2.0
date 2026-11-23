# Change 006: Seleção dos Equipamentos de Dosimetria de Ruído

## Objetivo

Substituir o preenchimento manual da identificação do equipamento por botões
selecionáveis, com destaque visual para as opções escolhidas, vinculando cada
equipamento à visita e à sua respectiva medição.

## Escopo

- Etapa de seleção de equipamentos no preenchimento da visita.
- Categoria **Dosimetria de Ruído** com as opções fornecidas pela equipe:
  - Chrompack: 2386, 3440, 2319, 3558, 5981.
  - Instrutherm: DOS-100X.
- Seleção múltipla por botões destacáveis (verde quando selecionado).
- Persistência aditiva da seleção e criação automática de um registro de
  medição vinculado a cada equipamento selecionado.
- Catálogo configurável em código para facilitar inclusão futura de marcas,
  categorias e equipamentos.
- Validação de finalização: pelo menos um equipamento selecionado.
- Inclusão dos equipamentos e medições no PDF e na exportação Excel.

## Fora de escopo

- Cadastro de opções não fornecidas pela equipe.
- Campos de resultado da medição (dose, dB(A), duração etc.).
- Integração com calibração, certificados ou planilhas externas.
- Alteração do checklist técnico existente.

## Impacto

Novos campos aditivos `equipment` e `measurements` em
`src/storage_manager.py`, catálogo `src/equipment_catalog.py`, etapa dedicada em
`src/views/visits_view.py`, seção de equipamentos no PDF/Excel em
`src/export_manager.py`, testes automatizados e documentação.
