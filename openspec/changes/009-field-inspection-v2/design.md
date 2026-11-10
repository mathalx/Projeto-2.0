# Design: Field Inspection v2

## Decisão

Criar um pacote de feature (`src/features/field_inspection/`) que compõe os
serviços existentes em vez de mover a persistência. Isso reduz o risco de
regressão e mantém a compatibilidade com painel, clientes, visitas,
fotografias, relatórios e Xano.

## Camadas

1. **Constantes/navegação** — `constants.py` e `sidebar.py`.
2. **Serviços de aplicação** — `services.py` orquestra `storage_manager`,
   `form_template` e validações.
3. **Captura de campo** — `header.py`, `geolocation.py`, `worker.py`,
   `equipment.py`, `epi.py`, `checklist.py` e `signatures.py`.
4. **Saída** — `actions.py` e `documents.py` para PDF/Excel e galeria.

## Fluxo de dados

```text
streamlit -> features/field_inspection/view.py
          -> services.py -> storage_manager (data/visits.json)
          -> weather_service (OpenWeather/Open-Meteo)
          -> equipment_catalog (data/equipments.json)
          -> export_manager (data/exports/)
```

## Riscos e mitigação

- **Chaves de widget duplicadas**: todas as chaves usam prefixo `fi_` e o ID
  da inspeção.
- **GPS bloqueado**: há captura manual de coordenadas e de temperatura/umidade.
- **Sem chave OpenWeather**: fallback automático para Open-Meteo.
- **Regressão nas rotas antigas**: renderizadores legados continuam no mapa de
  páginas e os testes existentes seguem passando.
- **Dados existentes**: nenhum campo obrigatório novo foi removido e os
  registros antigos continuam legíveis.
