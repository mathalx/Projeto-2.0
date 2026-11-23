# Captura Automática de Temperatura (CHANGE 03)

Este documento registra a implementação da captura de temperatura e umidade
durante o preenchimento da visita técnica.

## Objetivo

Reduzir o tempo de preenchimento e evitar erros de digitação, permitindo que o
técnico obtenha automaticamente a temperatura do local a partir da localização
do dispositivo.

## Como funciona

1. O aplicativo solicita a autorização de localização ao navegador por meio de
   um componente de geolocalização (`st.components.v2`).
2. O técnico clica em **“Obter temperatura”**.
3. O sistema consulta o serviço meteorológico com as coordenadas disponíveis:
   - **OpenWeather**, quando `OPENWEATHER_API_KEY` está configurada;
   - **Open-Meteo** (gratuita, sem chave), como fallback automático.
4. A temperatura, a umidade, a origem, o local e o horário da consulta são
   gravados no registro da visita e preenchem automaticamente o campo
   **“Temperatura externa (°C) — clima”**.

## Temperatura externa x temperatura interna

A seção diferencia dois campos:

- **Temperatura externa (clima):** preenchida pelo serviço meteorológico a
  partir da localização. Pode ser corrigida manualmente.
- **Temperatura interna medida (opcional):** habilitada por uma caixa de
  seleção e preenchida somente quando o técnico mede a temperatura com
  termômetro dentro da empresa.

O celular não é tratado como sensor de temperatura ambiente. A temperatura
interna nunca é preenchida automaticamente.

## Origem da informação

A temperatura retornada é a do **clima externo** na localização informada. Ela
não é uma medição interna da empresa e não substitui um termômetro no ambiente
avaliado. A interface identifica claramente a origem:

- `Clima externo • OpenWeather`
- `Clima externo • Open-Meteo`
- `Preenchimento manual`

## Fallbacks e cuidados

- Se o usuário negar a localização ou o GPS estiver indisponível, a temperatura
  pode ser informada manualmente.
- Também é possível informar latitude e longitude manualmente.
- Sem conexão com a internet, o preenchimento manual continua disponível.
- A temperatura e a umidade manuais são salvas com a origem `Manual`.

## Arquivos envolvidos

| Arquivo | Responsabilidade |
| --- | --- |
| `src/weather_service.py` | Consulta OpenWeather/Open-Meteo e formatação dos valores. |
| `src/geolocation.py` | Componente de geolocalização do navegador (CCv2). |
| `src/views/visits_view.py` | Seção de temperatura, botão de captura e ajuste manual. |
| `src/storage_manager.py` | Persistência do registro `weather` na visita. |
| `tests/test_weather_service.py` | Testes das consultas e fallbacks. |
| `tests/test_visit_weather.py` | Testes de persistência da temperatura. |

## Configuração

A chave da OpenWeather é opcional:

```env
OPENWEATHER_API_KEY=
```

Sem a chave, o sistema usa a Open-Meteo automaticamente.
