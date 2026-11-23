# Design: Seleção dos Equipamentos de Dosimetria de Ruído

## Fluxo

1. O técnico abre a visita e avança até a etapa **“Dosimetria de Ruído —
   equipamentos utilizados”**.
2. A tela renderiza botões a partir do catálogo configurável, agrupados por
   categoria e marca.
3. Ao tocar em um botão, a seleção é alternada e persistida imediatamente em
   `save_visit_equipment()`.
4. Para cada equipamento selecionado, o sistema mantém um registro de medição
   vinculado (`measurements`) com identificador estável (`meas_<codigo>`).
5. A etapa final e o fluxo de finalização bloqueiam a conclusão quando não há
   nenhum equipamento selecionado.
6. O PDF e a planilha listam os equipamentos escolhidos e suas medições.

## Modelo de dados

```json
{
  "equipment": {
    "category": "Dosimetria de Ruído",
    "selected": [
      {
        "codigo": "CHR-2386",
        "categoria": "Dosimetria de Ruído",
        "marca": "Chrompack",
        "modelo": "",
        "identificacao": "2386",
        "measurement_id": "meas_CHR-2386"
      }
    ]
  },
  "measurements": [
    {
      "id": "meas_CHR-2386",
      "category": "Dosimetria de Ruído",
      "equipment_code": "CHR-2386",
      "equipment_brand": "Chrompack",
      "equipment_model": "",
      "equipment_identification": "2386",
      "created_at": "2026-11-12 10:00:00"
    }
  ]
}
```

- `equipment.selected` é a fonte de verdade da seleção, na ordem do catálogo.
- `measurements` contém uma medição por equipamento selecionado.
- `measurement_id` e `equipment_code` estabelecem o vínculo bidirecional.

## Decisões

- **Catálogo configurável e fechado:** `src/equipment_catalog.py` define apenas
  as opções fornecidas; códigos desconhecidos são rejeitados na persistência.
- **Persistência imediata:** cada toque salva a seleção, evitando perda ao
  navegar entre etapas.
- **Botões com destaque visual:** botões `primary` (verde) para selecionados e
  `secondary` para não selecionados, compatíveis com a identidade visual atual.
- **Medição vinculada automaticamente:** a associação exigida pela change é
  garantida sem inventar campos de resultado da medição.
- **Obrigatório para finalizar:** rascunhos podem ser salvos sem seleção, mas a
  conclusão exige pelo menos um equipamento.
- **Compatibilidade aditiva:** visitas antigas sem os campos continuam válidas;
  registros legados em `devices` podem ser interpretados quando a identificação
  corresponde a uma opção do catálogo.
