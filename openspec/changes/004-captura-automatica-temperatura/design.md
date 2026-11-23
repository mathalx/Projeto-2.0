# Design: Captura Automática de Temperatura

## Fluxo

1. A seção de temperatura é renderizada no preenchimento da visita.
2. O componente `acnnorte_geolocation` solicita a localização ao navegador.
3. O técnico clica em **“Obter temperatura”**.
4. O sistema usa as coordenadas do GPS ou, na ausência delas, as coordenadas
   informadas manualmente.
5. `capture_weather_auto` consulta a OpenWeather (se configurada) e recorre à
   Open-Meteo em caso de ausência de chave ou falha.
6. O resultado é persistido no registro `weather` da visita.

## Modelo de dados

```json
{
  "weather": {
    "temperature_c": 27.3,
    "internal_temperature_c": 22.5,
    "humidity_pct": 61.0,
    "description": "Parcialmente nublado",
    "city": "São Paulo",
    "latitude": -23.5505,
    "longitude": -46.6333,
    "source": "Open-Meteo",
    "captured_at": "2026-11-12 09:30:00"
  }
}
```

- `temperature_c`: temperatura externa (clima), preenchida automaticamente.
- `internal_temperature_c`: temperatura interna medida na empresa, sempre
  informada manualmente e opcional.

## Decisões

- **Clima externo, não interno:** a interface e a documentação deixam explícito
  que o valor é meteorológico e não substitui medição no ambiente.
- **Sem dependência obrigatória de chave:** a Open-Meteo garante o funcionamento
  em instalações novas.
- **Degradação graciosa:** GPS negado, falta de rede ou falha do serviço levam
  ao preenchimento manual, sem bloquear a visita.
- **Persistência aditiva:** o campo `weather` é adicionado sem alterar os
  registros existentes; visitas antigas são tratadas como “não capturada”.
