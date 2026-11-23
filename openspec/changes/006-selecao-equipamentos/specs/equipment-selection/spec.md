# Specification: Seleção dos Equipamentos de Dosimetria de Ruído

## Purpose

Definir o comportamento da seleção de equipamentos de Dosimetria de Ruído na
visita técnica.

## Requirements

1. O preenchimento da visita deve oferecer botões selecionáveis para as opções
   fornecidas pela equipe.
2. As opções cadastradas devem ser exatamente:
   - Categoria Dosimetria de Ruído, marca Chrompack: 2386, 3440, 2319, 3558,
     5981.
   - Categoria Dosimetria de Ruído, marca Instrutherm: DOS-100X.
3. A opção selecionada deve ter destaque visual em relação às não selecionadas.
4. O técnico deve poder selecionar mais de um equipamento.
5. Cada equipamento selecionado deve ser associado à visita e à sua respectiva
   medição.
6. As opções devem estar estruturadas de forma configurável para inclusão
   futura de marcas, categorias e equipamentos, sem cadastrar opções não
   fornecidas pela equipe.
7. A finalização da visita deve ser bloqueada quando não houver equipamento
   selecionado; o salvamento de rascunho não deve ser bloqueado.
8. Os equipamentos selecionados e suas medições devem constar no PDF e na
   exportação Excel da visita.

## Scenarios

### Seleção múltipla
- **Given** uma visita em preenchimento
- **When** o técnico seleciona Chrompack 2386 e Instrutherm DOS-100X
- **Then** ambos ficam destacados e vinculados à visita com medições distintas

### Desmarcação
- **Given** um equipamento selecionado
- **When** o técnico toca novamente no botão
- **Then** o equipamento deixa de ficar destacado e sua medição vinculada é
  removida da seleção da visita

### Finalização sem equipamento
- **Given** uma visita sem equipamentos selecionados
- **When** o técnico tenta finalizar
- **Then** o sistema informa a pendência e não conclui a visita

### Catálogo fechado
- **Given** uma tentativa de gravar um código fora do catálogo
- **When** a persistência é executada
- **Then** o sistema rejeita a gravação e não cadastra a opção não fornecida
