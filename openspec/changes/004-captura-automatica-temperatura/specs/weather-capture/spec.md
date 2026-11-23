# Specification: Captura Automática de Temperatura

## Purpose

Definir o comportamento da captura de temperatura e umidade durante a visita
técnica.

## Requirements

1. O preenchimento da visita deve oferecer o botão **“Obter temperatura”**.
2. A localização do dispositivo deve ser solicitada somente após autorização
   do usuário.
3. A consulta deve usar OpenWeather quando `OPENWEATHER_API_KEY` estiver
   configurada e Open-Meteo como fallback gratuito.
4. O sistema deve gravar temperatura, umidade, origem, local e horário da
   consulta no registro da visita.
5. O local utilizado e o horário da consulta devem ser exibidos ao técnico.
6. O técnico deve poder corrigir ou informar manualmente a temperatura externa
   e a umidade.
7. O técnico deve poder informar latitude e longitude manualmente.
8. GPS negado, falta de internet ou falha do serviço não podem impedir o
   preenchimento manual.
9. A interface deve identificar claramente a origem da informação.
10. O sistema não pode apresentar o clima externo como temperatura interna da
    empresa.
11. Deve existir um campo separado e opcional para a temperatura interna medida
    com termômetro na empresa; ele nunca é preenchido automaticamente.

## Scenarios

### Captura automática por GPS
- **Given** uma visita em preenchimento e localização autorizada
- **When** o técnico clica em “Obter temperatura”
- **Then** a temperatura e a umidade são consultadas e gravadas com a origem
  do serviço utilizado

### GPS indisponível
- **Given** que o navegador bloqueou a localização
- **When** o técnico tenta obter a temperatura
- **Then** o sistema orienta o preenchimento manual sem bloquear a visita

### Preenchimento manual
- **Given** uma medição feita com termômetro no ambiente
- **When** o técnico informa temperatura e umidade manualmente
- **Then** os valores são gravados com a origem “Manual”
