# Tasks: 004-captura-automatica-temperatura

## Captura

- [x] Componente de geolocalização com autorização do navegador
- [x] Botão “Obter temperatura” no preenchimento da visita
- [x] Consulta OpenWeather quando `OPENWEATHER_API_KEY` existe
- [x] Fallback automático para Open-Meteo sem chave
- [x] Gravação de temperatura, umidade, origem, local e horário
- [x] Exibição do local utilizado e do horário da consulta

## Fallbacks

- [x] Preenchimento manual de temperatura e umidade
- [x] Informação manual de latitude e longitude
- [x] Mensagens amigáveis para GPS negado, falta de internet e falha do serviço
- [x] Identificação clara da origem da informação

## Validação

- [x] `python -m pytest -q` — todos os testes aprovados
- [x] Renderização da seção validada com `streamlit.testing.v1.AppTest`
- [x] Documentação registrada em `docs/acnnorte/07-captura-temperatura.md`
