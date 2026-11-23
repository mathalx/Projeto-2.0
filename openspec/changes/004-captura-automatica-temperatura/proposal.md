# Change 004: Captura Automática de Temperatura

## Objetivo

Facilitar o preenchimento da temperatura durante a visita técnica, permitindo
obter automaticamente o clima externo a partir da localização do dispositivo,
com possibilidade de correção e preenchimento manual.

## Escopo

- Botão **“Obter temperatura”** no preenchimento da visita.
- Solicitação de localização ao navegador, mediante autorização do usuário.
- Consulta meteorológica por OpenWeather (quando configurada) e Open-Meteo
  (fallback gratuito).
- Gravação de temperatura externa, umidade, origem, local e horário da consulta.
- Campo separado e opcional para a temperatura interna medida na empresa.
- Ajuste manual de temperatura externa, temperatura interna, umidade e
  coordenadas.
- Identificação explícita de que o valor automático é do clima externo e não de
  uma medição interna da empresa.

## Fora de escopo

- Presumir sensor de temperatura ambiente no celular.
- Substituir medições internas feitas com termômetro.
- Alterar autenticação, armazenamento ou regras do checklist.
- Exigir chave de API para o funcionamento básico.

## Impacto

Novos módulos `src/weather_service.py` e `src/geolocation.py`, ajustes em
`src/views/visits_view.py`, campo aditivo `weather` em `src/storage_manager.py`,
configuração opcional `OPENWEATHER_API_KEY` e testes automatizados.
