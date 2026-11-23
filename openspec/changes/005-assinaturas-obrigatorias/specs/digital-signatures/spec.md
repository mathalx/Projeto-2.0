# Specification: Assinaturas Digitais

## Purpose

Definir o comportamento das assinaturas do Responsável Técnico e do Avaliador
no encerramento da visita técnica.

## Requirements

1. A etapa final deve oferecer dois campos de assinatura: **Responsável
   Técnico** e **Avaliador**.
2. Cada campo deve ter nome do signatário e uma área para desenhar.
3. O desenho deve funcionar com mouse e com tela sensível ao toque.
4. O técnico deve poder visualizar, limpar, desfazer e refazer o desenho.
5. As assinaturas devem ser salvas vinculadas à visita, com nome, arquivo PNG e
   horário do registro.
6. As duas assinaturas devem ser obrigatórias para concluir a visita.
7. Salvar um rascunho não pode exigir assinaturas.
8. As assinaturas devem ser incluídas no relatório PDF.
9. A interface e o PDF devem informar que o registro não possui validade
   jurídica automática.
10. O sistema não deve declarar certificação digital ou validade jurídica sem
    processo externo específico.

## Scenarios

### Assinatura com mouse
- **Given** uma visita na etapa final
- **When** o técnico informa o nome e desenha com o mouse
- **Then** o desenho é salvo como PNG e vinculado à visita

### Assinatura por toque
- **Given** um dispositivo com tela sensível ao toque
- **When** o técnico desenha com o dedo
- **Then** o traço é registrado da mesma forma que o mouse

### Limpar e refazer
- **Given** uma assinatura já desenhada
- **When** o técnico clica em “Limpar” e desenha novamente
- **Then** o registro anterior é removido e o novo desenho é salvo

### Finalização sem assinaturas
- **Given** uma visita com o checklist completo, mas sem as duas assinaturas
- **When** o técnico tenta finalizar
- **Then** o sistema bloqueia a finalização e informa quais assinaturas faltam

### Rascunho sem assinaturas
- **Given** uma visita em preenchimento
- **When** o técnico clica em “Salvar agora”
- **Then** o rascunho é salvo normalmente, mesmo sem assinaturas
